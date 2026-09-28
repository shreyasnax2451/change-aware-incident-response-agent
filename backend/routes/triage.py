# routes/triage.py
from __future__ import annotations
from fastapi import APIRouter
from schemas import TriageRequest, TriageResponse, MemoryItem, SimilarIncident
from services import memory as mem_svc
from services import llm as llm_svc
import prompts

router = APIRouter()

_TRIAGE_SCHEMA_KEYS = [
    "matched", "root_cause", "recommended_fix", "avoid",
    "similar_incidents", "suspect_change", "confidence", "spoken_summary",
]


@router.post("/triage", response_model=TriageResponse)
async def triage(req: TriageRequest) -> TriageResponse:
    # 1. Recall relevant memories (skip if memory disabled)
    memories: list[dict] = []
    if req.use_memory:
        query = req.alert_text
        if req.service:
            query = f"{req.service}: {query}"
        memories = await mem_svc.recall(query, budget="mid")

        # Also pull engineer preferences
        if req.engineer:
            pref_mems = await mem_svc.recall(f"preferences of engineer {req.engineer}", budget="low")
            memories = memories + pref_mems

    # 2. Format memories for prompt
    memories_fmt = mem_svc.format_memories_for_prompt(memories) if req.use_memory else "(memory disabled)"

    # 3. Single LLM call
    user_prompt = prompts.TRIAGE_USER.format(
        alert_text=req.alert_text,
        memories_formatted=memories_fmt,
        engineer=req.engineer or "unknown",
    )
    data = llm_svc.call_llm(
        system=prompts.TRIAGE_SYSTEM,
        user=user_prompt,
        schema_keys=_TRIAGE_SCHEMA_KEYS,
    )

    # 4. Build response
    return TriageResponse(
        matched=bool(data.get("matched", False)),
        root_cause=data.get("root_cause", ""),
        recommended_fix=data.get("recommended_fix", []),
        avoid=data.get("avoid", []),
        similar_incidents=[
            SimilarIncident(**inc) for inc in data.get("similar_incidents", [])
        ],
        suspect_change=data.get("suspect_change"),
        confidence=data.get("confidence", "low"),
        spoken_summary=data.get("spoken_summary", ""),
        memories_used=[MemoryItem(**m) for m in memories],
    )
