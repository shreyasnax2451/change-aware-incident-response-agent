# routes/weakness.py
from __future__ import annotations
from fastapi import APIRouter
from schemas import WeaknessReportRequest, WeaknessReportResponse, MemoryItem
from services import memory as mem_svc
from services import llm as llm_svc
import prompts

router = APIRouter()

@router.post("/weakness", response_model=WeaknessReportResponse)
async def analyze_weakness(req: WeaknessReportRequest) -> WeaknessReportResponse:
    # 1. Recall past incidents for the service
    memories = await mem_svc.recall(req.service, budget="high")
    
    # 2. Format memories
    memories_fmt = mem_svc.format_memories_for_prompt(memories)
    
    # 3. LLM call
    user_prompt = prompts.WEAKNESS_USER.format(
        service=req.service,
        memories_formatted=memories_fmt
    )
    
    data = llm_svc.call_llm(
        system=prompts.WEAKNESS_SYSTEM,
        user=user_prompt,
        schema_keys=["report_markdown"]
    )
    
    return WeaknessReportResponse(
        service=req.service,
        report_markdown=data.get("report_markdown", "Failed to generate report."),
        memories_used=[MemoryItem(**m) for m in memories]
    )
