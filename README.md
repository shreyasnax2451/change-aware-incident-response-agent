# OnCall AI — Change-Aware Incident Memory Agent

> **Built for HackwithHyderabad 3.0**

**OnCall AI** is an intelligent, voice-enabled on-call engineering assistant that acts as the persistent, institutional memory of your engineering organization. It remembers every past production incident, exactly what caused it, the fixes that successfully resolved it, and most importantly—the fixes that *failed*. 

By leveraging a vectorized memory bank, OnCall AI fundamentally changes incident response from a stressful, reactive scramble into a confident, memory-driven process. It helps engineers resolve live incidents faster and preemptively warns teams about risky code deployments *before* they ship to production.

---

## The Problem: Organizational Amnesia

In modern software engineering, the speed of shipping code often outpaces a team's ability to document and retain operational knowledge. This leads to several critical issues:

1. **The 2 AM Panic:** When a critical service goes down at 2 AM, the responder on-call is often not the person who wrote the system. They lack the context of previous similar failures.
2. **Repeating Past Mistakes:** Responders waste precious downtime (TTR) attempting standard fixes (e.g., "restart the pods", "scale up the database") that have historically proven ineffective for that specific error signature.
3. **Reactive, Not Proactive:** Traditional incident response tools only help *after* the system breaks. They don't warn you if a newly merged pull request looks dangerously similar to a deploy that took down the site three months ago.
4. **Knowledge Silos:** When senior engineers leave, their mental models of failure states leave with them. 

## The Solution: Institutional Memory

**OnCall AI** acts as a brain that sits alongside your alerting and deployment pipelines, capturing the "tribal knowledge" of your operations. 

- **Reactive Triage (Incident Console):** When an alert fires, OnCall AI immediately queries its memory bank to find the closest historical matches based on error signatures and symptoms. It tells you exactly what worked last time and warns you against what didn't.
- **Proactive Prevention (Change Review):** Before a developer merges a pull request, OnCall AI reviews the code diff and queries its memory. If a similar infrastructure change previously caused an outage, it flags the PR as "High Risk" and provides concrete historical evidence.
- **Continuous Learning:** Every time an incident is resolved, the engineer dictates a quick post-mortem (via text or voice). OnCall AI immediately ingests this outcome into its memory, instantly making the agent smarter for the next outage.

---

## Core Features

1. **Memory-Driven Incident Triage:** Paste an alert (or speak it), and OnCall AI will diagnose the issue by citing exact past incident IDs.
2. **Pre-Deploy Risk Checks:** Paste a PR description or diff snippet. The agent checks if similar changes have broken production in the past.
3. **Interactive Voice Mode:** Designed for the chaotic 2 AM page. Engineers can push-to-talk to report symptoms, ask for past context, or dictate resolution notes entirely hands-free.
4. **Living Memory Timeline:** A fully searchable, instantaneous dashboard of every incident, deployment, and engineer preference the system knows about.
5. **Engineer Preferences:** The system learns how individual engineers like their briefings. If you tell it "keep it under two sentences," it remembers that preference for your future on-call shifts.

---

## How We Use Hindsight Memory

We use **Hindsight Cloud** as our vectorized memory backend to give the agent its persistent memory. Instead of relying on static, quickly-outdated Runbooks, OnCall AI dynamically queries past events.

| Feature | Hindsight Operation | Explanation |
|---|---|---|
| **Resolving Incidents** | `retain(...)` | When an incident concludes, we retain a structured natural-language paragraph detailing the symptoms, the root cause, the successful fix, and the failed fixes. |
| **Alert Triage** | `recall(...)` | When a new alert arrives, we query Hindsight using the alert text to find semantically similar past incidents, which the LLM synthesizes into a diagnosis. |
| **Change Review** | `recall(...)` | When a PR is submitted, we query the change description against the bank of past deploys and incidents to find historical risk evidence. |
| **Engineer Preferences** | `retain(...)` / `recall(...)` | Engineers can specify preferences ("No stack traces"). We store this as a preference document and recall it based on the current user's name. |

### Before/After: The Power of Memory

**(Insert Screenshots Here)**
- **Memory OFF:** The agent behaves like a standard LLM. It gives generic advice: "Check the logs, scale up pods, check database connections."
- **Memory ON:** The agent becomes a seasoned Staff Engineer. "This matches **INC-0412**. Last time this happened, the database connection pool was reduced. **Do NOT restart pods**—that failed last time. Rollback deploy #812."

---

## Comparison: OnCall AI vs. The Landscape

| Feature | OnCall AI (Ours) | HolmesGPT | Plain RAG |
|---|---|---|---|
| **Core Question** | "Have we seen this before, and what worked?" | "What is happening right now?" | "What is in the docs?" |
| **Knowledge Source** | Accumulated memory of incidents & deploys | Live telemetry + static runbooks | Static wikis and runbooks |
| **Learning** | Every resolution natively updates memory | Runbooks change only manually | Needs manual doc updates |
| **Deploys** | Predicts risk **before** merge | Verifies health **after** deploy | N/A |
| **Failed Fixes** | Remembered and warned against | Not a first-class concept | N/A |

---

## Technical Setup & Instructions

### Prerequisites
- Python 3.10+
- Node.js & npm
- Hindsight API Key & Base URL
- Groq API Key

### 1. Environment Variables
Copy `.env.example` to `.env` and fill in your keys:
```env
GROQ_API_KEY=your_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_FALLBACK_MODEL=qwen/qwen3-32b
HINDSIGHT_BASE_URL=your_hindsight_url
HINDSIGHT_API_KEY=your_hindsight_key
HINDSIGHT_BANK_ID=dejavu-eng
TTS_PROVIDER=groq
```

### 2. Backend Setup
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Seed the memory bank with synthetic historical data
python scripts/generate_data.py
python scripts/seed_memory.py

# Start the server
uvicorn main:app --reload --port 8000
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

---

## Architecture

```text
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
└───────┬───────────────────────────┬───────────────────────────────┘
        │                           │
  Hindsight Cloud               Groq API
  (Vector DB & Memory)          (LLM, Whisper, Orpheus)
```

## API Reference
- `POST /api/triage`: Triage an incoming alert
- `POST /api/resolve`: Submit a resolution to be retained
- `POST /api/risk-check`: Review a PR for deployment risk
- `GET /api/playbook/{service}`: Fetch living playbooks
- `POST /api/voice/command`: Process push-to-talk audio commands
- `GET /api/memories`: Fetch the global timeline of all memories

---

## Limitations & Roadmap
- **Real-Time Integrations:** Currently uses mock alerts. The roadmap includes real Webhook integrations for PagerDuty, OpsGenie, and AlertManager to intercept live pages.
- **Live Observability:** Future updates will feed OnCall AI's historical recall directly into a live investigation toolset, allowing the agent to query Grafana/Datadog directly based on past incident signatures.
- **ChatOps:** Integrating directly as a Slack/Teams bot so engineers can interact without a dedicated dashboard, retaining incident conversation threads natively.