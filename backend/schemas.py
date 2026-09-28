# schemas.py — Pydantic request/response models for all API endpoints
from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional, List, Literal


# ─── Shared ──────────────────────────────────────────────────────────────────

class MemoryItem(BaseModel):
    text: str
    type: str
    source: Optional[str] = None
    when: Optional[str] = None


# ─── Triage ──────────────────────────────────────────────────────────────────

class TriageRequest(BaseModel):
    alert_text: str = Field(..., description="Raw alert text, error log, or incident description")
    service: Optional[str] = None
    use_memory: bool = True
    engineer: Optional[str] = None


class SimilarIncident(BaseModel):
    id: str
    when: str
    why_similar: str


class TriageResponse(BaseModel):
    matched: bool
    root_cause: str
    recommended_fix: List[str]
    avoid: List[str]
    similar_incidents: List[SimilarIncident]
    suspect_change: Optional[str] = None
    confidence: Literal["low", "medium", "high"]
    spoken_summary: str
    memories_used: List[MemoryItem] = []


# ─── Resolve ─────────────────────────────────────────────────────────────────

class ResolveRequest(BaseModel):
    incident_id: Optional[str] = None
    alert_text: str
    service: Optional[str] = None
    worked: str = Field(..., description="What action fixed the incident")
    failed: Optional[str] = Field(None, description="What was tried but did not work")
    notes: Optional[str] = None
    engineer: Optional[str] = None


class ResolveResponse(BaseModel):
    ok: bool
    retained_ids: List[str] = []
    message: str = ""


# ─── Risk Check ──────────────────────────────────────────────────────────────

class RiskCheckRequest(BaseModel):
    service: str
    change_description: str = Field(..., description="PR title/description or plain text of the change")
    diff: Optional[str] = None
    use_memory: bool = True


class EvidenceItem(BaseModel):
    id: str
    when: str
    what_happened: str


class RiskCheckResponse(BaseModel):
    risk_level: Literal["low", "medium", "high"]
    evidence: List[EvidenceItem]
    recommendation: List[str]
    watch_metrics: List[str]
    spoken_summary: str
    memories_used: List[MemoryItem] = []


# ─── Playbook ────────────────────────────────────────────────────────────────

class PlaybookResponse(BaseModel):
    current: str
    previous: Optional[str] = None
    updated_at: Optional[str] = None


# ─── Voice ───────────────────────────────────────────────────────────────────

class TranscribeResponse(BaseModel):
    text: str


class SpeakRequest(BaseModel):
    text: str


class VoiceCommandResponse(BaseModel):
    transcript: str
    intent: Literal["triage", "resolve", "preference", "question"]
    result: dict
    spoken_summary: str


# ─── Memory ──────────────────────────────────────────────────────────────────

class MemorySearchResponse(BaseModel):
    results: List[MemoryItem]


# ─── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    hindsight: str
    groq: str
