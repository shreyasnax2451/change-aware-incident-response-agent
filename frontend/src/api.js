// api.js — All API calls with mock fallbacks for frontend-only development

const BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// ─── Mock Data ──────────────────────────────────────────────────────────────

const MOCK_TRIAGE = {
  matched: true,
  root_cause:
    "DB connection pool exhaustion on payments-service. Deploy DEP-812 reduced the HikariCP pool size from 50 → 20 to cut RDS cost, causing connection timeouts under peak load.",
  recommended_fix: [
    "Roll back DEP-901 immediately (same pool-size reduction pattern as DEP-812).",
    "Increase maximumPoolSize back to 50 in payments-service config.",
    "Watch HikariPool-1 connection-wait metrics after rollback.",
  ],
  avoid: [
    "Do NOT restart pods — pod restarts did not help in INC-0412 or INC-0288.",
    "Do NOT increase connection timeout — masks the real cause.",
  ],
  similar_incidents: [
    {
      id: "INC-0412",
      when: "2026-08-14",
      why_similar: "Identical HikariPool-1 timeout error; caused by DEP-812 (pool 50→20). TTR 38 min.",
    },
    {
      id: "INC-0288",
      when: "2026-06-02",
      why_similar: "Same service, same error signature. Pool size reduced in DEP-634. TTR 52 min.",
    },
    {
      id: "INC-0177",
      when: "2026-04-19",
      why_similar: "First occurrence; payments-service pool change DEP-441. TTR 70 min.",
    },
  ],
  suspect_change: "DEP-901 — reduced DB pool from 50 to 25 (deployed 47 min before alert)",
  confidence: "high",
  spoken_summary:
    "This matches three previous incidents. The DB pool size was cut again — do not restart pods, roll back deploy 901 immediately.",
  memories_used: [
    {
      text: "INC-0412 on 2026-08-14: payments-service, SEV1. HikariPool-1 connection timeouts. Root cause: DEP-812 reduced pool from 50→20. Pod restart failed. Rollback fixed in 11 min.",
      type: "incident postmortem",
      source: "INC-0412",
      when: "2026-08-14",
    },
    {
      text: "INC-0288 on 2026-06-02: payments-service. Same pool exhaustion pattern. DEP-634 to blame.",
      type: "incident postmortem",
      source: "INC-0288",
      when: "2026-06-02",
    },
    {
      text: "Engineer Ravi prefers concise briefings — fix first, root cause second.",
      type: "engineer preference",
      source: null,
      when: "2026-07-01",
    },
  ],
};

const MOCK_TRIAGE_NO_MEMORY = {
  matched: false,
  root_cause:
    "Database connection failures suggest resource exhaustion or misconfiguration. Could be pool limits, max connections at the DB level, or a networking issue.",
  recommended_fix: [
    "Check DB connection pool configuration and current connection count.",
    "Restart affected pods to reset connection state.",
    "Review recent deploys for configuration changes.",
    "Scale the service if resource pressure is the cause.",
  ],
  avoid: [],
  similar_incidents: [],
  suspect_change: null,
  confidence: "low",
  spoken_summary:
    "No memory available. Likely a database connection issue — check pool config and recent deploys.",
  memories_used: [],
};

const MOCK_RISK = {
  risk_level: "high",
  evidence: [
    {
      id: "INC-0412",
      when: "2026-08-14",
      what_happened:
        "DEP-812 reduced payments-service DB pool from 50→20. Caused SEV1 (HikariPool-1 timeouts). 38-minute TTR.",
    },
    {
      id: "INC-0288",
      when: "2026-06-02",
      what_happened:
        "DEP-634 reduced pool size. Same timeout pattern. 52-minute TTR.",
    },
    {
      id: "INC-0177",
      when: "2026-04-19",
      what_happened:
        "DEP-441 first pool-size reduction. 70-minute TTR before team understood root cause.",
    },
  ],
  recommendation: [
    "⛔ Do not merge without a canary rollout — this change has triggered SEV1 three times before.",
    "Set a connection-pool floor of 40 for payments-service.",
    "If cost savings are needed, reduce the application's query frequency or upgrade the RDS instance tier instead.",
    "If you proceed, alert the on-call team in advance and have a rollback plan ready.",
  ],
  watch_metrics: [
    "HikariPool-1 connection-wait ms",
    "DB active connections",
    "payments-service p99 latency",
    "5xx error rate on /checkout",
  ],
  spoken_summary:
    "High risk. This exact change broke production three times in the last six months. Use a canary and watch DB connection metrics closely.",
  memories_used: [
    {
      text: "DEP-812 to payments-service reduced DB pool 50→20 and caused INC-0412 (SEV1). Rollback was the only fix.",
      type: "deploy event",
      source: "DEP-812",
      when: "2026-08-14",
    },
  ],
};

