# routes/playbook.py — Living service playbooks via Hindsight reflect
from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException
from schemas import PlaybookResponse
from services import memory as mem_svc

router = APIRouter()

# We store playbook versions locally so we can show diffs
_PLAYBOOK_STORE_PATH = Path(__file__).parent.parent.parent / "data" / "playbooks.json"


def _load_store() -> dict:
    if _PLAYBOOK_STORE_PATH.exists():
        with open(_PLAYBOOK_STORE_PATH) as f:
            return json.load(f)
    return {}


def _save_store(store: dict) -> None:
    _PLAYBOOK_STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(_PLAYBOOK_STORE_PATH, "w") as f:
        json.dump(store, f, indent=2)


@router.get("/playbook/{service}", response_model=PlaybookResponse)
async def get_playbook(service: str) -> PlaybookResponse:
    store = _load_store()
    entry = store.get(service)
    if not entry:
        # Generate on first access
        return await refresh_playbook(service)
    return PlaybookResponse(**entry)


@router.post("/playbook/{service}/refresh", response_model=PlaybookResponse)
async def refresh_playbook(service: str) -> PlaybookResponse:
    from prompts import PLAYBOOK_REFLECT

    # Use reflect to synthesize current playbook from memory
    current_text = await mem_svc.reflect(
        query=PLAYBOOK_REFLECT.format(service=service),
        context=f"service={service}",
        budget="high",
    )

    if not current_text:
        current_text = (
            f"# {service}\n\nNo incidents recorded yet for this service.\n"
            "Resolve incidents and they will appear here automatically."
        )

    store = _load_store()
    existing = store.get(service, {})
    previous_text = existing.get("current")  # promote current → previous

    now = datetime.now(timezone.utc).isoformat()
    store[service] = {
        "current": current_text,
        "previous": previous_text,
        "updated_at": now,
    }
    _save_store(store)

    return PlaybookResponse(
        current=current_text,
        previous=previous_text,
        updated_at=now,
    )
