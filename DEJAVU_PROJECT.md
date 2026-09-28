# OnCall AI — Change-Aware Incident Memory Agent

**HackwithHyderabad 3.0 · Hindsight (Vectorize) memory hackathon · 1-day build · 2-person team**

> An on-call assistant that remembers every past production incident, what caused it, what fixed it and what *didn't*, and uses that memory to resolve new incidents faster **and** to warn about risky changes *before* they ship. Voice-enabled for the 2 AM page.

---

## 0. TL;DR for the team

| | |
|---|---|
| **Theme** | Build an AI agent on **Hindsight** whose memory makes it visibly better over time |
| **Our angle** | Incident response that is **reactive + preventive** (most existing projects are reactive only) |
| **Headline feature** | Pre-deploy risk check: "the last 3 times someone changed this, production broke" |
| **Stack** | FastAPI · React (Vite) · Groq (LLM + Whisper STT + Orpheus TTS) · Hindsight Cloud |
| **Must ship** | Triage → Resolve (learn) → Risk check → Memory ON/OFF toggle → Voice |
| **Nice to have** | Living service playbooks (Hindsight mental models) with version history |

---

## 1. Problem statement (from organizers)

- Build an AI agent using **Hindsight** so it has persistent memory and learns from past interactions.
- Solve a **real business problem** ("would someone pay $50/month?"). No student projects.
- Make **memory the star**: show before/after, recall from weeks ago, learn preferences, improve over interactions.
- **LLM:** any. Groq recommended: `openai/gpt-oss-120b` or `qwen/qwen3-32b`. Handle function-calling errors.
- **Hindsight Cloud promo:** `MEMHACK99` ($50 credit, add in Billing after signup).

**Judging:** Innovation 30% · Use of Hindsight memory 25% · Technical implementation 20% · UX 15% · Real-world impact 10%

**Submission checklist**
- [ ] GitHub repo with clean, documented code
- [ ] Demo video
- [ ] Live demo to judges
- [ ] "How we use Hindsight memory" explanation (in README)
- [ ] **Each member:** article + social media post + video (per content guide)

---

## 2. Landscape and positioning

### 2.1 Existing Hindsight-hackathon incident agents (already on GitHub)
Several teams built "paste an incident, recall similar past incidents, store the fix". That is **table stakes** for us, not our pitch. Don't copy their structure or README.

### 2.2 HolmesGPT (the tool our teammate flagged)
**What it is:** open-source SRE agent, CNCF sandbox project, originally by Robusta with Microsoft contributions. CLI + server + Slack/Teams via Robusta.

**How it works:**
- **Agentic loop over live data.** The LLM decides which "toolsets" to call (Kubernetes, Prometheus, Grafana, Datadog, Loki, Elasticsearch, AWS/Azure/GCP, databases, GitHub, Confluence, etc.) and queries live observability data to find the root cause.
- **Alert integrations:** pulls alerts from AlertManager, PagerDuty, OpsGenie, Jira and writes findings back.
- **Runbooks:** you write instructions for known alerts; it follows them.
- **Operator mode:** runs 24/7, scheduled health checks, **deployment verification** (checks a new version is healthy *after* deploy), can open GitHub PRs with fixes.
- **Read-only by design**, respects RBAC. Any LLM provider.

**How OnCall AI differs (use this in the pitch):**

| | HolmesGPT | OnCall AI (ours) |
|---|---|---|
| Question it answers | "What is happening **right now**?" | "Have we seen this **before**, and what worked?" |
| Knowledge source | Live telemetry + static runbooks you write | Accumulated memory of incidents, deploys, fixes, failed fixes, preferences |
| Learning | Runbooks change only when humans edit them | Every resolution updates memory; playbooks rewrite themselves |
| Deploys | Verifies health **after** deploy | Predicts risk **before** merge from incident history |
| Failed fixes | Not a first-class concept | Remembered and actively warned against |

**One-liner:** *HolmesGPT is the detective at the scene; OnCall AI is the team's institutional memory.* They're complementary. A future version could feed OnCall AI's recall into a Holmes-style investigation.

