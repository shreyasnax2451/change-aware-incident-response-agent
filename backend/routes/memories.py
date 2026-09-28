# routes/memories.py — Memory timeline endpoint
from __future__ import annotations
from fastapi import APIRouter, Query
from schemas import MemorySearchResponse, MemoryItem
from services import memory as mem_svc

router = APIRouter()


@router.get("/memories", response_model=MemorySearchResponse)
async def get_memories(q: str = Query(default="")) -> MemorySearchResponse:
    query = q.strip() if q.strip() else "incident deploy resolution preference"
    memories = await mem_svc.recall(query, budget="high")
    return MemorySearchResponse(
        results=[MemoryItem(**m) for m in memories]
    )
