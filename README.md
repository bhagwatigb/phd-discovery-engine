# 🎯 Automated PhD Discovery Engine

An end-to-end, 100% free-to-use, zero-cost intelligence pipeline designed to automate the discovery and tracking of open PhD positions across **Life Sciences**, **Computational Biology**, **Bioinformatics**, **Systems Biology**, and **Metabolic Modelling**.

The system dynamically scrapes institutional rankings, uncovers active vacancy portals without paid search APIs, renders dynamic JavaScript-heavy sites with anti-bot bypass, extracts structured schema details locally using local LLMs on Apple Silicon GPU, and organizes all findings into an interactive dashboard.

---

## ⚡ Tech Stack & Architecture

| Component | Technology | Cost | Description |
| :--- | :--- | :--- | :--- |
| **Rankings Target Seeder** | `Playwright` + `rapidfuzz` | Free | Headless extraction from QS Rankings with automatic institutional domain mapping |
| **Web Search Discovery** | `ddgs` (DuckDuckGo Engine) | Free | Real-time URL query engine; no API keys, rate limits, or tokens |
| **Web Scraping & Rendering** | `crawl4ai` (Stealth Mode) | Free | Headless Chromium engine equipped with `magic=True` to bypass Cloudflare 403 blocks |
| **Structured LLM Extraction** | `Ollama` (`llama3.2:3b`) | Free | Local on-device Apple Silicon GPU inference using strict Pydantic JSON schemas |
| **Database Storage** | SQLite (`sqlite3`) | Free | Deduplication engine using SHA-256 fingerprinting |
| **User Interface** | `Streamlit` | Free | Interactive dashboard with real-time sync control and regional/application filtering |

---

## 🔄 Pipeline Workflow

```mermaid
graph TD
    A[build_qs_seed.py] -->|Extracts Top 50 Life Sci/Bio Universities| B(universities_seed.json)
    B --> C[Streamlit Dashboard: app.py]
    C -->|Trigger Sync| D[discovery.py: DuckDuckGo Search]
    D -->|Candidate Vacancy URLs| E[extractor.py: Crawl4AI]
    E -->|Clean Markdown Text| F[Local Ollama: Llama 3.2 3B]
    F -->|Pydantic Schema JSON| G[database.py: SQLite DB]
    G -->|Hash-deduped entries| H[(phd_positions.db)]
    H -->|Live Table View| C
