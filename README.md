# LAWGIC-Crawler – AI-Powered Legal Intelligence & Case Discovery Platform

> LAWGIC-Crawler is an AI-powered legal intelligence platform that combines NLP, semantic similarity, web crawling, OCR, and cloud-hosted LLMs to analyze FIR descriptions, recommend BNS/IPC sections, retrieve similar legal cases and judgments, and generate structured printable legal research reports with linked legal references.

---

## Features

### Core Analysis
- 🧠 **AI-powered FIR analysis** using cloud-hosted LLMs (Groq, Gemini, OpenRouter)
- ⚖️ **BNS/IPC section recommendation** via semantic similarity matching
- 🎤 **Voice input** using Web Speech API
- 📷 **Image-based FIR input** using OCR (Tesseract)

### Case Discovery (NEW)
- 🔍 **Intelligent web crawling** — searches Indian Kanoon for similar cases
- 📊 **Semantic similarity scoring** — ranks cases using embedding similarity + keywords + section overlap
- 🏛️ **Court authority scoring** — weighs Supreme Court results higher than lower courts
- 🔗 **Clickable source links** — every result links to the original case

### Reports
- 📄 **Enhanced PDF reports** with professional typography, case cards, and hyperlinks
- 🌐 **Printable HTML reports** with modern design
- 📋 **JSON export** for programmatic access

### Architecture
- ☁️ **Cloud LLM integration** — no local GPU required (configurable provider + fallback)
- 💾 **SQLite caching** — avoids redundant LLM calls and web crawling
- 🔒 **Security** — input sanitization, rate limiting, structured logging
- 🐳 **Docker support** — containerized deployment with Gunicorn

---

## System Architecture

```
User Input (Text / Voice / Image)
        │
        ▼
   ┌─────────┐
   │  Flask   │ ← Web Interface
   │  Server  │
   └────┬─────┘
        │
   ┌────┴────────────────────────────┐
   │                                 │
   ▼                                 ▼
┌──────────┐                 ┌──────────────┐
│ OCR      │                 │ Embedding    │
│ (Tesseract)│               │ (MiniLM-L6)  │
└──────────┘                 └──────┬───────┘
                                    │
                    ┌───────────────┼───────────────┐
                    │               │               │
                    ▼               ▼               ▼
            ┌──────────┐   ┌──────────┐    ┌──────────────┐
            │ BNS Law  │   │ Cloud    │    │ Web Crawler  │
            │ Matching │   │ LLM API  │    │ (Indian      │
            │          │   │ (Groq)   │    │  Kanoon)     │
            └──────────┘   └──────────┘    └──────────────┘
                    │               │               │
                    └───────────────┼───────────────┘
                                    │
                                    ▼
                            ┌──────────────┐
                            │ Report Gen   │
                            │ (PDF/HTML)   │
                            └──────────────┘
```

---

## Project Structure

```
Lawgic-Crawler/
├── app.py                  # Main Flask application
├── config/
│   ├── __init__.py
│   └── settings.py         # Central configuration
├── services/
│   ├── __init__.py
│   ├── llm_service.py      # Cloud LLM API client
│   ├── report_generator.py # PDF + HTML report generation
│   └── cache_service.py    # SQLite caching
├── crawler/
│   ├── __init__.py
│   ├── search_engine.py    # Search orchestrator
│   ├── scraper.py          # Web scraping + HTTP
│   ├── parser.py           # Legal document parser
│   ├── ranking.py          # Result ranking
│   ├── sources.py          # Legal source definitions
│   └── utils.py            # Rate limiting, helpers
├── retrieval/
│   ├── __init__.py
│   ├── embedder.py         # SentenceTransformer wrapper
│   ├── vector_store.py     # FAISS vector index
│   ├── similarity.py       # Semantic search
│   └── reranker.py         # LLM-based reranking (placeholder)
├── templates/
│   └── index.html          # Web interface
├── static/
│   ├── css/style.css       # Stylesheet
│   └── js/app.js           # Client-side JavaScript
├── build_db.py             # Database builder
├── parse_bns.py            # BNS text parser
├── bns_laws.csv            # Parsed BNS sections
├── raw_bns.txt             # Raw BNS text
├── lawgic.db               # SQLite database
├── requirements.txt        # Python dependencies
├── .env.example            # Environment template
├── Dockerfile              # Container build
├── docker-compose.yml      # Container orchestration
└── README.md               # This file
```

---

## Technologies Used

