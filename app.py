import os
import json
import sqlite3
import logging
import datetime
import pandas as pd
from flask import Flask, render_template, request, make_response, jsonify
from sentence_transformers import SentenceTransformer, util
from PIL import Image
import pytesseract
from fpdf import FPDF
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from config.settings import settings
from services.llm_service import call_cloud_llm
from services.report_generator import generate_pdf, generate_html_report
from services.cache_service import get_cache
from crawler.search_engine import SearchEngine
from retrieval.similarity import find_similar_cases

# ─── Logging ───
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = settings.SECRET_KEY

# ---------------- DATABASE ---------------- #
def get_db_connection():
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ---------------- LOAD EMBEDDING MODEL ---------------- #
print("Loading Embedding Model...")
model = SentenceTransformer(settings.EMBEDDING_MODEL)

conn = get_db_connection()
df = pd.read_sql_query("SELECT * FROM laws", conn)
conn.close()

df["combined_text"] = df["section"] + ": " + df["description"]
law_embeddings = model.encode(df["combined_text"].tolist(), convert_to_tensor=True)

print("Indexed", len(df), "BNS Sections")

# ---------------- SEARCH ENGINE ---------------- #
search_engine = SearchEngine()
cache = get_cache()

# ---------------- OCR ---------------- #
pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD

def extract_text_from_image(image_file):
    try:
        img = Image.open(image_file.stream).convert("RGB")
        text = pytesseract.image_to_string(img)
        return text.strip()
    except Exception as e:
        print("OCR Error:", e)
        return ""

# ---------------- CLOUD LLM CALL ---------------- #
# Uses cloud-hosted LLM API (Groq/Gemini/OpenRouter/Ollama)
# Configured via .env — see .env.example for options

# ---------------- SMART TEXT EXTRACTION ---------------- #
def extract_relevant_text(raw_text, max_chars=1500):
    """
    For long inputs, extract the most relevant sentences using embeddings.
    Short inputs are returned as-is.
    """
    if len(raw_text) <= max_chars:
        return raw_text

    import re

    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', raw_text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]

    if not sentences:
        return raw_text[:max_chars]

    # Legal/crime keywords to find factual content (not definitions)
    crime_query = (
        "victim accused crime incident theft robbery murder assault "
        "injured police FIR complaint arrested weapon knife gun "
        "stolen property damage hurt killed attack night"
    )

    query_emb = model.encode(crime_query, convert_to_tensor=True)
    sent_embs = model.encode(sentences, convert_to_tensor=True)
    scores = util.cos_sim(query_emb, sent_embs)[0]

    # Rank sentences by relevance and pick top ones
    scored = sorted(zip(scores.tolist(), range(len(sentences)), sentences),
                    reverse=True)

    # Take top sentences in original order (to preserve narrative flow)
    top_indices = sorted([idx for _, idx, _ in scored[:15]])
    selected = [sentences[i] for i in top_indices]

    result = " ".join(selected)
    if len(result) > max_chars:
        result = result[:max_chars].rsplit(' ', 1)[0] + "..."

    return result


# ---------------- FULL LEGAL ANALYSIS ---------------- #
def full_case_analysis(case_text):

    # Smart extraction: keep only the most relevant parts for the LLM
    extracted_text = extract_relevant_text(case_text, max_chars=1500)

    # Use full text for embedding search (better section matching)
    search_text = case_text[:3000]
    query_embedding = model.encode(search_text, convert_to_tensor=True)
    hits = util.semantic_search(query_embedding, law_embeddings, top_k=5)

    retrieved_laws = []
    matched_sections = []
    for hit in hits[0]:
        idx = hit["corpus_id"]
        row = df.iloc[idx]

        # Use smart-chunked fields: definition + punishment
        definition = row.get('definition', '') or row['description'][:400]
        punishment = row.get('punishment', '')

        entry = f"- {row['section']}: {definition}"
        if punishment:
            entry += f"\n  Punishment: {punishment}"
        retrieved_laws.append(entry)
        matched_sections.append(row['section'])

    law_context = "\n\n".join(retrieved_laws)

    prompt = f"""You are a senior Indian Criminal Court Judge analyzing an FIR/incident report.
Apply Bharatiya Nyaya Sanhita (BNS), 2023 to the following FACTUAL INCIDENT.
Even if the facts are brief, provide your best legal analysis.

=== FACTUAL INCIDENT (FIR) ===
{extracted_text}

=== POTENTIALLY APPLICABLE BNS SECTIONS ===
{law_context}

=== INSTRUCTIONS ===
Based on the factual incident above, provide the following structured analysis:

1. Case Summary: (Summarize the incident in 2-3 sentences)
2. Legal Ingredients Identified: (Key legal elements from the facts)
3. Applicable BNS Sections: (Which sections apply and why)
4. Legal Reasoning: (How the facts satisfy the legal elements)
5. Possible Punishment: (Imprisonment terms and fines as per BNS)
6. Aggravating Factors: (If any)
7. Mitigating Factors: (If any)
8. Final Legal Opinion: (Conclusion on likely conviction and sentencing)
9. Confidence Level: (0-100%)

Provide the analysis now."""



    # Check cache first
    cached = cache.get_llm_response(prompt)
    if cached:
        return cached, matched_sections

    analysis = call_cloud_llm(prompt)

    # Only cache successful responses (not error messages)
    if not analysis.startswith("⚠️"):
        cache.set_llm_response(prompt, analysis, provider=settings.LLM_PROVIDER)

    return analysis, matched_sections