**What we borrow from Holmes (cheaply):**
- Accept alerts in an **AlertManager-like JSON shape** so it looks real.
- A small **"toolset" abstraction** for evidence sources (our mock deploy log is one toolset). Keeps the architecture extensible without building integrations.
- **Read-only** stance: the agent recommends; humans act.
- Optional stretch: a tiny CLI (`python -m dejavu ask "..."`) mirroring Holmes' interactive mode.

**What we do NOT do:** integrate or run HolmesGPT itself. It needs a real cluster and observability stack; not a one-day job.

---

## 3. Features (build in this order)

### F1. Incident triage *(must, hours 1–3)*
Input: alert text / error log (typed, pasted or spoken).
Output: likely root cause, recommended fix, **what to avoid**, similar past incidents with reasons, confidence, citations to memories.

### F2. Learn from outcomes *(must, hours 3–5)*
"Resolve" form (or voice): what worked, what failed, notes. Retained to Hindsight. Next similar incident → agent ranks the proven fix first and warns against failed ones.

### F3. Pre-deploy risk check *(must, headline, hours 5–7)*
Input: PR title/description/diff snippet + service.
Output: risk level, evidence (past incidents linked to similar changes, with dates), recommendation (e.g. "canary first, watch DB connection count, rollback plan").

### F4. Memory ON/OFF toggle *(must, trivial)*
Same prompt with vs without recall. The single most important visual for the 25% memory score.

### F5. Voice *(must-lite, hours 7–8.5)*
Push-to-talk. Spoken briefing on triage; dictate resolutions; learns preferences ("keep it shorter").

### F6. Living service playbooks *(nice to have; cut first if behind)*
Hindsight **mental model** per service: "Known failure modes and proven fixes for `<service>`". Show current version + previous version side by side after a resolution.

---

## 4. Voice: what we use

**Pattern:** push-to-talk (hold button → record → release → send). Not always-listening. Reliable in a noisy hall.

| Layer | Primary | Fallback | Notes |
|---|---|---|---|
| Capture | Browser `MediaRecorder` (webm/opus) | — | No library needed |
| Speech-to-text | **Groq Whisper** `whisper-large-v3-turbo` | Browser Web Speech API | Same Groq key. Use the `prompt` param with service names/jargon ("payments-service, Redis, HikariCP, p99") to improve accuracy |
| Text-to-speech | **Groq Orpheus** `canopylabs/orpheus-v1-english` (voices e.g. `troy`, `hannah`) | Browser `speechSynthesis` | Orpheus is marked **Preview** on Groq: keep the browser fallback wired behind a flag |
| Orchestration | Our backend | — | No LiveKit/Pipecat/realtime APIs: overkill for 1 day |

**Rules**
- LLM returns a separate `spoken_summary` (≤3 sentences). Never read stack traces or diffs aloud.
- Always keep a typed input as fallback.
- Show a "Checking past incidents…" status during the ~2–4 s round trip.
- Record the voice segment of the demo video in a quiet room.

**Voice intents** (classified by LLM from transcript):
`triage` (describe a problem) · `resolve` ("rolling back 812 fixed it") · `preference` ("keep it shorter") · `question` ("what did we do last time after rollback?")

---

## 5. Architecture

```
┌────────────────────────── React (Vite) ───────────────────────────┐
│ Incident Console │ Change Review │ Playbooks │ Memory Timeline    │
│  mic (push-to-talk) · Memory ON/OFF toggle · citations panel      │
└───────────────┬───────────────────────────────────────────────────┘
                │ REST (JSON / multipart audio)
┌───────────────▼──────────────── FastAPI ──────────────────────────┐
│ routes/  triage · resolve · risk_check · playbook · voice · mem   │
│ services/                                                         │
│   memory.py   ── Hindsight client (retain / recall / reflect)     │
│   llm.py      ── Groq chat, strict JSON, retry + repair           │
│   voice.py    ── Groq Whisper STT, Orpheus TTS                    │
│   toolsets/   ── deploy_log.py (mock evidence source)             │
│ Deterministic orchestration: WE call recall, then ONE LLM call.   │
│ No LLM tool-calling (Groq function-calling can be flaky).         │
└───────┬───────────────────────────┬───────────────────────────────┘
        │                           │
  Hindsight Cloud               Groq API
  bank: dejavu-eng              gpt-oss-120b · whisper · orpheus
```

