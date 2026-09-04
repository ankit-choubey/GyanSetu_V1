# ENVIRONMENT_SETUP.md — Zero-to-Running (Day 0)

> This is "Day 0" — everything here should be done **before** Build Guide §8's Day 1 plan starts. The Day 1 morning task list assumes tools are already installed and keys already work. Don't let Day 1 morning become Day 0 by accident.
>
> Do this once, together (a 10-minute sync beats three people independently hitting the same blocker), then confirm independently that it works on each person's own machine.

---

## 1. Local Tooling — Install Before Anything Else

| Tool | Needed for | Check installed |
|---|---|---|
| **Node.js 18+ (LTS)** | Frontend (Next.js) | `node -v` |
| **Python 3.11+** | Backend (FastAPI), ML/AI | `python3 --version` |
| **Git** | Everything — see `GIT_WORKFLOW.md` | `git --version` |
| **pip / venv** | Python dependency isolation | `python3 -m venv --help` |
| **npm or pnpm** | Frontend dependencies | `npm -v` |
| A code editor or agentic IDE | All | — |

If any of these are missing, install them **before** the hackathon clock starts — troubleshooting a Python version mismatch on Day 1 morning eats into build time you don't get back.

---

## 2. Accounts to Create — Do This as a Team, Not Solo, So You Don't Duplicate Signups

| Service | Purpose | Who needs it | Credit card? |
|---|---|---|---|
| **GitHub** (x2 — one per repo owner, see `GIT_WORKFLOW.md`) | Source control | Everyone, as collaborators | No |
| **Groq Console** (console.groq.com) | LLM inference | ML/AI owner primarily; see §3 for shared-vs-individual-key tradeoff | No, for free tier |
| **Vercel** | Frontend hosting | Frontend owner | No, for hobby tier |
| **Render** *or* **Railway** — pick one, don't set up both | Backend hosting | Backend owner | No, for free tier (may sleep on inactivity — factor into demo rehearsal) |
| **Supabase** *or* **Neon** — pick one | Managed PostgreSQL | Backend owner | No, for free tier |
| **Upstash** (optional) | Managed Redis, if you use the optional caching layer | Backend owner | No, for free tier |

> Whichever you pick for hosting/DB, record the choice in `PROJECT_CONTEXT.md` §9 and the URL in `PROJECT_STATUS.md` §2 so it isn't ambiguous later which one is "the" deployment.

**Not needed as a separate account:** ChromaDB (runs embedded/local, no account), local Whisper and local Sentence Transformers (downloaded as model weights the first time you run them — no login required for the standard public models this project uses; if you ever hit a Hugging Face download rate-limit on a shared network, a free Hugging Face account + `huggingface-cli login` resolves it, but treat this as a fallback, not a Day 0 requirement).

---

## 3. Groq Setup (Replaces Gemini — Full Detail)

### 3.1 Get an API key
1. Go to **console.groq.com** and sign up (no credit card required for the free tier).
2. Go to **API Keys** → **Create API Key**. Copy it immediately — Groq shows it once.
3. Put it in your `.env` file as `GROQ_API_KEY=...` (never anywhere else — see `GIT_WORKFLOW.md` §7).

### 3.2 Shared key vs. individual keys — pick one and note the choice in `PROJECT_CONTEXT.md` §9
| | One shared key | Three individual keys |
|---|---|---|
| Setup effort | Lowest — one person creates it, shares via a secure channel (not group chat, not committed anywhere — see §6 below) | Each person signs up separately |
| Rate limit behavior | Free-tier limits are shared across everyone using the key — heavy MCQ-generation testing by one person can throttle everyone else mid-demo-prep | Each person gets their own limit, isolating one person's testing load from another's |
| Recommended when | Team is disciplined about not batch-testing at the same time as someone else | You've already hit a rate limit once with a shared key |

Either way works for a 3-day hackathon; the individual-key option is the safer default if you can spare the 5 minutes per person.

### 3.3 Endpoint and model IDs
Groq exposes an **OpenAI-compatible** chat completions API, so anything already written against the OpenAI Python/JS SDK works by pointing the `base_url` at Groq instead:

```
Base URL:  https://api.groq.com/openai/v1
Header:    Authorization: Bearer $GROQ_API_KEY
```

