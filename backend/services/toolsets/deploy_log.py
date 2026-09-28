# services/toolsets/deploy_log.py — Mock deploy evidence source
# This simulates a real deploy log API (like GitHub deployments or Spinnaker).
# In production you'd swap this for a real integration.
from __future__ import annotations
import json
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).parent.parent.parent.parent / "data" / "deploys.json"

_deploys: Optional[list[dict]] = None


def _load() -> list[dict]:
    global _deploys
    if _deploys is None:
        if _DATA_PATH.exists():
            with open(_DATA_PATH) as f:
                _deploys = json.load(f)
        else:
            _deploys = []
    return _deploys


def get_deploys_for_service(service: str) -> list[dict]:
    """Return all deploys for a given service, newest first."""
    return [d for d in _load() if d.get("service") == service]


def get_deploy(deploy_id: str) -> Optional[dict]:
    """Look up a single deploy by ID."""
    return next((d for d in _load() if d.get("id") == deploy_id), None)


def get_recent_deploys(service: str, limit: int = 5) -> list[dict]:
    """Return the N most recent deploys for a service."""
    deploys = get_deploys_for_service(service)
    # Sort by timestamp descending
    deploys.sort(key=lambda d: d.get("timestamp", ""), reverse=True)
    return deploys[:limit]


def format_deploy_context(service: str) -> str:
    """Format recent deploys as a text block for use in LLM prompts."""
    deploys = get_recent_deploys(service, limit=5)
    if not deploys:
        return "(no recent deploy data available)"
    lines = []
    for d in deploys:
        caused = f" → caused {d['caused_incident']}" if d.get("caused_incident") else ""
        lines.append(
            f"  {d.get('id','?')} by {d.get('author','?')} on {d.get('timestamp','?')[:10]}: "
            f"{d.get('change_summary','')}{caused}"
        )
    return "\n".join(lines)