---

## 6. Repo structure

```
dejavu/
├── README.md                    # pitch, demo gif, "How we use Hindsight", setup
├── .env.example
├── backend/
│   ├── requirements.txt
│   ├── main.py                  # FastAPI app, CORS, routers
│   ├── config.py                # env loading
│   ├── schemas.py               # Pydantic request/response models
│   ├── prompts.py               # all LLM prompts in one place
│   ├── services/
│   │   ├── memory.py
│   │   ├── llm.py
│   │   ├── voice.py
│   │   └── toolsets/deploy_log.py
│   ├── routes/
│   │   ├── triage.py
│   │   ├── resolve.py
│   │   ├── risk.py
│   │   ├── playbook.py
│   │   └── voice.py
│   └── scripts/
│       ├── generate_data.py     # LLM-generated synthetic history -> data/*.json
│       ├── seed_memory.py       # create bank + retain everything (backdated)
│       └── smoke_test.py        # retain/recall/reflect sanity check
├── data/
│   ├── incidents.json
│   ├── deploys.json
│   └── demo_alerts.json         # the exact alerts/PRs used in the live demo
└── frontend/
    ├── package.json
    └── src/
        ├── App.jsx
        ├── api.js
        ├── components/
        │   ├── IncidentConsole.jsx
        │   ├── DiagnosisCard.jsx
        │   ├── MemoryEvidence.jsx
        │   ├── ChangeReview.jsx
        │   ├── PlaybookView.jsx
        │   ├── MemoryToggle.jsx
        │   └── PushToTalk.jsx
        └── styles.css
```

---

## 7. Setup

```bash
# backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install fastapi uvicorn[standard] python-dotenv pydantic groq hindsight-client python-multipart
cp ../.env.example ../.env   # fill keys
python scripts/smoke_test.py
uvicorn main:app --reload --port 8000

# frontend
cd frontend
npm create vite@latest . -- --template react
npm install
npm run dev
```

`.env.example`
```
GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=qwen/qwen3-32b
HINDSIGHT_BASE_URL=            # from Hindsight Cloud dashboard
HINDSIGHT_API_KEY=             # from Hindsight Cloud dashboard
HINDSIGHT_BANK_ID=dejavu-eng
TTS_PROVIDER=groq              # groq | browser
```

---

## 8. Hindsight memory design

### 8.1 One bank
```python
client.create_bank(
    bank_id="dejavu-eng",
    name="OnCall AI – Engineering Incident Memory",
    mission=("You are the institutional memory of an engineering org. Track production "
             "incidents, their root causes, fixes that worked and fixes that failed, "
             "deploys/changes and their consequences, and on-call engineers' preferences."),
    disposition={"skepticism": 4, "literalism": 3, "empathy": 2},  # skeptical: don't copy fixes blindly
)
```

### 8.2 What we retain

| Memory kind | `context` | When | Example content (natural language, Hindsight extracts facts) |
|---|---|---|---|
| Incident post-mortem | `incident postmortem` | seed + every resolve | "INC-0412 on 2026-08-14, payments-service, SEV1. Checkout returned 503s; logs showed HikariPool-1 connection timeouts. Root cause: deploy #812 reduced DB pool from 50 to 20. Restarting pods did NOT help. Rolling back #812 fixed it in 11 minutes." |
| Deploy / change | `deploy event` | seed + every risk check | "Deploy #812 to payments-service on 2026-08-14 by Ravi: reduced DB connection pool size from 50 to 20 to save RDS cost." |
| Resolution feedback | `incident resolution` | resolve (typed/voice) | "For INC-0503, pod restart did not help; rollback of deploy #845 resolved it." |
| Engineer preference | `engineer preference` | voice/typed preference | "On-call engineer Matrix prefers briefings of at most 2 sentences, fix first." |

Always pass `timestamp` (backdated for seed data), `document_id` (incident/deploy id), `metadata` (`{"service": ..., "kind": ..., "severity": ...}`).
Tags per service/kind (`service:payments`, `kind:deploy`) if supported by the client version: **verify in docs** (integrations show retain tags + recall tag filters).

