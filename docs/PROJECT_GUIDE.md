# NewsLens File Guide and Pre-Push Checklist

## What each file does

| File / folder | Purpose |
|---|---|
| `main.py` | Local development entry point. Starts the FastAPI server at `http://127.0.0.1:8000`. |
| `backend/app/main.py` | Defines the FastAPI application, serves the dashboard, and exposes `GET /api/health` and `POST /api/research`. |
| `backend/app/models.py` | Pydantic data models for sources, claims, agent events, requests, and final reports. |
| `backend/app/services.py` | Core research loop: web search, relevance screening, safe page retrieval, text extraction, optional Ollama synthesis, and report generation. |
| `frontend/index.html` | Dashboard page structure and research form. |
| `frontend/app.js` | Sends questions to the API and renders the report, sources, claims, and research trace. |
| `frontend/styles.css` | Dashboard visual design and responsive layout. |
| `tests/test_services.py` | Offline unit tests for source classification, relevance filtering, and social-source exclusions. |
| `test_search.py` | Manual Tavily smoke script; it runs only when explicitly invoked, not during pytest. |
| `requirements.txt` | Python packages required to run and test the project. |
| `.env.example` | Safe template for local environment settings. Commit this file. |
| `.env` | Your local secrets and model settings. Never commit it. |
| `.gitignore` | Excludes secrets, virtual environments, Python caches, and test cache files from Git. |
| `README.md` | Setup and architecture overview for users of the repository. |
| `docs/PROJECT_PLAN.md` | The original project vision and phased roadmap. |

## Before you push

1. **Rotate the Tavily key that was previously exposed.** Create a new key in Tavily, put it only in `.env`, and revoke the old one.

2. **Confirm Git will not include secrets.** Run:

   ```powershell
   git status --short
   git check-ignore .env
   ```

   `.env` must not appear in `git status`; `git check-ignore .env` should print `.env`.

3. **Review every staged change before committing.**

   ```powershell
   git add .
   git diff --cached
   ```

   Check specifically that no API key, token, personal path, or research output containing private information is staged.

4. **Run the tests.**

   ```powershell
   .\.venv\Scripts\python.exe -m pytest -q tests
   ```

5. **Run the app manually.**

   ```powershell
   python main.py
   ```

   Open `http://127.0.0.1:8000`, submit a question, and confirm the report either has citations or clearly says evidence was insufficient.

6. **Check your local configuration.** Live research requires `TAVILY_API_KEY`. Rich synthesis uses a running local Ollama service with `gemma3:4b` by default, or the model named by `OLLAMA_MODEL`.

7. **Use an honest README description.** This is a first-pass research prototype, not a finished fact-checking service: it inspects a limited number of pages, has no database, and does not yet perform primary-source discovery.

## Recommended first commit

```powershell
git add README.md PROJECT_GUIDE.md .gitignore .env.example requirements.txt main.py backend frontend tests test_search.py
git diff --cached
git commit -m "Build NewsLens research prototype"
```

Do not add `.env`, `.venv`, `__pycache__`, or `.pytest_cache`.