const MOCK_RISK_NO_MEMORY = {
  risk_level: "medium",
  evidence: [],
  recommendation: [
    "DB connection pool changes can affect peak-load capacity.",
    "Monitor DB connection counts and latency after deploy.",
    "Have a rollback plan ready.",
  ],
  watch_metrics: ["DB connections", "Service latency", "Error rate"],
  spoken_summary: "Medium risk. Monitor connection pool metrics after deploy.",
  memories_used: [],
};

const MOCK_PLAYBOOK = {
  "payments-service": {
    current: `# payments-service — Known Failure Modes & Proven Fixes
*Version 3 · Updated after INC-0503 · 2026-09-12*

## DB Connection Pool Exhaustion
**Signature:** HikariPool-1 - Connection is not available, request timed out after 30000ms
**Root cause:** DB pool max-size reduced below safe threshold (~40 for current traffic)
**Fix:**
  1. Roll back the deploy that changed maximumPoolSize
  2. Do NOT restart pods — not effective
  3. Pool floor: 40 connections minimum
**Evidence:** INC-0412, INC-0288, INC-0177, INC-0503 — all same pattern

## Redis OOM / Eviction
**Signature:** OOM command not allowed / NOEVICTION policy triggered
**Fix:** Raise maxmemory, switch to allkeys-lru, set TTL on cart keys (86400s)

## Circuit breaker open (payments → fraud-service)
**Signature:** CircuitBreakerOpenException after fraud-service latency spike
**Fix:** Check fraud-service health first; circuit resets automatically in 30s`,
    previous: `# payments-service — Known Failure Modes & Proven Fixes
*Version 2 · Updated after INC-0412 · 2026-08-15*

## DB Connection Pool Exhaustion
**Signature:** HikariPool-1 - Connection is not available, request timed out after 30000ms
**Root cause:** DB pool max-size reduced below safe threshold
**Fix:**
  1. Roll back the deploy that changed maximumPoolSize
  2. Pod restarts may help (UNVERIFIED)
**Evidence:** INC-0412, INC-0288

## Redis OOM / Eviction
**Signature:** OOM command not allowed
**Fix:** Raise maxmemory, switch to allkeys-lru`,
    updated_at: "2026-09-12T10:23:00+05:30",
  },
};

const MOCK_MEMORIES = [
  {
    id: "m-001",
    text: "INC-0412 on 2026-08-14: payments-service, SEV1. HikariPool-1 connection timeouts during evening peak. Root cause: DEP-812 reduced DB pool from 50→20. Pod restart did NOT help. Rollback of DEP-812 fixed it in 11 minutes.",
    type: "incident postmortem",
    service: "payments-service",
    severity: "SEV1",
    when: "2026-08-14",
  },
  {
    id: "m-002",
    text: "DEP-812 to payments-service on 2026-08-14 by Ravi: reduced DB connection pool size from 50 to 20 to cut RDS cost.",
    type: "deploy event",
    service: "payments-service",
    when: "2026-08-14",
  },
  {
    id: "m-003",
    text: "INC-0288 on 2026-06-02: payments-service, SEV2. Same pool exhaustion pattern as INC-0412. DEP-634 to blame. TTR 52 min.",
    type: "incident postmortem",
    service: "payments-service",
    severity: "SEV2",
    when: "2026-06-02",
  },
  {
    id: "m-004",
    text: "INC-0177 on 2026-04-19: payments-service, SEV2. First DB pool exhaustion incident. Team did not immediately identify pool size as root cause. TTR 70 min.",
    type: "incident postmortem",
    service: "payments-service",
    severity: "SEV2",
    when: "2026-04-19",
  },
  {
    id: "m-005",
    text: "auth-service JWT clock-skew bug permanently fixed in May 2026 (DEP-555). If clock-skew errors recur on auth-service, suspect a regression of this fix.",
    type: "incident postmortem",
    service: "auth-service",
    when: "2026-05-08",
  },
  {
    id: "m-006",
    text: "checkout-api Redis OOM during Diwali Sale 2026-10-28. Fix: raise maxmemory to 4GB, switch to allkeys-lru policy, set TTL 86400 on cart keys.",
    type: "incident postmortem",
    service: "checkout-api",
    severity: "SEV1",
    when: "2026-10-28",
  },
  {
    id: "m-007",
    text: "Engineer Ravi prefers briefings of at most 2 sentences: fix first, root cause second.",
    type: "engineer preference",
    service: null,
    when: "2026-07-01",
  },
  {
    id: "m-008",
    text: "INC-0503 on 2026-09-11: payments-service, SEV1. Fourth occurrence of DB pool exhaustion. Resolved by rollback of DEP-901 in 22 min.",
    type: "incident postmortem",
    service: "payments-service",
    severity: "SEV1",
    when: "2026-09-11",
  },
];