Model IDs to use (these are current production model IDs on Groq — pin them by exact string, don't guess a name):

| Model ID | Use it for | Notes |
|---|---|---|
| `llama-3.3-70b-versatile` | Primary model: MCQ generation, concept extraction, chatbot answers | 131K context window, general-purpose, good default per Build Guide §3's "Tier 1: LIVE LLM" |
| `llama-3.1-8b-instant` | Fast fallback for latency-sensitive calls, or if you're deliberately trading quality for speed under a rate-limit crunch | Notably faster, still 131K context |
| `openai/gpt-oss-120b` | Alternative if you want a second production-grade model for comparison/validation cross-checks | Also 131K context |

Preview models (`qwen/qwen3-32b`, `meta-llama/llama-4-scout-17b-16e-instruct`, etc.) exist on Groq but are explicitly not meant for anything you depend on for the demo — Groq can deprecate or change these without notice. Stick to the production-tier models above for anything that has to work on demo day.

### 3.4 Test it works (do this before writing any project code against it)
```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $GROQ_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Reply with exactly one word: hello"}]
  }'
```
Or from Python, using the OpenAI SDK pointed at Groq:
```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_GROQ_API_KEY",   # or os.environ["GROQ_API_KEY"]
    base_url="https://api.groq.com/openai/v1",
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[{"role": "user", "content": "Reply with exactly one word: hello"}],
)
print(response.choices[0].message.content)
```
If this returns a response, `ML-001` in `PROJECT_STATUS.md` can move to `DONE`.

### 3.5 Rate limits — check live, don't trust a hardcoded number
Groq's free tier applies per-minute request limits and daily token caps that vary by model and change over time, at the **organization level** (shared across everyone using that key, per §3.2). Rather than build against a number that may already be stale by the time you read this, check the current limits for your own key at **console.groq.com/settings/limits** on Day 0, and re-check if you start seeing `429 Too Many Requests` errors. Build Guide §3's 4-Tier Fallback Hierarchy (Live LLM → validated cache → curated bank → deterministic response) exists specifically so a rate-limit hit doesn't take down your demo — make sure Tier 2's cache is actually populated before Day 3, not assumed.

### 3.6 Optional: Groq also hosts Whisper, if you ever want it
The Build Guide's ML/AI stack uses **local** Whisper (tiny/base) for speech-to-text, and that's unchanged by this patch. If local Whisper turns out to be too slow or too heavy for a demo laptop, Groq also serves `whisper-large-v3` and `whisper-large-v3-turbo` as hosted transcription endpoints on the same API key — worth knowing as a fallback option, not a required change.

---

## 4. `.env.example` — Copy This Into Each Service, Fill In Real Values Locally, Never Commit the Filled-In Version

### Backend (`backend/.env.example`)
```bash
# Database
DATABASE_URL=postgresql://user:pass@host:5432/dbname

# Auth
JWT_SECRET=replace-with-a-long-random-string
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# CORS — comma-separated list of allowed frontend origins
CORS_ORIGINS=http://localhost:3000,https://your-frontend.vercel.app

# ML service (if backend calls ML as a separate service rather than a shared import)
ML_SERVICE_URL=http://localhost:8001

# Optional
REDIS_URL=redis://default:password@host:port
```

### ML/AI (`ml_pipeline/.env.example`)
```bash
# Groq — replaces GEMINI_API_KEY everywhere the Build Guide mentions it
GROQ_API_KEY=your_groq_key_here
GROQ_BASE_URL=https://api.groq.com/openai/v1
GROQ_MODEL_PRIMARY=llama-3.3-70b-versatile
GROQ_MODEL_FAST=llama-3.1-8b-instant

# ChromaDB (embedded — local path, not a hosted service)
CHROMA_PERSIST_DIR=./chroma_db
```

### Frontend (`frontend/.env.local.example`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

> Note `.env.local.example` for Next.js — Next.js's convention is `.env.local` for local overrides, which is already in the `.gitignore` from `GIT_WORKFLOW.md` §3.

---

## 5. Database Setup (Supabase or Neon — Whichever You Picked in §2)

1. Create a new project on your chosen provider's dashboard.
2. Copy the connection string it gives you — this goes into `DATABASE_URL` in the backend `.env`. It'll look like:
   ```
   postgresql://<user>:<password>@<host>:5432/<database>
   ```
3. Confirm you can connect from your local machine before writing any migration:
   ```bash
   psql "$DATABASE_URL" -c "SELECT 1;"
   ```
4. Run your first Alembic migration once the models exist (Build Guide §10, `DB-001` in `PROJECT_STATUS.md`).

---

## 6. Sharing Keys Safely Among 3 People

Do **not** share API keys or DB passwords over group chat screenshots, in `PROJECT_STATUS.md`, or in any committed file. Use whatever password manager or encrypted-note tool the team already trusts (or, at minimum, a chat message that gets deleted after the other person confirms they copied it) — the point is that it never lands somewhere `git log` or a public channel history can surface it later.

---

## 7. Day 0 Checklist — Run Through This as a Group

```
☐ Node.js, Python, Git installed on all 3 laptops
☐ All 3 people have GitHub accounts and are collaborators on both repos (GIT_WORKFLOW.md §2)
☐ Groq account created, API key generated, curl test in §3.4 returns a response
☐ Vercel account created (Frontend owner)
☐ Render/Railway account created (Backend owner) — pick one
☐ Supabase/Neon account created (Backend owner) — pick one, connection string confirmed with psql
☐ .env.example copied to .env in each service folder, filled in locally, confirmed NOT tracked by git
☐ Frontend: npm install runs clean, npm run dev serves a page locally
☐ Backend: pip install -r requirements.txt runs clean, uvicorn serves /docs locally
☐ ML/AI: Groq test call (§3.4) succeeds from a plain Python script, before wiring into the pipeline
☐ PROJECT_STATUS.md updated: header filled in, Quick Dashboard still accurate
```

Once every box above is checked, you're ready for Build Guide §8's Day 1 morning plan.

---

## 8. Troubleshooting Quick Reference

| Symptom | Likely cause | Fix |
|---|---|---|
| `curl` to Groq returns 401 | Key not set, or set in the wrong shell session | `echo $GROQ_API_KEY` to confirm it's actually exported; re-check for a copy-paste trailing space |
| Groq returns 429 | Rate limit hit (see §3.5) | Check console.groq.com/settings/limits; wait, or switch to `llama-3.1-8b-instant`, or fall back to cache (Build Guide §3, Tier 2) |
| `psql` can't connect | Wrong connection string, or provider requires SSL params | Copy the exact string from the provider dashboard again; some require `?sslmode=require` appended |
| `git push` asks for a password and rejects it | GitHub no longer accepts account passwords for git operations | Use a Personal Access Token or SSH key instead — see `GIT_WORKFLOW.md` §2 |
| Frontend can't reach backend locally | CORS not enabled, or wrong `NEXT_PUBLIC_API_URL` | Check `CORS_ORIGINS` in backend `.env` includes `http://localhost:3000`; check the frontend env var matches where the backend is actually running |
