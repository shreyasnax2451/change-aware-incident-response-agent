#!/usr/bin/env python3
"""
generate_data.py — Generate synthetic Kirana Cart incidents and deploys.

Usage:
    python scripts/generate_data.py

Writes:
    data/incidents.json
    data/deploys.json
    data/demo_alerts.json

This uses the Groq LLM to generate realistic data, then hand-codes the
hero patterns (Pattern A: payments-service DB pool) for demo reliability.
"""
from __future__ import annotations
import json
import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import settings
from groq import Groq

OUT_DIR = Path(__file__).parent.parent.parent / "data"
OUT_DIR.mkdir(parents=True, exist_ok=True)

client = Groq(api_key=settings.GROQ_API_KEY)


def llm(prompt: str) -> dict | list:
    resp = client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        response_format={"type": "json_object"},
        temperature=0.7,
    )
    return json.loads(resp.choices[0].message.content)


# ─── Hero pattern (hand-coded for demo reliability) ───────────────────────────
HERO_DEPLOYS = [
    {
        "id": "DEP-441",
        "service": "payments-service",
        "timestamp": "2026-04-19T17:45:00+05:30",
        "author": "Ravi",
        "change_summary": "Reduce DB connection pool max from 80 to 30 to reduce RDS cost",
        "diff_snippet": "- maximumPoolSize: 80\n+ maximumPoolSize: 30",
        "caused_incident": "INC-0177",
    },
    {
        "id": "DEP-634",
        "service": "payments-service",
        "timestamp": "2026-06-02T14:20:00+05:30",
        "author": "Sneha",
        "change_summary": "Reduce DB pool from 60 to 20 — cost optimisation initiative",
        "diff_snippet": "- maximumPoolSize: 60\n+ maximumPoolSize: 20",
        "caused_incident": "INC-0288",
    },
    {
        "id": "DEP-812",
        "service": "payments-service",
        "timestamp": "2026-08-14T18:55:00+05:30",
        "author": "Ravi",
        "change_summary": "Reduce DB pool max from 50 to 20 to save RDS cost",
        "diff_snippet": "- maximumPoolSize: 50\n+ maximumPoolSize: 20",
        "caused_incident": "INC-0412",
    },
    # The 4th occurrence — the live demo deploy
    {
        "id": "DEP-901",
        "service": "payments-service",
        "timestamp": "2026-09-28T01:00:00+05:30",
        "author": "Matrix",
        "change_summary": "Reduce DB pool from 50 to 25 to cut RDS cost by 30%",
        "diff_snippet": "- maximumPoolSize: 50\n+ maximumPoolSize: 25",
        "caused_incident": "INC-0503",
    },
]

