# routes/risk.py — Pre-deploy risk check
from __future__ import annotations
from fastapi import APIRouter
from schemas import RiskCheckRequest, RiskCheckResponse, EvidenceItem, MemoryItem
from services import memory as mem_svc
from services import llm as llm_svc
from services.toolsets import deploy_log
import prompts

router = APIRouter()

_RISK_SCHEMA_KEYS = [
    "risk_level", "evidence", "recommendation", "watch_metrics", "spoken_summary",
]


@router.post("/risk-check", response_model=RiskCheckResponse)
async def risk_check(req: RiskCheckRequest) -> RiskCheckResponse:
    memories: list[dict] = []

    if req.use_memory:
        # Recall based on change description + service
        query = f"{req.service}: {req.change_description}"
        memories = await mem_svc.recall(query, budget="mid")

        # Also use reflect to get a synthesized view of past changes like this
        reflection = await mem_svc.reflect(
            query=f"What happened after past changes like: {req.change_description} on {req.service}?",
            context=f"service={req.service}",
            budget="low",
        )
        if reflection:
            memories.append({
                "text": reflection,
                "type": "reflection",
                "source": "hindsight-reflect",
                "when": None,
            })

    # Enrich with local deploy log data
    deploy_context = deploy_log.format_deploy_context(req.service)

    memories_fmt = mem_svc.format_memories_for_prompt(memories) if req.use_memory else "(memory disabled)"

    # Truncate diff to prevent exceeding the 8000 TPM token limit
    diff_text = req.diff[:2000] + "\n...(truncated)" if req.diff and len(req.diff) > 2000 else req.diff
    diff_section = f"\nDiff:\n{diff_text}" if diff_text else ""

    user_prompt = prompts.RISK_USER.format(
        service=req.service,
        change_description=req.change_description,
        diff_section=diff_section,
        memories_formatted=memories_fmt,
    )

    # Append deploy context as additional context
    if deploy_context and deploy_context != "(no recent deploy data available)":
        user_prompt += f"\n\nRECENT DEPLOYS FOR {req.service}:\n{deploy_context}"

    data = llm_svc.call_llm(
        system=prompts.RISK_SYSTEM,
        user=user_prompt,
        schema_keys=_RISK_SCHEMA_KEYS,
    )

    return RiskCheckResponse(
        risk_level=data.get("risk_level", "medium"),
        evidence=[EvidenceItem(**e) for e in data.get("evidence", [])],
        recommendation=data.get("recommendation", []),
        watch_metrics=data.get("watch_metrics", []),
        spoken_summary=data.get("spoken_summary", ""),
        memories_used=[MemoryItem(**m) for m in memories],
    )
