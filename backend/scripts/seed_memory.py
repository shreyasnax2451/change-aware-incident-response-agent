#!/usr/bin/env python3
"""
seed_memory.py — Seed the Hindsight bank with all Kirana Cart history.

Usage:
    python scripts/seed_memory.py

Prerequisites:
    - data/incidents.json and data/deploys.json must exist (run generate_data.py first)
    - HINDSIGHT_API_KEY, HINDSIGHT_BASE_URL, HINDSIGHT_BANK_ID must be set in .env

The bank is created if it doesn't exist yet.
All records are retained with backdated timestamps so Hindsight
can reason about time ("3 months ago").

Timing note: retain() does processing (fact extraction, consolidation).
Run this script at least 5–10 minutes before the demo so memories are queryable.
"""
from __future__ import annotations
import asyncio
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def get_client():
    from hindsight_client import Hindsight  # type: ignore
    return Hindsight(
        base_url=settings.HINDSIGHT_BASE_URL,
        api_key=settings.HINDSIGHT_API_KEY,
        timeout=60.0,
    )


def parse_iso(ts: str) -> datetime:
    """
    Parse an ISO-8601 timestamp string to a UTC datetime.
    Works on Python 3.10 which doesn't support the Z suffix in fromisoformat().
    """
    ts = ts.strip().replace("Z", "+00:00")
    return datetime.fromisoformat(ts).astimezone(timezone.utc)


async def ensure_bank(hs) -> None:
    """Create the bank if it doesn't exist."""
    try:
        await hs.acreate_bank(
            bank_id=settings.HINDSIGHT_BANK_ID,
            name="Déjà Vu — Engineering Incident Memory",
            mission=(
                "You are the institutional memory of the Kirana Cart engineering org. "
                "Track production incidents, their root causes, fixes that worked and "
                "fixes that failed, deploys/changes and their consequences, and on-call "
                "engineers' preferences. Be skeptical — do not recommend fixes just "
                "because they are in memory; verify they match the current context."
            ),
            disposition={"skepticism": 4, "literalism": 3, "empathy": 2},
        )
        print(f"  ✓ Created bank: {settings.HINDSIGHT_BANK_ID}")
    except Exception as e:
        if "already exists" in str(e).lower() or "409" in str(e):
            print(f"  ℹ Bank already exists: {settings.HINDSIGHT_BANK_ID}")
        else:
            # Fall back to sync create_bank if async version not available
            try:
                hs.create_bank(
                    bank_id=settings.HINDSIGHT_BANK_ID,
                    name="Déjà Vu — Engineering Incident Memory",
                    mission=(
                        "You are the institutional memory of the Kirana Cart engineering org. "
                        "Track production incidents, their root causes, fixes that worked and "
                        "fixes that failed, deploys/changes and their consequences, and on-call "
                        "engineers' preferences."
                    ),
                )
                print(f"  ✓ Created bank (sync): {settings.HINDSIGHT_BANK_ID}")
            except Exception as e2:
                if "already exists" in str(e2).lower() or "409" in str(e2):
                    print(f"  ℹ Bank already exists: {settings.HINDSIGHT_BANK_ID}")
                else:
                    raise


def incident_to_text(inc: dict) -> str:
    """Convert an incident record to a natural-language paragraph for Hindsight."""
    parts = [
        f"{inc['id']} on {inc['started_at'][:10]}, {inc['service']}, {inc['severity']}.",
        f"Detected by: {inc['detected_by']}.",
        f"Symptoms: {inc['symptoms']}",
        f"Error signature: {inc.get('error_signature', '')}",
    ]
    if inc.get("root_cause"):
        parts.append(f"Root cause: {inc['root_cause']}")
    if inc.get("related_deploy"):
        parts.append(f"Related deploy: {inc['related_deploy']}")

    for fix in inc.get("fixes_tried", []):
        outcome = "worked" if fix["worked"] else "did NOT work"
        parts.append(f"Fix tried: '{fix['action']}' — {outcome}.")

    if inc.get("resolution"):
        parts.append(f"Resolution: {inc['resolution']}")
    if inc.get("ttr_minutes"):
        parts.append(f"TTR: {inc['ttr_minutes']} minutes.")
    if inc.get("responders"):
        parts.append(f"Responders: {', '.join(inc['responders'])}.")

    return " ".join(parts)


def deploy_to_text(dep: dict) -> str:
    """Convert a deploy record to a natural-language paragraph."""
    parts = [
        f"Deploy {dep['id']} to {dep['service']} on {dep['timestamp'][:10]}",
        f"by {dep['author']}: {dep['change_summary']}",
    ]
    if dep.get("diff_snippet"):
        parts.append(f"Diff: {dep['diff_snippet']}")
    if dep.get("caused_incident"):
        parts.append(f"This deploy caused {dep['caused_incident']}.")
    return " ".join(parts)


