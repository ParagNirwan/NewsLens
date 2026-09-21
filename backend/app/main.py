from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from .models import ResearchRequest, ResearchReport
from .services import investigate

ROOT = Path(__file__).resolve().parents[2]
app = FastAPI(title="NewsLens", version="0.1.0")
app.mount("/static", StaticFiles(directory=ROOT / "frontend"), name="static")
@app.get("/", include_in_schema=False)
def dashboard(): return FileResponse(ROOT / "frontend" / "index.html")
@app.get("/api/health")
def health(): return {"status": "ok", "service": "newslens"}
@app.post("/api/research", response_model=ResearchReport)
def research(request: ResearchRequest):
    try: return investigate(request.question.strip())
    except Exception as exc: raise HTTPException(500, "Research could not be completed safely.") from exc