// ─── API helpers ─────────────────────────────────────────────────────────────

async function apiFetch(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  if (!res.ok) throw new Error(`API ${path} returned ${res.status}`);
  return res.json();
}

const delay = (ms) => new Promise((r) => setTimeout(r, ms));

// ─── Public API ──────────────────────────────────────────────────────────────

export async function triage({ alert_text, service, use_memory, engineer }) {
  try {
    return await apiFetch('/api/triage', {
      method: 'POST',
      body: JSON.stringify({ alert_text, service, use_memory, engineer }),
    });
  } catch {
    await delay(1800);
    return use_memory ? MOCK_TRIAGE : MOCK_TRIAGE_NO_MEMORY;
  }
}

export async function resolve({ incident_id, alert_text, service, worked, failed, notes, engineer }) {
  try {
    return await apiFetch('/api/resolve', {
      method: 'POST',
      body: JSON.stringify({ incident_id, alert_text, service, worked, failed, notes, engineer }),
    });
  } catch {
    await delay(900);
    return { ok: true, retained_ids: ['ret-' + Date.now()] };
  }
}

export async function riskCheck({ service, change_description, diff, use_memory }) {
  try {
    return await apiFetch('/api/risk-check', {
      method: 'POST',
      body: JSON.stringify({ service, change_description, diff, use_memory }),
    });
  } catch {
    await delay(1600);
    return use_memory ? MOCK_RISK : MOCK_RISK_NO_MEMORY;
  }
}

export async function getPlaybook(service) {
  try {
    return await apiFetch(`/api/playbook/${service}`);
  } catch {
    await delay(700);
    return MOCK_PLAYBOOK[service] || {
      current: `# ${service}\n\nNo playbook entries yet. Resolve incidents and they will appear here.`,
      previous: null,
      updated_at: new Date().toISOString(),
    };
  }
}

export async function refreshPlaybook(service) {
  try {
    return await apiFetch(`/api/playbook/${service}/refresh`, { method: 'POST' });
  } catch {
    await delay(1200);
    return getPlaybook(service);
  }
}

export async function getMemories(query = '') {
  try {
    const data = await apiFetch(`/api/memories?q=${encodeURIComponent(query)}`);
    return data.results;
  } catch {
    await delay(500);
    const q = query.toLowerCase();
    return q
      ? MOCK_MEMORIES.filter(
          (m) =>
            m.text.toLowerCase().includes(q) ||
            (m.service && m.service.toLowerCase().includes(q))
        )
      : MOCK_MEMORIES;
  }
}

export async function transcribeAudio(audioBlob) {
  try {
    const form = new FormData();
    form.append('audio', audioBlob, 'recording.webm');
    const res = await fetch(`${BASE}/api/voice/transcribe`, { method: 'POST', body: form });
    if (!res.ok) throw new Error('STT failed');
    return res.json();
  } catch {
    await delay(1200);
    return {
      text: "Rollback of deploy 901 fixed it. Pod restarts did not help. Please keep briefings shorter next time.",
    };
  }
}

export async function speak(text) {
  try {
    const res = await fetch(`${BASE}/api/voice/speak`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text }),
    });
    if (!res.ok) throw new Error('TTS failed');
    const blob = await res.blob();
    return URL.createObjectURL(blob);
  } catch {
    // Browser TTS fallback
    return null;
  }
}

export async function healthCheck() {
  try {
    return await apiFetch('/api/health');
  } catch {
    return { hindsight: 'offline (mock mode)', groq: 'offline (mock mode)' };
  }
}

export async function getWeaknessReport(service) {
  try {
    return await apiFetch('/api/weakness', {
      method: 'POST',
      body: JSON.stringify({ service }),
    });
  } catch {
    await delay(1500);
    return {
      service,
      report_markdown: `# Structural Weakness Report: ${service}\n\n**Mock Data**: The backend is offline. But normally, this would analyze all past incidents and suggest architectural refactors.`
    };
  }
}
