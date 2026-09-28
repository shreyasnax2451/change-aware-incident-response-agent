# main.py — FastAPI application entry point
from __future__ import annotations
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config import settings
from routes import triage, resolve, risk, playbook, voice, memories, weakness
from schemas import HealthResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OnCall AI — Change-Aware Incident Memory Agent",
    description=(
        "An on-call assistant that remembers every past production incident, "
        "what caused it, what fixed it — and warns about risky changes before they ship."
    ),
    version="1.0.0",
)

# Allow the Vite dev server to talk to us
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
API = "/api"
app.include_router(triage.router,   prefix=API, tags=["triage"])
app.include_router(resolve.router,  prefix=API, tags=["resolve"])
app.include_router(risk.router,     prefix=API, tags=["risk"])
app.include_router(playbook.router, prefix=API, tags=["playbook"])
app.include_router(voice.router,    prefix=API, tags=["voice"])
app.include_router(memories.router, prefix=API, tags=["memories"])
app.include_router(weakness.router, prefix=API, tags=["weakness"])


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health() -> HealthResponse:
    # Check Hindsight connectivity
    hindsight_status = "ok"
    try:
        if not settings.HINDSIGHT_API_KEY or not settings.HINDSIGHT_BASE_URL:
            hindsight_status = "not configured"
        else:
            from services.memory import _get_client
            hs = _get_client()
            if hs is None:
                hindsight_status = "client unavailable"
    except Exception as e:
        hindsight_status = f"error: {e}"

    # Check Groq connectivity
    groq_status = "ok"
    try:
        if not settings.GROQ_API_KEY:
            groq_status = "not configured"
        else:
            from groq import Groq
            Groq(api_key=settings.GROQ_API_KEY)
    except Exception as e:
        groq_status = f"error: {e}"

    return HealthResponse(hindsight=hindsight_status, groq=groq_status)


@app.on_event("startup")
async def startup() -> None:
    logger.info("OnCall AI backend starting up")
    logger.info("  GROQ_MODEL     = %s", settings.GROQ_MODEL)
    logger.info("  HINDSIGHT_BANK = %s", settings.HINDSIGHT_BANK_ID)
    logger.info("  TTS_PROVIDER   = %s", settings.TTS_PROVIDER)
    if not settings.GROQ_API_KEY:
        logger.warning("  GROQ_API_KEY is not set — LLM calls will fail")
    if not settings.HINDSIGHT_API_KEY:
        logger.warning("  HINDSIGHT_API_KEY is not set — memory calls will be skipped")
