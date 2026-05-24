# Detailed Upgrade Prompt for LAWGIC-Crawler

Use this as a master implementation prompt for yourself, GitHub Copilot, Cursor, Claude Code, or another AI coding assistant.

---

## PROJECT GOAL

Transform the existing LAWGIC project into an advanced AI-powered Legal Intelligence & Web Case Discovery platform.

The current project already:

* Analyzes FIR descriptions
* Recommends BNS/IPC sections
* Uses local NLP models
* Uses Ollama locally
* Generates reports

The upgraded version should:

* Add intelligent web crawling
* Retrieve similar legal cases and judgments
* Include source links in reports
* Generate printable legal research reports
* Replace slow local LLM inference with cloud-based Ollama models/APIs
* Improve architecture, modularity, and scalability

---

# REQUIRED CHANGES

## 1. REMOVE LOCAL MODEL DEPENDENCY

### Current Problem

The current repo uses locally running Ollama/Llama models which are slow and resource-intensive.

### Required Change

Replace local inference with cloud-hosted LLM APIs.

### Target

Use:

* Ollama Cloud models (if available)
  OR
* Groq API
  OR
* OpenRouter
  OR
* Gemini API
  OR
* Together AI

Preferred:

* Ollama-compatible cloud endpoint
* OpenAI-compatible API structure

### Requirements

* Move API keys to `.env`
* Add configurable provider support
* Add fallback provider logic
* Add timeout + retry handling
* Add streaming response support

### New Files

Create:

* `services/llm_service.py`
* `config/settings.py`

### Environment Variables

```env
LLM_PROVIDER=groq
LLM_API_KEY=your_key
LLM_MODEL=llama-3.3-70b
LLM_BASE_URL=https://api.groq.com/openai/v1
```

---

# 2. ADD WEB CRAWLING MODULE

## Goal

Search the web for:

* Similar legal cases
* Related judgments
* Matching FIRs
* Legal precedents
* Relevant legal articles

---

## New Folder Structure

```bash
crawler/
├── search_engine.py
├── scraper.py
├── parser.py
├── ranking.py
├── sources.py
└── utils.py
```

---

## Functional Requirements

### Input

The crawler should use:

* FIR text
* Extracted keywords
* Recommended BNS sections
* Semantic embeddings

### Output

Return:

* Case title
* Summary
* Court/source
* Relevant sections
* Similarity score
* Source URL

---

## Suggested Sources

### Legal Websites

* Indian Kanoon
* Supreme Court archives
* High Court websites
* Government legal portals
* Public judgments

### IMPORTANT

Respect:

* robots.txt
* rate limits
* legal compliance

---

# 3. ADD SEMANTIC LEGAL SEARCH

## Goal

Retrieve similar legal cases using embeddings instead of only keywords.

---

## Requirements

Use:

* Sentence Transformers
* FAISS vector search

### Flow

1. Convert FIR → embedding
2. Convert crawled cases → embeddings
3. Perform semantic similarity search
4. Rank results

---

## New Files

```bash
retrieval/
├── embedder.py
├── vector_store.py
├── similarity.py
└── reranker.py
```

---

# 4. PRINTABLE LEGAL REPORTS

## Goal

Generate professional legal intelligence reports.

---

## Report Sections

### Include

* FIR Summary
* Recommended BNS/IPC Sections
* Punishments
* AI Legal Reasoning
* Similar Cases
* Source Links
* Legal References
* Confidence Score

---

## Output Formats

### Required

* PDF
* Printable HTML

### Optional

* DOCX
* JSON export

---

## Improve Existing PDF Generation

Replace simple FPDF formatting with:

* Better typography
* Tables
* Hyperlinks
* Structured layouts

Recommended:

* WeasyPrint
  OR
* ReportLab

---

# 5. ADD CLICKABLE CASE REFERENCES

## Requirement

Every crawled result must include:

* Clickable source URL
* Court/judgment reference
* Related legal section

---

## Example Output

```json
{
  "case_title": "State vs XYZ",
  "court": "Delhi High Court",
  "summary": "Case involving financial fraud...",
  "sections": ["BNS 318", "IPC 420"],
  "similarity_score": 0.89,
  "source_url": "https://..."
}
```

---

# 6. IMPROVE PROJECT ARCHITECTURE

## Current Issue

The current repo is too monolithic.

---

## Refactor Into Modules

```bash
app/
├── routes/
├── services/
├── crawler/
├── retrieval/
├── reports/
├── templates/
├── static/
├── models/
└── utils/
```

---

# 7. ADD ASYNC PROCESSING

## Goal

Web crawling and LLM requests should not block the UI.

---

## Requirements

Use:

* Asyncio
* aiohttp
* Background tasks

Optional:

* Celery + Redis

---

# 8. ADD SEARCH RESULT RANKING

## Goal

Rank cases by:

* Semantic similarity
* Legal section overlap
* Keyword relevance
* Recency
* Court authority

---

## Scoring Formula

Weighted scoring:

```python
final_score =
0.5 * embedding_similarity +
0.2 * keyword_match +
0.2 * section_overlap +
0.1 * source_authority
```

---

# 9. ADD CACHING

## Goal

Avoid repeated crawling and repeated embeddings.

---

## Use

* Redis
  OR
* SQLite cache

Cache:

* Search results
* Embeddings
* LLM responses

---

# 10. FRONTEND IMPROVEMENTS

## Required UI Changes

### Add:

* Similar Cases panel
* Source links
* PDF download button
* Search progress indicator
* Confidence visualization
* Expandable reasoning sections

---

# 11. SECURITY IMPROVEMENTS

## Add

* Input sanitization
* API rate limiting
* Error handling
* Secure env handling
* Logging

---

# 12. DATABASE CHANGES

## Add Tables

### Similar Cases

```sql
similar_cases (
    id,
    fir_id,
    title,
    summary,
    source_url,
    court,
    similarity_score
)
```

### Crawled Results Cache

```sql
crawl_cache (
    query_hash,
    response,
    created_at
)
```

---

# 13. OPTIONAL ADVANCED FEATURES

## Future Upgrades

### Add:

* RAG-based legal chatbot
* Legal timeline extraction
* Multi-language FIR support
* Judge prediction analytics
* Graph-based crime relation mapping
* Real-time legal news ingestion

---

# 14. DEPLOYMENT CHANGES

## Replace Local-Only Setup

### Add:

* Docker support
* Cloud deployment support
* Gunicorn
* Nginx

---

## Create:

```bash
Dockerfile
docker-compose.yml
```

---

# 15. PERFORMANCE TARGETS

## Goals

### FIR Analysis

< 5 sec

### Similar Case Retrieval

< 10 sec

### PDF Generation

< 3 sec

### Concurrent Users

50+

---

# 16. UPDATED PROJECT DESCRIPTION

Use this description in README:

> LAWGIC-Crawler is an AI-powered legal intelligence platform that combines NLP, semantic similarity, web crawling, OCR, and cloud-hosted LLMs to analyze FIR descriptions, recommend BNS/IPC sections, retrieve similar legal cases and judgments, and generate structured printable legal research reports with linked legal references.

---

# 17. FINAL DELIVERABLES

The upgraded project should provide:

✅ FIR analysis
✅ AI legal reasoning
✅ Cloud-hosted LLM support
✅ Similar case discovery
✅ Intelligent web crawling
✅ Semantic legal search
✅ Printable legal reports
✅ Source-linked judgments
✅ Modern scalable architecture
✅ Fast inference without local GPU dependency
✅ Updated README.md with all the changes