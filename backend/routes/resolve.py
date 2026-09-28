# routes/resolve.py
from __future__ import annotations
from datetime import datetime, timezone
from fastapi import APIRouter
from schemas import ResolveRequest, ResolveResponse
from services import memory as mem_svc

router = APIRouter()


@router.post("/resolve", response_model=ResolveResponse)
async def resolve(req: ResolveRequest) -> ResolveResponse:
    now = datetime.now(timezone.utc)
    inc_id = req.incident_id or f"INC-{int(now.timestamp())}"
    retained_ids: list[str] = []

    # 1. Retain resolution outcome
    parts = [f"For {inc_id}"]
    if req.service:
        parts.append(f"on {req.service}")
    parts.append(f": what worked: {req.worked}.")
    if req.failed:
        parts.append(f"What did NOT work (do not repeat): {req.failed}.")
    if req.notes:
        parts.append(f"Notes: {req.notes}.")
    if req.engineer:
        parts.append(f"Resolved by {req.engineer}.")

    resolution_text = " ".join(parts)

    rid = await mem_svc.remember(
        content=resolution_text,
        context="incident resolution",
        when=now,
        doc_id=f"{inc_id}-resolution",
        meta={
            "service": req.service or "",
            "kind": "resolution",
            "incident_id": inc_id,
            "engineer": req.engineer or "",
        },
    )
    if rid:
        retained_ids.append(rid)

    # 2. Also retain updated post-mortem paragraph for future recall
    postmortem_parts = [f"{inc_id}: {req.alert_text[:300]}"]
    if req.service:
        postmortem_parts.append(f"Service: {req.service}.")
    postmortem_parts.append(f"Fix that worked: {req.worked}.")
    if req.failed:
        postmortem_parts.append(f"Fix that did NOT work: {req.failed}.")

    pm_rid = await mem_svc.remember(
        content=" ".join(postmortem_parts),
        context="incident postmortem",
        when=now,
        doc_id=f"{inc_id}-postmortem",
        meta={
            "service": req.service or "",
            "kind": "incident",
            "incident_id": inc_id,
        },
    )
    if pm_rid:
        retained_ids.append(pm_rid)

    # 3. Retain engineer preference if mentioned
    pref_rid = None
    if req.engineer and req.notes and any(
        kw in req.notes.lower() for kw in ["shorter", "longer", "prefer", "brief", "detail"]
    ):
        pref_rid = await mem_svc.remember(
            content=f"Engineer {req.engineer} preference: {req.notes}",
            context="engineer preference",
            when=now,
            doc_id=f"pref-{req.engineer}-{int(now.timestamp())}",
            meta={"kind": "preference", "engineer": req.engineer},
        )
        if pref_rid:
            retained_ids.append(pref_rid)

    # 4. Generate automated post-mortem document
    import prompts
    from services import llm as llm_svc
    pm_user = prompts.POSTMORTEM_USER.format(
        alert_text=req.alert_text[:1000],  # truncate to save tokens
        worked=req.worked,
        failed=req.failed or "None",
        notes=req.notes or "None",
        memories_formatted="(Context omitted to save tokens, refer to alert text and resolution)"
    )
    
    postmortem_md = "Failed to generate post-mortem."
    try:
        pm_data = llm_svc.call_llm(
            system=prompts.POSTMORTEM_SYSTEM,
            user=pm_user,
            schema_keys=["postmortem_markdown"]
        )
        postmortem_md = pm_data.get("postmortem_markdown", postmortem_md)
    except Exception as e:
        print("Post-mortem generation failed:", e)

    # Update the local backend cache so the UI updates instantly
    try:
        from routes.memories import ALL_MEMORIES
        from schemas import MemoryItem
        
        # Add the resolution
        ALL_MEMORIES.insert(0, MemoryItem(
            text=resolution_text,
            type="incident resolution",
            source=f"{inc_id}-resolution",
            when=str(now)[:10]
        ))
        
        # Add the post-mortem
        ALL_MEMORIES.insert(0, MemoryItem(
            text=" ".join(postmortem_parts),
            type="incident postmortem",
            source=f"{inc_id}-postmortem",
            when=str(now)[:10]
        ))
        
        # Add preference if any
        if pref_rid:
            ALL_MEMORIES.insert(0, MemoryItem(
                text=f"Engineer {req.engineer} preference: {req.notes}",
                type="engineer preference",
                source=f"pref-{req.engineer}-{int(now.timestamp())}",
                when=str(now)[:10]
            ))
    except Exception as e:
        print("Failed to update ALL_MEMORIES cache:", e)

    return ResolveResponse(
        ok=True,
        retained_ids=retained_ids,
        message=f"Saved {len(retained_ids)} memory records for {inc_id}.",
        postmortem_markdown=postmortem_md,
    )