# ---------------- ROUTES ---------------- #

@app.route("/", methods=["GET", "POST"])
def index():

    analysis = None
    input_text = ""
    similar_cases = None
    similar_cases_json = "[]"

    if request.method == "POST":

        # Get typed text
        input_text = request.form.get("case_description", "").strip()

        # Get uploaded image
        file = request.files.get("fir_file")

        if file and file.filename != "":
            print("Image uploaded. Running OCR...")
            extracted = extract_text_from_image(file)
            print("OCR Extracted Text:", extracted)
            input_text = input_text + " " + extracted

        # Validate minimum input
        input_text = input_text.strip()

        if len(input_text) < 5:
            analysis = "Please provide a case description or upload an image."
        else:
            print(f"Running Legal Analysis... (input: {len(input_text)} chars)")

            # 1. Run AI analysis
            analysis, matched_sections = full_case_analysis(input_text)
            analysis = analysis.replace("**", "")

            # 2. Search for similar cases
            try:
                logger.info("Searching for similar cases...")
                case_results = search_engine.search(
                    fir_text=input_text,
                    bns_sections=matched_sections,
                )

                if case_results:
                    # Compute embedding similarities
                    embedding_scores = find_similar_cases(input_text, case_results)

                    # Update scores with embedding similarity
                    from crawler.ranking import rank_results
                    from crawler.utils import extract_keywords, extract_bns_sections

                    keywords = extract_keywords(input_text)
                    section_nums = []
                    for sec in matched_sections:
                        section_nums.extend(extract_bns_sections(sec))

                    case_results = rank_results(
                        case_results,
                        query_keywords=keywords,
                        query_sections=section_nums,
                        embedding_scores=embedding_scores,
                    )

                    # Deduplicate by URL and take top 8
                    seen_urls = set()
                    similar_cases = []
                    for c in case_results:
                        d = c.to_dict()
                        if d["source_url"] not in seen_urls:
                            seen_urls.add(d["source_url"])
                            similar_cases.append(d)
                        if len(similar_cases) >= 8:
                            break
                    similar_cases_json = json.dumps(similar_cases)

                    logger.info(f"Found {len(similar_cases)} similar cases")
            except Exception as e:
                logger.error(f"Similar case search failed: {e}")
                similar_cases = None

    return render_template(
        "index.html",
        analysis=analysis,
        input_text=input_text,
        similar_cases=similar_cases,
        similar_cases_json=similar_cases_json,
    )

# ---------------- PDF REPORT ---------------- #
@app.route("/download_report", methods=["POST"])
def download_report():

    analysis = request.form["analysis"]
    user_case = request.form["user_case"]

    # Parse similar cases if provided
    similar_cases = None
    cases_json = request.form.get("similar_cases_json", "[]")
    try:
        parsed = json.loads(cases_json)
        if parsed:
            similar_cases = parsed
    except (json.JSONDecodeError, TypeError):
        pass

    pdf_bytes = generate_pdf(analysis, user_case, similar_cases)

    response = make_response(pdf_bytes)
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = "attachment; filename=lawgic_report.pdf"

    return response

# ---------------- HTML REPORT ---------------- #
@app.route("/download_report_html", methods=["POST"])
def download_report_html():

    analysis = request.form["analysis"]
    user_case = request.form["user_case"]

    similar_cases = None
    cases_json = request.form.get("similar_cases_json", "[]")
    try:
        parsed = json.loads(cases_json)
        if parsed:
            similar_cases = parsed
    except (json.JSONDecodeError, TypeError):
        pass

    html = generate_html_report(analysis, user_case, similar_cases)

    response = make_response(html)
    response.headers["Content-Type"] = "text/html"
    response.headers["Content-Disposition"] = "inline; filename=lawgic_report.html"

    return response

# ---------------- JSON EXPORT ---------------- #
@app.route("/api/report_json", methods=["POST"])
def report_json():

    analysis = request.form.get("analysis", "")
    user_case = request.form.get("user_case", "")

    similar_cases = []
    cases_json = request.form.get("similar_cases_json", "[]")
    try:
        similar_cases = json.loads(cases_json)
    except (json.JSONDecodeError, TypeError):
        pass

    report = {
        "generated_at": datetime.datetime.now().isoformat(),
        "platform": "LAWGIC Legal Intelligence",
        "case_description": user_case,
        "ai_analysis": analysis,
        "similar_cases": similar_cases,
    }

    return jsonify(report)


if __name__ == "__main__":
    app.run(
        host=settings.FLASK_HOST,
        port=settings.FLASK_PORT,
        debug=settings.FLASK_DEBUG
    )