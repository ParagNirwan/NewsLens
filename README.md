# NewsLens

<p align="center"><strong>Evidence-aware news research, not another answer box.</strong></p>

<p align="center"><a href="#what-it-does">What it does</a> · <a href="#how-it-works">How it works</a> · <a href="#quick-start">Quick start</a> · <a href="#api">API</a> · <a href="#project-status">Status</a></p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white" alt="Python 3.12+" />
  <img src="https://img.shields.io/badge/FastAPI-0.115%2B-009688?logo=fastapi&logoColor=white" alt="FastAPI" />
  <img src="https://img.shields.io/badge/LLM-Ollama-black" alt="Ollama" />
  <img src="https://img.shields.io/badge/Search-Tavily-FF5A5F" alt="Tavily" />
  <img src="https://img.shields.io/badge/Tests-pytest-0A9EDC?logo=pytest&logoColor=white" alt="pytest" />
</p>

> Ask a news question. NewsLens searches for relevant reporting, reads selected source pages, and produces a cited summary that makes uncertainty visible.

## What it does

NewsLens is an AI-assisted research prototype for questions such as:

> “What happened after the latest local elections?”

It does not treat a search snippet as proof. Instead, it follows a bounded research workflow:

1. Preserves the user's question.
2. Searches the web through Tavily.
3. Deduplicates and relevance-screens candidate sources.
4. Excludes unsuitable social-media sources from page inspection.
5. Retrieves a limited number of public HTML pages with size, timeout, and SSRF protections.
6. Extracts readable text from inspected pages.
7. Uses local Ollama synthesis when available, or a clearly labelled extractive fallback.
8. Returns a report with sources, claim status, research events, and uncertainty.

## Why it matters

Most chat interfaces return an answer before showing their work. NewsLens is built around a different rule:

> **No inspected evidence, no confident conclusion.**

When sources do not establish an answer, the report says so. It does not invent sources, quotes, or certainty.

## How it works

```text
Question
   │
   ▼
FastAPI research endpoint
   │
   ├── Tavily web search
   │       │
   │       ▼
   │   relevance screening + source-role classification
   │       │
   │       ▼
   ├── safe public-page retrieval + text extraction
   │       │
   │       ▼
   └── local Ollama synthesis
           │
           ▼
     evidence-aware report in the dashboard
```

| Layer | Responsibility |
|---|---|
| Dashboard | Accepts a research question and presents reports, claims, sources, and trace events. |
| FastAPI | Serves the dashboard and exposes the research API. |
| Research loop | Searches, filters, retrieves, extracts, synthesizes, and records safe action summaries. |
| Tavily | Supplies web search results. |
| Ollama | Runs local LLM synthesis using inspected source text only. |

## Features

- Evidence-aware summaries tied to inspected source text
- Source deduplication and basic relevance screening
- Source roles: `PRIMARY`, `NEWS`, `ANALYSIS`, and `OFFICIAL`
- Claim statuses such as `SUPPORTED`, `DISPUTED`, and `INSUFFICIENT_EVIDENCE`
- High-level agent trace that does not expose hidden reasoning
- Safe page retrieval with public-address validation, timeouts, response limits, and HTML-only checks
- Local model support through Ollama
- Graceful fallbacks when search, page retrieval, or local synthesis is unavailable

## Quick start

### Prerequisites

- Python 3.12 or newer
- A [Tavily](https://tavily.com/) API key for live web discovery
- [Ollama](https://ollama.com/) and a local model such as `gemma3:4b` for structured summaries

### Install and run

```powershell
git clone <your-repository-url>
cd NewsLens

python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

Copy-Item .env.example .env
python main.py
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000).

### Configure local secrets

Create `.env` from `.env.example` and set:

```env
TAVILY_API_KEY=your_tavily_key_here
OLLAMA_MODEL=gemma3:4b
```

Start Ollama and download the selected model if necessary:

```powershell
ollama pull gemma3:4b
ollama serve
```

`OLLAMA_MODEL` is optional. If Ollama is unavailable, NewsLens uses a weaker extractive summary and labels that limitation in the report. Without a Tavily key, it runs in safe-demo mode and does not invent live research results.

## API

### `POST /api/research`

```json
{
  "question": "What happened after the latest local elections?"
}
```

The response includes an executive summary, established facts, claims, cited sources, uncertainty, and high-level research events.

### `GET /api/health`

Returns the service health status.

## Project structure

```text
NewsLens/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI routes and static dashboard host
│       ├── models.py        # Request, source, claim, event, and report models
│       └── services.py      # Bounded research loop and tool adapters
├── frontend/
│   ├── index.html           # Dashboard structure
│   ├── app.js               # Browser-side report rendering
│   └── styles.css           # Editorial dashboard styling
├── tests/
│   └── test_services.py     # Offline unit tests
├── docs/
│   ├── PROJECT_GUIDE.md     # File guide and pre-push checklist
│   └── PROJECT_PLAN.md      # Original roadmap
├── .env.example
├── requirements.txt
└── main.py                  # Development server entry point
```

## Run tests

```powershell
.\.venv\Scripts\python.exe -m pytest -q tests
```

## Project status

This is a working first-pass research prototype, not a finished fact-checking platform.

| Available now | Planned next |
|---|---|
| Search, page retrieval, source filtering, text extraction, local synthesis, source links, and a research trace | Primary-source discovery, multi-step query planning, persistence, richer claim extraction, evaluation benchmarks, and Docker deployment |

## Safety and limits

- Search results are discovery material, not verified evidence.
- The app only summarizes text from pages it successfully inspected.
- It limits the number of pages and response sizes per request.
- It does not present political orientation as proof of truth or falsehood.
- It is not legal, medical, financial, or professional fact-checking advice.
- Read the linked source pages before relying on a report for consequential decisions.

## Documentation

- [Project guide and pre-push checklist](docs/PROJECT_GUIDE.md)
- [Project roadmap](docs/PROJECT_PLAN.md)

## Before pushing

Never commit `.env` or API keys. Review [the pre-push checklist](docs/PROJECT_GUIDE.md#before-you-push) before publishing the repository.