| Category | Technology |
|----------|------------|
| Language | Python 3.11+ |
| Web Framework | Flask |
| NLP | Sentence Transformers (all-MiniLM-L6-v2) |
| Vector Search | FAISS |
| Cloud LLM | Groq / Gemini / OpenRouter (OpenAI-compatible) |
| Web Crawling | BeautifulSoup4, Requests |
| OCR | Tesseract, Pillow |
| Voice Input | Web Speech API |
| Database | SQLite |
| Reports | FPDF, HTML/CSS |
| Deployment | Docker, Gunicorn |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/Lawgic-Crawler.git
cd Lawgic-Crawler
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env with your API key:
# LLM_PROVIDER=groq
# LLM_API_KEY=your_groq_api_key
```

### 5. Build the Database (if needed)

```bash
python build_db.py
```

### 6. Run the Application

```bash
python app.py
```

Open your browser and go to: **http://localhost:5050**

### Docker (Optional)

```bash
docker-compose up --build
```

---

## Usage

1. **Enter a case description** in the input field
2. Optionally: **speak** the FIR using voice input or **upload** an FIR image
3. Click **⚡ Analyze Case**
4. The system will display:
   - AI legal analysis with BNS sections, reasoning, and punishments
   - Confidence score visualization
   - Similar cases from Indian Kanoon with relevance scores
5. **Download** the complete analysis as PDF, printable HTML, or JSON

---

## Configuration

All settings are configured via `.env` file. See [.env.example](.env.example) for all options.

### LLM Providers

| Provider | Base URL | Free Tier |
|----------|----------|-----------|
| **Groq** (default) | `https://api.groq.com/openai/v1` | ✅ Yes |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai` | ✅ Yes |
| OpenRouter | `https://openrouter.ai/api/v1` | ✅ Limited |
| Ollama (local) | `http://localhost:11434/v1` | N/A |

---

## Performance Targets

| Operation | Target |
|-----------|--------|
| FIR Analysis | < 5 sec |
| Similar Case Retrieval | < 10 sec |
| PDF Generation | < 3 sec |
| Concurrent Users | 50+ |

---

## Limitations

- The system depends on the quality of the FIR description
- OCR accuracy depends on image clarity
- Voice recognition may be affected by background noise
- Web crawling results depend on Indian Kanoon availability
- This system is designed for academic purposes and does not replace professional legal advice

---

## Future Enhancements

- RAG-based legal chatbot
- Legal timeline extraction
- Multi-language FIR support
- Judge prediction analytics
- Graph-based crime relation mapping
- Real-time legal news ingestion

---

## Credits & Acknowledgments

### Original Developers (Parent Repository)
This project is forked from the parent repository [reventhelangovan2005gmailcom/LAWGIC](https://github.com/reventhelangovan2005gmailcom/LAWGIC) developed by:
* **Reventh E** (Reg_no: 2260422, BTCS CU'26)
* **Charunetra M** (Reg_no: 2260391, BTCS CU'26)
* **Under the guidance of**: Dr. Kalyana Saravanan.A (Associate Professor)

**Department of Computer Science and Engineering**  
**CHRIST (Deemed to be University), Bangalore**

---

### Upgraded & Modular Edition (Current Fork)

This version of the platform has been extensively re-engineered and upgraded as part of a **corporate academic internship (1st – 30th May 2026)** with:  
**UTINA INFOTECH PRIVATE LIMITED**

#### Fork Team Developers

##### M.Tech in Computer Science and Engineering (3MTCS)
* **Shivangi** (Roll No: 2567113 | [shivangi.a@mtech.christuniversity.in](mailto:shivangi.a@mtech.christuniversity.in))
* **SN Chandra Kanta Kund** (Roll No: 2567114 | [sn.chandra@mtech.christuniversity.in](mailto:sn.chandra@mtech.christuniversity.in))
* **Arnab Mondal** (Roll No: 2567118 | [arnab.mondal@mtech.christuniversity.in](mailto:arnab.mondal@mtech.christuniversity.in))

##### M.Tech in Data Science (3MTDS)
* **Abhishek Deep** (Roll No: 2567201 | [abhishek.deep@mtech.christuniversity.in](mailto:abhishek.deep@mtech.christuniversity.in))
* **Anshu Kumari** (Roll No: 2567203 | [anshu.kumari@mtech.christuniversity.in](mailto:anshu.kumari@mtech.christuniversity.in))

**Under the guidance of:** Dr. Kalyana Saravanan.A (Associate Professor)  
**CHRIST (Deemed to be University), Bangalore**

---

#### Engineering Enhancements & Upgrades
The fork team transformed the initial baseline baseline into a robust, high-performance, modular system:
- 🛠️ **Modular Re-architecture**: Split the monolithic codebase into structured packages (`crawler/`, `retrieval/`, `services/`, `config/`) for long-term scalability and clean separation of concerns.
- 🧠 **Smart BNS Chunking Parser**: Developed a custom regex-based parser that segments raw BNS chapters into discrete semantic components (definitions, punishments, illustrations, and exceptions).
- 🔍 **Indian Kanoon Crawler Upgrade**: Bypassed strict robots.txt blocks safely, introduced an elegant multi-query orchestration engine, and implemented robust selectors to parse court tiers, snippets, and document links.
- ⚡ **Cross-Query Deduplication & Ranking**: Implemented multi-criteria ranking weights (keyword relevancy, section overlap, court-tier authority) with full cross-query URL deduplication.
- 💾 **SQLite Semantic Caching**: Configured a local high-performance SQLite LLM cache table to minimize latency and bypass cloud API costs on redundant queries, with strict error exclusions.
- ☁️ **Native Ollama & Fallbacks**: Integrated native `/api/chat` support for local or cloud-hosted Ollama models (such as `gemma4:31b-cloud`) with reliable multi-provider fallback.
- 🚀 **Input Robustness & Sentence Ranking**: Added embedding-based sentence ranking to automatically extract the top 15 most factual sentences from raw, multi-thousand-character FIR inputs to stay within LLM context windows.

---

**Disclaimer:** This system is developed for academic and research purposes. The recommendations generated by the system should not be considered as official legal advice.
