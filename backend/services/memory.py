# services/memory.py — Hindsight client wrapper (async-native)
from __future__ import annotations
import logging
from datetime import datetime
from typing import Optional, Any

from config import settings

logger = logging.getLogger(__name__)


def _get_client():
    """
    Lazy-load the Hindsight client.
    Returns None if keys/URL are missing — callers must handle None gracefully.
    """
    # Explicit guard: both must be non-empty strings
    if not settings.HINDSIGHT_BASE_URL or not settings.HINDSIGHT_API_KEY:
        return None
    try:
        from hindsight_client import Hindsight  # type: ignore
        return Hindsight(
            base_url=settings.HINDSIGHT_BASE_URL,
            api_key=settings.HINDSIGHT_API_KEY,
            timeout=60.0,
        )
    except Exception as e:
        logger.warning("Hindsight client unavailable: %s", e)
        return None


BANK = settings.HINDSIGHT_BANK_ID


async def remember(
    content: str,
    context: str,
    when: datetime,
    doc_id: str,
    meta: dict[str, Any],
) -> Optional[str]:
    """
    Retain a memory in Hindsight (async).
    Returns the retained document ID or None on failure/missing config.
    """
    hs = _get_client()
    if not hs:
        logger.debug("remember() skipped — Hindsight not configured")
        return None
    try:
        result = await hs.aretain(
            bank_id=BANK,
            content=content,
            context=context,
            timestamp=when,
            document_id=doc_id,
            metadata=meta,
        )
        return getattr(result, "document_id", doc_id)
    except Exception as e:
        logger.error("aretain() failed: %s", e)
        return None


async def recall(query: str, budget: str = "mid") -> list[dict]:
    """
    Recall relevant memories for a query (async).
    Returns a list of dicts with 'text', 'type', 'source', 'when' keys.
    Returns [] gracefully when Hindsight is not configured.
    """
    hs = _get_client()
    if not hs:
        logger.debug("recall() skipped — Hindsight not configured")
        return []
    try:
        r = await hs.arecall(
            bank_id=BANK,
            query=query,
            budget=budget,
            max_tokens=1500,
            include_chunks=True,
        )
        out = []
        for m in r.results:
            chunk_id = getattr(m, "chunk_id", None)
            chunk = (r.chunks or {}).get(chunk_id) if chunk_id else None
            out.append({
                "text": getattr(m, "text", ""),
                "type": getattr(m, "type", ""),
                "source": chunk.text[:400] if chunk else getattr(m, "document_id", None),
                "when": str(getattr(m, "timestamp", ""))[:10] or None,
            })
        return out
    except Exception as e:
        logger.error("arecall() failed: %s", e)
        return []


async def reflect(query: str, context: Optional[str] = None, budget: str = "mid") -> str:
    """
    Ask Hindsight to synthesize a reflection over the memory bank (async).
    Returns plain text, or "" when Hindsight is not configured.
    """
    hs = _get_client()
    if not hs:
        logger.debug("reflect() skipped — Hindsight not configured")
        return ""
    try:
        result = await hs.areflect(
            bank_id=BANK,
            query=query,
            context=context,
            budget=budget,
        )
        return getattr(result, "text", "") or ""
    except Exception as e:
        logger.error("areflect() failed: %s", e)
        return ""


def format_memories_for_prompt(memories: list[dict]) -> str:
    """Format a list of memory dicts into the prompt block."""
    if not memories:
        return "(no relevant memory found)"
    lines = []
    for i, m in enumerate(memories, 1):
        lines.append(
            f"[{i}] type={m.get('type','?')} source={m.get('source','?')} when={m.get('when','?')}\n"
            f"    {m.get('text','')}"
        )
    return "\n".join(lines)
