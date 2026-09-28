# services/llm.py — Groq LLM wrapper with JSON mode, retry, and repair
from __future__ import annotations
import json
import logging
from typing import Any, Optional

from groq import Groq

from config import settings
import prompts

logger = logging.getLogger(__name__)

_client: Optional[Groq] = None


def _get_groq() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _chat(messages: list[dict], model: str, temperature: float = 0.2) -> str:
    """Single chat call, returns raw text content."""
    client = _get_groq()
    resp = client.chat.completions.create(
        model=model,
        messages=messages,
        response_format={"type": "json_object"},
        temperature=temperature,
    )
    return resp.choices[0].message.content or ""


def _repair_json(broken: str, schema_keys: list[str]) -> dict:
    """Ask the LLM to fix broken JSON — one repair attempt."""
    logger.warning("Attempting JSON repair for output: %s…", broken[:120])
    messages = [
        {"role": "system", "content": prompts.JSON_REPAIR_SYSTEM},
        {
            "role": "user",
            "content": prompts.JSON_REPAIR_USER.format(
                broken_json=broken,
                schema_keys=", ".join(schema_keys),
            ),
        },
    ]
    raw = _chat(messages, model=settings.GROQ_MODEL)
    return json.loads(raw)


def call_llm(
    system: str,
    user: str,
    schema_keys: Optional[list[str]] = None,
    temperature: float = 0.2,
) -> dict[str, Any]:
    """
    Call the primary Groq model; on failure retry with the fallback model;
    on JSON parse error attempt one repair call.
    Returns a parsed dict.
    """
    messages = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]

    for attempt, model in enumerate(
        [settings.GROQ_MODEL, settings.GROQ_FALLBACK_MODEL], start=1
    ):
        try:
            raw = _chat(messages, model=model, temperature=temperature)
            try:
                return json.loads(raw)
            except json.JSONDecodeError:
                if schema_keys:
                    return _repair_json(raw, schema_keys)
                raise
        except Exception as e:
            logger.error("LLM call attempt %d with %s failed: %s", attempt, model, e)
            if attempt == 2:
                raise RuntimeError(f"All LLM attempts failed: {e}") from e

    raise RuntimeError("Unexpected exit from call_llm")
