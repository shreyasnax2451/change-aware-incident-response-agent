#!/usr/bin/env python3
"""
smoke_test.py — Verify Hindsight retain/recall/reflect is working.

Usage:
    python scripts/smoke_test.py

Tests:
    1. retain: write a test memory
    2. recall: retrieve it
    3. reflect: synthesize a reflection
    4. Groq: simple LLM call
"""
from __future__ import annotations
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings


def test_groq():
    print("\n── Groq LLM ──────────────────────────────────────")
    if not settings.GROQ_API_KEY:
        print("  SKIP: GROQ_API_KEY not set")
        return
    try:
        from groq import Groq
        client = Groq(api_key=settings.GROQ_API_KEY)
        resp = client.chat.completions.create(
            model=settings.GROQ_MODEL,
            messages=[{"role": "user", "content": 'Reply with only valid JSON: {"status": "ok"}'}],
            response_format={"type": "json_object"},
            temperature=0,
        )
        import json
        data = json.loads(resp.choices[0].message.content)
        assert data.get("status") == "ok", f"Unexpected response: {data}"
        print(f"  ✓ {settings.GROQ_MODEL} responding correctly")
    except Exception as e:
        print(f"  ✗ Groq failed: {e}")


def test_hindsight():
    print("\n── Hindsight Memory ──────────────────────────────")
    if not settings.HINDSIGHT_API_KEY or not settings.HINDSIGHT_BASE_URL:
        print("  SKIP: HINDSIGHT_API_KEY or HINDSIGHT_BASE_URL not set")
        return

    try:
        from hindsight_client import Hindsight  # type: ignore
        hs = Hindsight(
            base_url=settings.HINDSIGHT_BASE_URL,
            api_key=settings.HINDSIGHT_API_KEY,
            timeout=60.0,
        )
        bank = settings.HINDSIGHT_BANK_ID
        print(f"  Bank: {bank}")

        # 1. retain
        print("  Testing retain…")
        hs.retain(
            bank_id=bank,
            content="SMOKE TEST: payments-service DB pool exhaustion test memory. This is a test record.",
            context="incident postmortem",
            timestamp=datetime.now(timezone.utc),
            document_id="smoke-test-001",
            metadata={"kind": "test", "service": "payments-service"},
            retain_async=False,
        )
        print("  ✓ retain succeeded")

        # 2. recall
        print("  Testing recall…")
        import time
        time.sleep(2)  # brief wait for processing
        r = hs.recall(
            bank_id=bank,
            query="payments-service DB pool",
            budget="low",
            max_tokens=1024,
            include_chunks=True,
        )
        if r.results:
            print(f"  ✓ recall returned {len(r.results)} results")
            print(f"    First: {r.results[0].text[:80]}…")
        else:
            print("  ⚠ recall returned 0 results (may need more processing time)")

        # 3. reflect
        print("  Testing reflect…")
        ref = hs.reflect(
            bank_id=bank,
            query="What are the common failure patterns for payments-service?",
            budget="low",
        )
        if ref and ref.text:
            print(f"  ✓ reflect returned text ({len(ref.text)} chars)")
            print(f"    Preview: {ref.text[:120]}…")
        else:
            print("  ⚠ reflect returned empty (bank may need more memories)")

    except ImportError:
        print("  ✗ hindsight-client not installed. Run: pip install hindsight-client")
    except Exception as e:
        print(f"  ✗ Hindsight failed: {e}")


def main():
    print("=== Déjà Vu Smoke Test ===")
    print(f"GROQ_MODEL     = {settings.GROQ_MODEL}")
    print(f"HINDSIGHT_BANK = {settings.HINDSIGHT_BANK_ID}")
    print(f"HINDSIGHT_URL  = {settings.HINDSIGHT_BASE_URL or '(not set)'}")

    test_groq()
    test_hindsight()

    print("\n=== Done ===")


if __name__ == "__main__":
    main()
