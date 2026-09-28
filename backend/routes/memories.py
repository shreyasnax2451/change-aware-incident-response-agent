# routes/memories.py — Memory timeline endpoint
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, Query
from schemas import MemorySearchResponse, MemoryItem

router = APIRouter()

# Global cache of all memories loaded on server start
ALL_MEMORIES: list[MemoryItem] = []

def parse_iso(ts: str) -> datetime:
    ts = ts.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(ts).astimezone(timezone.utc)

def incident_to_text(inc: dict) -> str:
    parts = [
        f"{inc['id']} on {inc['started_at'][:10]}, {inc['service']}, {inc['severity']}.",
        f"Detected by: {inc['detected_by']}.",
        f"Symptoms: {inc['symptoms']}",
        f"Error signature: {inc.get('error_signature', '')}",
    ]
    if inc.get("root_cause"): parts.append(f"Root cause: {inc['root_cause']}")
    if inc.get("related_deploy"): parts.append(f"Related deploy: {inc['related_deploy']}")
    for fix in inc.get("fixes_tried", []):
        outcome = "worked" if fix["worked"] else "did NOT work"
        parts.append(f"Fix tried: '{fix['action']}' — {outcome}.")
    if inc.get("resolution"): parts.append(f"Resolution: {inc['resolution']}")
    if inc.get("ttr_minutes"): parts.append(f"TTR: {inc['ttr_minutes']} minutes.")
    return " ".join(parts)

def deploy_to_text(dep: dict) -> str:
    parts = [
        f"Deploy {dep['id']} to {dep['service']} on {dep['timestamp'][:10]}",
        f"by {dep['author']}: {dep['change_summary']}",
    ]
    if dep.get("diff_snippet"): parts.append(f"Diff: {dep['diff_snippet']}")
    if dep.get("caused_incident"): parts.append(f"This deploy caused {dep['caused_incident']}.")
    return " ".join(parts)

def load_initial_memories():
    global ALL_MEMORIES
    ALL_MEMORIES.clear()
    data_dir = Path(__file__).parent.parent.parent / "data"
    
    inc_path = data_dir / "incidents.json"
    if inc_path.exists():
        with open(inc_path) as f:
            for inc in json.load(f):
                try:
                    ALL_MEMORIES.append(MemoryItem(
                        text=incident_to_text(inc),
                        type="incident postmortem",
                        source=f"{inc['id']}-postmortem",
                        when=str(parse_iso(inc["started_at"]))[:10]
                    ))
                except: pass
    
    dep_path = data_dir / "deploys.json"
    if dep_path.exists():
        with open(dep_path) as f:
            for dep in json.load(f):
                try:
                    ALL_MEMORIES.append(MemoryItem(
                        text=deploy_to_text(dep),
                        type="deploy event",
                        source=f"{dep['id']}-deploy",
                        when=str(parse_iso(dep["timestamp"]))[:10]
                    ))
                except: pass
                
    prefs = [
        {"text": "Engineer Ravi prefers briefings of at most 2 sentences: fix first, root cause second.", "id": "pref-ravi-1"},
        {"text": "Engineer Matrix prefers very concise answers. No stack traces.", "id": "pref-matrix-1"},
    ]
    now_str = str(datetime.now(timezone.utc))[:10]
    for p in prefs:
        ALL_MEMORIES.append(MemoryItem(
            text=p["text"], type="engineer preference", source=p["id"], when=now_str
        ))
    
    # Sort descending by date
    ALL_MEMORIES.sort(key=lambda x: x.when or "", reverse=True)

# Run once on server startup (module load)
load_initial_memories()

@router.get("/memories", response_model=MemorySearchResponse)
async def get_memories(q: str = Query(default="")) -> MemorySearchResponse:
    if not q:
        return MemorySearchResponse(results=ALL_MEMORIES)
    
    q_low = q.lower()
    results = []
    for m in ALL_MEMORIES:
        if (q_low in (m.text or "").lower() or 
            q_low in (m.type or "").lower() or 
            q_low in (m.source or "").lower()):
            results.append(m)
    return MemorySearchResponse(results=results)