### 8.3 How each feature uses memory

| Feature | Hindsight op |
|---|---|
| Triage | `recall(query=alert_text, budget="mid", include_chunks=True)` + `recall(query="preferences of engineer X")` |
| Resolve | `retain(...)` resolution + updated post-mortem |
| Risk check | `recall(query=change_description)` for evidence + `reflect(query="What happened after past changes like: ...?")` for synthesis |
| Playbooks | Mental models (see Mental Models API docs), fallback: `reflect(query="Known failure modes and proven fixes for <service>")` and store versions ourselves |
| Memory OFF | Skip recall entirely, same LLM prompt |

### 8.4 `services/memory.py` (sketch)
```python
from hindsight_client import Hindsight
from config import settings

hs = Hindsight(base_url=settings.HINDSIGHT_BASE_URL, api_key=settings.HINDSIGHT_API_KEY, timeout=60.0)
BANK = settings.HINDSIGHT_BANK_ID

def remember(content, context, when, doc_id, meta):
    return hs.retain(bank_id=BANK, content=content, context=context,
                     timestamp=when, document_id=doc_id, metadata=meta, retain_async=False)

def recall(query, budget="mid"):
    r = hs.recall(bank_id=BANK, query=query, budget=budget, max_tokens=4096, include_chunks=True)
    out = []
    for m in r.results:
        chunk = (r.chunks or {}).get(getattr(m, "chunk_id", None))
        out.append({"text": m.text, "type": m.type, "source": chunk.text[:400] if chunk else None})
    return out

def reflect(query, context=None, budget="mid"):
    return hs.reflect(bank_id=BANK, query=query, context=context, budget=budget).text
```

> **Timing gotcha:** retain does processing (fact extraction/consolidation). Seed hours before the demo. Measure how long a fresh resolve takes to become recallable; if slow, keep `retain_async=False` and also include the just-resolved text directly in the next prompt for the live demo.

---

## 9. LLM layer (Groq)

- Default `openai/gpt-oss-120b`; on failure retry once, then `qwen/qwen3-32b`.
- Use JSON mode (`response_format={"type": "json_object"}`), validate with Pydantic, on parse failure send one "repair this JSON" call.
- Low temperature (0.2).

### 9.1 Triage prompt (`prompts.py`)
```
SYSTEM:
You are OnCall AI, an incident-response assistant for an engineering team.
You receive a NEW INCIDENT and RELEVANT MEMORY from the team's past incidents,
deploys, resolutions and engineer preferences.
Rules:
- Base conclusions on memory when it is genuinely similar (same service, same error
  signature, same change type). Say so explicitly and cite incident/deploy IDs.
- If memory is not relevant, say "No close match in memory" and reason from first principles.
- Always list fixes that FAILED before under "avoid".
- Respect engineer preferences for length/format.
- Never invent incident IDs that are not in memory.
Return ONLY JSON:
{
 "matched": bool,
 "root_cause": str,
 "recommended_fix": [str],
 "avoid": [str],
 "similar_incidents": [{"id": str, "when": str, "why_similar": str}],
 "suspect_change": str | null,
 "confidence": "low" | "medium" | "high",
 "spoken_summary": str   // <= 3 sentences, no logs, no code
}

USER:
NEW INCIDENT:
{alert_text}

RELEVANT MEMORY:
{memories_formatted or "(memory disabled)"}

ENGINEER: {engineer_name}
```

### 9.2 Risk-check prompt
Same shape; output:
```json
{"risk_level": "low|medium|high", "evidence": [{"id": "", "when": "", "what_happened": ""}],
 "recommendation": [""], "watch_metrics": [""], "spoken_summary": ""}
```

### 9.3 Voice intent prompt
Classify transcript → `{"intent": "triage|resolve|preference|question", "payload": {...}}`.

---

## 10. API contract

| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/api/triage` | `{alert_text, use_memory: bool, engineer}` | triage JSON + `memories_used[]` |
| POST | `/api/resolve` | `{incident_id, alert_text, service, worked, failed, notes, engineer}` | `{ok, retained_ids}` |
| POST | `/api/risk-check` | `{service, change_description, diff?, use_memory}` | risk JSON + `memories_used[]` |
| GET | `/api/playbook/{service}` | — | `{current, previous, updated_at}` |
| POST | `/api/playbook/{service}/refresh` | — | `{current}` |
| POST | `/api/voice/transcribe` | multipart `audio` | `{text}` |
| POST | `/api/voice/speak` | `{text}` | `audio/wav` |
| POST | `/api/voice/command` | multipart `audio`, `engineer` | `{transcript, intent, result, spoken_summary}` |
| GET | `/api/memories?q=` | — | recall results for the Memory Timeline |
| GET | `/api/health` | — | Hindsight + Groq status |

Freeze this contract in hour 1 so frontend and backend work in parallel (frontend can mock responses).

---

## 11. Synthetic data spec

**Company:** "Kirana Cart", fictional Indian quick-commerce app (makes the story relatable).
**Services:** `payments-service`, `checkout-api`, `auth-service`, `search-service`, `notification-worker`
**Period:** ~6 months back from demo day. **~20 incidents, ~40 deploys.** Realistic engineer names, timestamps, log excerpts (Java/Python/Node traces, Postgres/Redis/Kafka errors).

### Incident JSON
```json
{
  "id": "INC-0412", "title": "Checkout 503s during evening peak",
  "service": "payments-service", "severity": "SEV1",
  "started_at": "2026-08-14T19:42:00+05:30", "detected_by": "PagerDuty: p99 latency > 3s",
  "symptoms": "...", "error_signature": "HikariPool-1 - Connection is not available, request timed out after 30000ms",
  "log_excerpt": "...", "root_cause": "...", "related_deploy": "DEP-812",
  "fixes_tried": [{"action": "Restarted payments pods", "worked": false},
                  {"action": "Rolled back DEP-812", "worked": true}],
  "resolution": "...", "ttr_minutes": 38, "responders": ["Ravi", "Sneha"]
}
```

### Deploy JSON
```json
{"id": "DEP-812", "service": "payments-service", "timestamp": "2026-08-14T18:55:00+05:30",
 "author": "Ravi", "change_summary": "Reduce DB pool max from 50 to 20 to cut RDS cost",
 "diff_snippet": "- maximumPoolSize: 50\n+ maximumPoolSize: 20", "caused_incident": "INC-0412"}