HERO_INCIDENTS = [
    {
        "id": "INC-0177",
        "title": "payments-service DB connection pool exhaustion",
        "service": "payments-service",
        "severity": "SEV2",
        "started_at": "2026-04-19T19:10:00+05:30",
        "detected_by": "PagerDuty: p99 latency > 3s",
        "symptoms": "Checkout returning 503s, HikariPool-1 connection timeouts",
        "error_signature": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
        "log_excerpt": "2026-04-19 19:11:22 ERROR c.z.h.p.HikariPool - HikariPool-1 - Connection is not available, request timed out after 30000ms.\njava.sql.SQLTransientConnectionException: payments-ds - Connection is not available",
        "root_cause": "DEP-441 reduced DB connection pool from 80 to 30; peak evening traffic exhausted available connections",
        "related_deploy": "DEP-441",
        "fixes_tried": [
            {"action": "Restarted payments pods (2 replicas)", "worked": False},
            {"action": "Increased DB query timeout", "worked": False},
            {"action": "Rolled back DEP-441", "worked": True},
        ],
        "resolution": "Rolled back DEP-441 to restore pool size to 80. Recovery took 70 minutes because root cause was not immediately identified.",
        "ttr_minutes": 70,
        "responders": ["Ravi", "Priya"],
    },
    {
        "id": "INC-0288",
        "title": "payments-service 503s during evening peak — HikariCP timeout",
        "service": "payments-service",
        "severity": "SEV2",
        "started_at": "2026-06-02T19:55:00+05:30",
        "detected_by": "PagerDuty: error rate > 20%",
        "symptoms": "checkout returning HTTP 503, DB connection wait times spiking",
        "error_signature": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
        "log_excerpt": "2026-06-02 19:56:10 ERROR c.z.h.p.HikariPool - HikariPool-1 - Connection is not available, request timed out after 30000ms.",
        "root_cause": "DEP-634 reduced DB pool from 60 to 20; same pattern as INC-0177",
        "related_deploy": "DEP-634",
        "fixes_tried": [
            {"action": "Restarted pods", "worked": False},
            {"action": "Rolled back DEP-634", "worked": True},
        ],
        "resolution": "Rolled back DEP-634. Recovery in 52 minutes.",
        "ttr_minutes": 52,
        "responders": ["Sneha", "Ravi"],
    },
    {
        "id": "INC-0412",
        "title": "Checkout 503s during evening peak — HikariPool exhaustion",
        "service": "payments-service",
        "severity": "SEV1",
        "started_at": "2026-08-14T19:42:00+05:30",
        "detected_by": "PagerDuty: p99 latency > 3s",
        "symptoms": "All checkout requests returning 503. HikariPool-1 connection timeouts in logs.",
        "error_signature": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
        "log_excerpt": "2026-08-14 19:43:01 ERROR c.z.h.p.HikariPool - HikariPool-1 - Connection is not available, request timed out after 30000ms.\njava.sql.SQLTransientConnectionException: payments-ds - Connection is not available, request timed out after 30000ms.",
        "root_cause": "DEP-812 reduced HikariCP maximumPoolSize from 50 to 20; peak load exceeded pool capacity",
        "related_deploy": "DEP-812",
        "fixes_tried": [
            {"action": "Restarted payments pods", "worked": False},
            {"action": "Rolled back DEP-812", "worked": True},
        ],
        "resolution": "Rolled back DEP-812. Pool restored to 50 connections. Service recovered in 11 minutes after rollback.",
        "ttr_minutes": 38,
        "responders": ["Ravi", "Sneha"],
    },
    {
        "id": "INC-0503",
        "title": "payments-service down — 4th DB pool exhaustion",
        "service": "payments-service",
        "severity": "SEV1",
        "started_at": "2026-09-28T01:47:00+05:30",
        "detected_by": "PagerDuty: p99 latency > 3s | Error rate 34% on /checkout",
        "symptoms": "HikariPool-1 connection timeouts, checkout returning 503, DB active connections maxed",
        "error_signature": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
        "log_excerpt": "2026-09-28 01:48:12 ERROR c.z.h.p.HikariPool - HikariPool-1 - Connection is not available, request timed out after 30000ms.\njava.sql.SQLTransientConnectionException: payments-ds - Connection is not available",
        "root_cause": "DEP-901 reduced pool from 50 to 25; fourth occurrence of same pattern",
        "related_deploy": "DEP-901",
        "fixes_tried": [],
        "resolution": "LIVE INCIDENT — demo scenario",
        "ttr_minutes": None,
        "responders": ["Matrix"],
    },
]

