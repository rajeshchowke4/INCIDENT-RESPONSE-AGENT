import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from backend.config import settings
from backend.memory.hindsight_manager import memory_manager
from backend.agent.sre_agent import sre_agent
from backend.agent.postmortem_generator import postmortem_generator
from backend.agent.llm_client import llm_client
from backend.mock_telemetry.incident_scenarios import SCENARIOS

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("resqops_api")

app = FastAPI(
    title="ResqOps - SRE Incident Copilot with Hindsight Memory",
    description="Autonomous on-call incident response and institutional post-mortem memory system powered by Hindsight.",
    version="1.0.0"
)

# Enable CORS for local web dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files directory
FRONTEND_DIR = Path(__file__).parent.parent / "frontend"

# Request Schemas
class InvestigateRequest(BaseModel):
    service: str
    severity: str
    alert_name: str
    summary: str
    raw_logs: str
    timestamp: Optional[str] = None

class PostMortemRequest(BaseModel):
    service: str
    title: str
    severity: str
    summary: str
    raw_logs: str
    resolution_notes: str
    failed_attempts_notes: Optional[str] = None

class SettingsUpdateRequest(BaseModel):
    hindsight_api_key: Optional[str] = None
    hindsight_base_url: Optional[str] = None
    hindsight_bank_id: Optional[str] = None
    groq_api_key: Optional[str] = None
    gemini_api_key: Optional[str] = None

class ManualRetainRequest(BaseModel):
    content: str
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

# --- API Endpoints ---

@app.get("/api/status")
def get_system_status():
    """Returns the live status of Hindsight Memory, LLM inference, and memory count."""
    hindsight_status = memory_manager.get_status()
    return {
        "status": "online",
        "hindsight": hindsight_status,
        "llm": {
            "has_groq_key": bool(settings.GROQ_API_KEY),
            "groq_model": settings.GROQ_MODEL,
            "has_gemini_key": bool(settings.GEMINI_API_KEY),
            "active_provider": "Groq" if settings.GROQ_API_KEY else ("Gemini" if settings.GEMINI_API_KEY else "Intelligent SRE Offline Engine")
        },
        "promo_code_tip": "Use promo code MEMHACK99 on https://ui.hindsight.vectorize.io for $50 free Hindsight Cloud credits."
    }

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    """Dynamically updates credentials and reconnects memory/LLM clients."""
    if req.hindsight_api_key is not None:
        memory_manager.update_credentials(
            api_key=req.hindsight_api_key,
            base_url=req.hindsight_base_url,
            bank_id=req.hindsight_bank_id
        )
    if req.groq_api_key is not None or req.gemini_api_key is not None:
        llm_client.update_keys(groq_key=req.groq_api_key, gemini_key=req.gemini_api_key)
        
    return {"status": "updated", "system": get_system_status()}

@app.get("/api/scenarios")
def list_scenarios():
    """Returns predefined realistic incident scenarios for 1-click demos."""
    return SCENARIOS

@app.post("/api/investigate")
def investigate_incident(req: InvestigateRequest):
    """
    Core evaluation endpoint:
    Runs side-by-side diagnosis comparing Vanilla LLM (Stateless)
    vs ResqOps (Augmented with Hindsight Memory).
    """
    try:
        result = sre_agent.investigate(req.model_dump())
        return result
    except Exception as e:
        logger.error(f"Incident investigation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/memories")
def get_memories(search: Optional[str] = None):
    """Inspects the Hindsight Memory Bank."""
    all_mems = memory_manager.list_all_memories()
    if search:
        s_lower = search.lower()
        filtered = [m for m in all_mems if s_lower in json.dumps(m).lower()]
        return {"total": len(filtered), "memories": filtered}
    return {"total": len(all_mems), "memories": all_mems}

@app.post("/api/memories/retain")
def retain_custom_memory(req: ManualRetainRequest):
    """Manually stores a new runbook or memory snippet into Hindsight."""
    result = memory_manager.local_fallback.retain(
        content=req.content,
        metadata=req.metadata or {},
        tags=req.tags or []
    )
    return {"status": "success", "result": result, "total": len(memory_manager.list_all_memories())}

@app.post("/api/memories/reset")
def reset_memories():
    """Resets memory bank back to original seed post-mortems."""
    memory_manager.clear_all()
    return {"status": "reset", "total": len(memory_manager.list_all_memories())}

@app.post("/api/postmortem/generate")
def generate_and_retain_postmortem(req: PostMortemRequest):
    """
    Generates a standardized blameless post-mortem report
    and immediately retains it into Hindsight Memory.
    """
    try:
        result = postmortem_generator.generate_and_retain(
            service=req.service,
            title=req.title,
            severity=req.severity,
            summary=req.summary,
            raw_logs=req.raw_logs,
            resolution_notes=req.resolution_notes,
            failed_attempts_notes=req.failed_attempts_notes
        )
        return result
    except Exception as e:
        logger.error(f"Post-mortem generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

# Serve Frontend static assets
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

@app.get("/")
def serve_index():
    index_file = FRONTEND_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"message": "ResqOps SRE API is running. Place index.html in /frontend to view UI."}
