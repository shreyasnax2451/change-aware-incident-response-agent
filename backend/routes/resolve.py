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

    return ResolveResponse(
        ok=True,
        retained_ids=retained_ids,
        message=f"Saved {len(retained_ids)} memory records for {inc_id}.",
    )