# ─── Pattern B: Redis OOM on checkout-api ─────────────────────────────────────
PATTERN_B_INCIDENT = {
    "id": "INC-0350",
    "title": "checkout-api Redis OOM during Diwali Sale",
    "service": "checkout-api",
    "severity": "SEV1",
    "started_at": "2026-10-24T20:15:00+05:30",
    "detected_by": "PagerDuty: Redis OOM errors",
    "symptoms": "Add-to-cart failing, NOEVICTION errors from Redis",
    "error_signature": "OOM command not allowed when used memory > 'maxmemory'",
    "log_excerpt": "redis.exceptions.ResponseError: OOM command not allowed when used memory > 'maxmemory'. Used: 3.98gb Max: 4.00gb",
    "root_cause": "Cart keys had no TTL set; Diwali Sale traffic caused Redis memory to exceed maxmemory limit with allkeys-noeviction policy",
    "related_deploy": "DEP-789",
    "fixes_tried": [
        {"action": "Restarted Redis pod", "worked": False},
        {"action": "Raised maxmemory to 6GB and switched to allkeys-lru", "worked": True},
        {"action": "Set TTL of 86400s on all cart: keys", "worked": True},
    ],
    "resolution": "Raised maxmemory to 6GB, switched eviction policy to allkeys-lru, added TTL 86400s to cart keys. Recovered in 25 minutes.",
    "ttr_minutes": 25,
    "responders": ["Priya", "Matrix"],
}

# ─── Pattern C: auth-service JWT clock-skew (fixed) ──────────────────────────
PATTERN_C_INCIDENT = {
    "id": "INC-0200",
    "title": "auth-service JWT validation failures",
    "service": "auth-service",
    "severity": "SEV2",
    "started_at": "2026-05-03T11:22:00+05:30",
    "detected_by": "Datadog: 401 error rate spike",
    "symptoms": "Users unable to login, JWT token validation rejecting valid tokens",
    "error_signature": "io.jsonwebtoken.ExpiredJwtException: JWT expired at ...",
    "log_excerpt": "ERROR c.k.auth.JwtFilter - JWT expired at 2026-05-03T11:20:00Z. Current time: 2026-05-03T11:19:45Z.",
    "root_cause": "Clock skew > 30s between auth-service pods and issuer; NTP misconfiguration in DEP-555",
    "related_deploy": "DEP-555",
    "fixes_tried": [
        {"action": "Restarted auth pods", "worked": False},
        {"action": "Fixed NTP config and redeployed (DEP-560)", "worked": True},
    ],
    "resolution": "Fixed NTP configuration in DEP-560. Bug permanently resolved in May 2026. If clock-skew errors recur on auth-service, suspect a regression of this fix.",
    "ttr_minutes": 45,
    "responders": ["Kavya", "Ravi"],
}


def generate_noise_incidents() -> tuple[list, list]:
    """Generate ~12 unrelated incidents via LLM for realistic recall discrimination."""
    prompt = """Generate exactly 12 realistic production incidents for "Kirana Cart", 
a fictional Indian quick-commerce app. Services: checkout-api, auth-service, search-service, notification-worker.

These should be DIFFERENT failure modes from DB connection pool or Redis OOM (those are already covered).
Include: Kafka consumer lag, slow Elasticsearch queries, notification-worker OOM, 
auth-service rate limit, search indexing failures, etc.

Return JSON: {"incidents": [...], "deploys": [...]}

Each incident must have these exact fields:
id (INC-XXXX), title, service, severity (SEV1/SEV2/SEV3), started_at (ISO8601 between 2026-03-01 and 2026-09-20), 
detected_by, symptoms, error_signature, log_excerpt, root_cause, related_deploy (DEP-XXXX or null),
fixes_tried ([{action, worked}]), resolution, ttr_minutes, responders ([names])

Each deploy must have:
id (DEP-XXXX), service, timestamp (ISO8601), author, change_summary, diff_snippet, caused_incident (or null)

Make IDs realistic and non-overlapping with INC-0177,0200,0288,0350,0412,0503 and DEP-441,555,560,634,789,812,901."""

    print("  Generating noise incidents via LLM…")
    try:
        data = llm(prompt)
        return data.get("incidents", []), data.get("deploys", [])
    except Exception as e:
        print(f"  Warning: LLM generation failed ({e}), using empty noise set")
        return [], []