async def retain_one(hs, content: str, context: str, when: datetime, doc_id: str, meta: dict) -> None:
    """Retain one memory — always called within a single asyncio.run() context."""
    try:
        await hs.aretain(
            bank_id=settings.HINDSIGHT_BANK_ID,
            content=content,
            context=context,
            timestamp=when,
            document_id=doc_id,
            metadata=meta,
        )
        print(f"    ✓ retained {doc_id}")
    except Exception as e:
        print(f"    ✗ failed {doc_id}: {e}")
    await asyncio.sleep(0.3)  # gentle rate-limit buffer


async def seed_incidents(hs, incidents: list[dict]) -> None:
    print(f"\nSeeding {len(incidents)} incidents…")
    for inc in incidents:
        try:
            when = parse_iso(inc["started_at"])
        except Exception as e:
            print(f"    ⚠ skipped {inc['id']} — bad timestamp '{inc['started_at']}': {e}")
            continue
        text = incident_to_text(inc)
        await retain_one(
            hs, text,
            context="incident postmortem",
            when=when,
            doc_id=f"{inc['id']}-postmortem",
            meta={
                "service": inc["service"],
                "severity": inc["severity"],
                "kind": "incident",
                "incident_id": inc["id"],
            },
        )


async def seed_deploys(hs, deploys: list[dict]) -> None:
    print(f"\nSeeding {len(deploys)} deploys…")
    for dep in deploys:
        try:
            when = parse_iso(dep["timestamp"])
        except Exception as e:
            print(f"    ⚠ skipped {dep['id']} — bad timestamp '{dep['timestamp']}': {e}")
            continue
        text = deploy_to_text(dep)
        await retain_one(
            hs, text,
            context="deploy event",
            when=when,
            doc_id=f"{dep['id']}-deploy",
            meta={
                "service": dep["service"],
                "kind": "deploy",
                "deploy_id": dep["id"],
                "caused_incident": dep.get("caused_incident") or "",
            },
        )


async def seed_preferences(hs) -> None:
    print("\nSeeding engineer preferences…")
    prefs = [
        {
            "text": "Engineer Ravi prefers briefings of at most 2 sentences: fix first, root cause second.",
            "doc_id": "pref-ravi-1",
            "engineer": "Ravi",
        },
        {
            "text": "Engineer Matrix prefers very concise answers. No stack traces.",
            "doc_id": "pref-matrix-1",
            "engineer": "Matrix",
        },
    ]
    now = datetime.now(timezone.utc)
    for p in prefs:
        await retain_one(
            hs, p["text"],
            context="engineer preference",
            when=now,
            doc_id=p["doc_id"],
            meta={"kind": "preference", "engineer": p["engineer"]},
        )


async def run_all(incidents: list[dict], deploys: list[dict]) -> None:
    """
    Run the entire seeding pipeline inside a single asyncio event loop
    so the aiohttp client session stays open throughout.
    """
    hs = get_client()

    print("\n1. Ensuring bank exists…")
    await ensure_bank(hs)

    print(f"\nLoaded {len(incidents)} incidents, {len(deploys)} deploys")

    await seed_incidents(hs, incidents)
    await seed_deploys(hs, deploys)
    await seed_preferences(hs)


def main():
    print("=== Déjà Vu — Hindsight Memory Seeder ===")
    print(f"Bank: {settings.HINDSIGHT_BANK_ID}")
    print(f"URL:  {settings.HINDSIGHT_BASE_URL or '(not set)'}")

    if not settings.HINDSIGHT_API_KEY or not settings.HINDSIGHT_BASE_URL:
        print("\nERROR: HINDSIGHT_API_KEY or HINDSIGHT_BASE_URL not set in .env")
        sys.exit(1)

    incidents_path = DATA_DIR / "incidents.json"
    deploys_path = DATA_DIR / "deploys.json"

    if not incidents_path.exists():
        print("ERROR: data/incidents.json not found. Run generate_data.py first.")
        sys.exit(1)

    with open(incidents_path) as f:
        incidents = json.load(f)
    with open(deploys_path) as f:
        deploys = json.load(f)

    # Run everything inside ONE event loop — fixes "Event loop is closed" errors
    asyncio.run(run_all(incidents, deploys))

    print("\n=== Seeding complete ===")
    print("Wait 1–2 minutes for Hindsight to process memories before testing.")
    print("Then run: python scripts/smoke_test.py")


if __name__ == "__main__":
    main()