```

### Planted patterns (the demo depends on these)
- **A (hero):** payments-service DB pool changes → incidents **3 times** (Apr, Jun, Aug). Pod restart failed every time; rollback worked.
- **B:** Redis evictions on `checkout-api` during sale events (Diwali/Big Sale) → fix: raise maxmemory + TTL on cart keys.
- **C:** `auth-service` JWT clock-skew bug fixed permanently in May → agent should say "fixed in May; if it recurs, suspect regression".
- **Noise:** ~12 unrelated incidents so recall has to discriminate.

`generate_data.py`: ask the LLM for incidents/deploys **per pattern** with the schema above, then hand-edit the hero pattern. `seed_memory.py`: convert each record to a natural-language paragraph and `retain` with backdated `timestamp`.

`demo_alerts.json`: the exact new alert (pattern A, 4th occurrence) and the exact PR text for the risk check. Rehearse with these.

---

## 12. Frontend screens

1. **Incident Console** (main)
   - Left: alert textarea (prefilled from `demo_alerts.json`), service dropdown, **PushToTalk** button, **Memory ON/OFF** toggle, Analyze.
   - Right: **DiagnosisCard** (root cause, fix steps, red "Avoid" box, confidence badge) + **MemoryEvidence** (cited past incidents with dates, source snippets).
   - "Resolve" drawer: worked / failed / notes (or speak it).
2. **Change Review:** PR title + description + diff → risk badge, evidence timeline, recommendations.
3. **Playbooks:** per-service playbook; "v2 → v3" diff highlighting new lines after a resolution.
4. **Memory Timeline** *(optional)*: chronological list of what the agent knows, filterable by service.

Design: dark "ops console" look, monospace for logs, red/amber/green severity. Split-screen when Memory OFF vs ON is compared.

---

## 13. Work split

| Person A: memory, data, backend | Person B: frontend, voice, story |
|---|---|
| Hindsight Cloud + bank + smoke test | Vite app, layout, API mocks from contract |
| `generate_data.py`, `seed_memory.py` | IncidentConsole, DiagnosisCard, MemoryEvidence |
| `/triage`, `/resolve`, `/risk-check` | ChangeReview, MemoryToggle |
| Prompts, JSON validation, fallbacks | PushToTalk, `/voice/*` endpoints, TTS fallback |
| Playbooks (mental models) | README, demo script, video, content pieces |

## 14. Timeline

| Hours | Milestone | Owner |
|---|---|---|
| 0–1 | Keys, Hindsight smoke test passes, API contract frozen, repo scaffolded | Both |
| 1–3 | Data generated + seeded; `/triage` works end-to-end with real memory | A · B builds UI on mocks |
| 3–5 | `/resolve` + failed-fix memory; UI wired to real API | A · B |
| 5–7 | `/risk-check` (headline); playbooks if on track | A · B: Change Review screen |
| 7–8.5 | Voice (STT, TTS, intents, preferences); UI polish | B (A helps) |
| 8.5–10 | Rehearse demo ×3, fix bugs, record demo video | Both |
| 10–12 | README + "How we use Hindsight", articles, posts, videos | Both |

**Cut rule:** behind at hour 5 → drop playbooks. Voice never blocks triage or risk check.

---

## 15. Demo script (~3 min)

1. **Problem (20s):** "It's 2 AM. Kirana Cart checkout is failing. The engineer who fixed this last time has left."
2. **Memory OFF (20s):** Paste alert → generic advice ("check DB, restart pods").
3. **Memory ON (40s):** Same alert → "Matches INC-0412 (Aug), INC-0288 (Jun). Root cause: pool size change. Do NOT restart pods; roll back." Point to the citations.
4. **Learn by voice (30s):** Hold mic: "Rollback of 901 fixed it, restart didn't help. And keep briefings shorter." → Playbook updates v2 → v3.
5. **Prevention (50s):** Change Review → paste PR "reduce payments pool to 25". → **HIGH RISK**, evidence from 4 incidents, recommendation. "We went from remembering incidents to preventing them."
6. **Close (20s):** Spoken short briefing on a new alert shows the preference was learned. "Every incident makes it smarter."

---

## 16. README must include

- One-paragraph pitch + demo GIF/video link
- Problem → solution → why memory is essential
- **How we use Hindsight** (retain / recall / reflect / mental models table + diagram)
- Before/after screenshots (Memory OFF vs ON)
- Comparison with HolmesGPT and plain RAG (short table)
- Setup instructions, env vars, seeding
- Architecture diagram, API list
- Limitations + roadmap (real PagerDuty/GitHub integration, Slack bot, feeding recall into a Holmes-style live investigation)

---

## 17. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Retain → recall latency | Seed early; `retain_async=False`; inject fresh resolution into prompt directly during demo |
| Groq JSON/tool errors | No tool calling; JSON mode + Pydantic + repair call + fallback model |
| Recall returns irrelevant memories | Include service + error signature in query; skeptical disposition; prompt says "no close match" is allowed |
| Orpheus TTS (Preview) fails | `TTS_PROVIDER=browser` fallback |
| Noisy venue breaks STT | Push-to-talk, Whisper `prompt` with jargon, typed fallback, voice shown in recorded video |
| Rate limits during demo | Cache responses for the exact demo inputs as last-resort backup |
| Looks like other incident agents | Lead the demo with risk check + failed-fix memory + voice learning, not plain triage |

---

## 18. Links

- Hindsight docs: https://hindsight.vectorize.io/
- Hindsight Python client: https://hindsight.vectorize.io/sdks/python
- Mental models: https://hindsight.vectorize.io/developer/mental-models
- Hindsight GitHub: https://github.com/vectorize-io/hindsight
- Hindsight Cloud: https://ui.hindsight.vectorize.io
- Idea inspiration repo: https://github.com/vectorize-io/self-driving-agents
- Groq console: https://console.groq.com/
- Groq speech-to-text: https://console.groq.com/docs/speech-to-text
- Groq text-to-speech: https://console.groq.com/docs/text-to-speech
- HolmesGPT: https://github.com/HolmesGPT/holmesgpt