def main():
    print("Generating Kirana Cart synthetic data…")

    noise_incidents, noise_deploys = generate_noise_incidents()

    all_incidents = HERO_INCIDENTS + [PATTERN_B_INCIDENT, PATTERN_C_INCIDENT] + noise_incidents
    all_deploys = HERO_DEPLOYS + noise_deploys

    # Also include the auth-service fix deploy
    all_deploys.extend([
        {
            "id": "DEP-555",
            "service": "auth-service",
            "timestamp": "2026-05-03T10:50:00+05:30",
            "author": "Kavya",
            "change_summary": "Update NTP config in auth-service (misconfigured clock sync)",
            "diff_snippet": "- ntpServer: pool.ntp.org\n+ ntpServer: 169.254.169.123  # AWS Time Sync",
            "caused_incident": "INC-0200",
        },
        {
            "id": "DEP-560",
            "service": "auth-service",
            "timestamp": "2026-05-03T12:45:00+05:30",
            "author": "Kavya",
            "change_summary": "Fix NTP configuration — resolves JWT clock-skew bug permanently",
            "diff_snippet": "- ntpServer: pool.ntp.org\n+ ntpServer: 169.254.169.123\n+ maxClockSkew: 60s",
            "caused_incident": None,
        },
        {
            "id": "DEP-789",
            "service": "checkout-api",
            "timestamp": "2026-10-24T18:00:00+05:30",
            "author": "Priya",
            "change_summary": "Add Diwali Sale feature flags — no cart key TTL change",
            "diff_snippet": "+ DIWALI_SALE_ENABLED=true\n+ SALE_DISCOUNT_PERCENT=30",
            "caused_incident": "INC-0350",
        },
    ])

    # Write files
    incidents_path = OUT_DIR / "incidents.json"
    deploys_path = OUT_DIR / "deploys.json"
    demo_path = OUT_DIR / "demo_alerts.json"

    with open(incidents_path, "w") as f:
        json.dump(all_incidents, f, indent=2)
    print(f"  ✓ Wrote {len(all_incidents)} incidents → {incidents_path}")

    with open(deploys_path, "w") as f:
        json.dump(all_deploys, f, indent=2)
    print(f"  ✓ Wrote {len(all_deploys)} deploys → {deploys_path}")

    # Write the exact demo inputs for rehearsal
    demo_alerts = {
        "demo_alert": (
            "CRITICAL: payments-service — HikariPool-1 connection timeouts\n"
            "PagerDuty: p99 latency > 3s | Error rate 34% on /checkout\n"
            "Detected: 2026-09-28T01:47:00+05:30\n"
            "Logs: HikariPool-1 - Connection is not available, request timed out after 30000ms\n"
            "      java.sql.SQLTransientConnectionException: payments-ds - Connection is not available\n"
            "Recent deploy: DEP-901 by Matrix (47 min ago) — 'Reduce DB pool max from 50 to 25 to cut RDS cost'"
        ),
        "demo_pr": {
            "service": "payments-service",
            "change_description": (
                "Reduce DB connection pool from 50 to 25 to cut RDS cost by ~30%. "
                "Change: maximumPoolSize: 50 → 25 in payments-service HikariCP config."
            ),
            "diff": (
                "--- a/config/payments-service.yaml\n"
                "+++ b/config/payments-service.yaml\n"
                "@@ -14,7 +14,7 @@ datasource:\n"
                "   hikari:\n"
                "-    maximumPoolSize: 50\n"
                "+    maximumPoolSize: 25\n"
                "     minimumIdle: 5\n"
                "     connectionTimeout: 30000"
            ),
        },
    }
    with open(demo_path, "w") as f:
        json.dump(demo_alerts, f, indent=2)
    print(f"  ✓ Wrote demo inputs → {demo_path}")
    print("\nDone! Run seed_memory.py next.")


if __name__ == "__main__":
    main()
