# PROJECT_CONTEXT.md — Read This First

> **Read time: ~8 minutes. Read before you write a single line of code.**
> This is the single onboarding document for GyanSetu. It doesn't replace `GyanSetu_IDEA.md` (the "why/what," frozen) or `GyanSetu_BUILD_GUIDE.md` (the "how," frozen except for the Operating Reality Patch at its top) — it sits above both of them and tells you what to read, in what order, and what's actually true about the team, the stack, and the repos *right now*.
>
> If anything in this file conflicts with `GyanSetu_BUILD_GUIDE.md` or `GyanSetu_IDEA.md`, **this file wins** — it's the newest and it's meant to be kept current. If anything in this file conflicts with `PROJECT_STATUS.md`, **`PROJECT_STATUS.md` wins** for anything about "what's actually built right now" — that file updates every session, this one doesn't.

---

## 0. Team Roster — CONFIRM THIS FIRST

This mapping was inferred from the two GitHub accounts supplied when this file was created. It has **not** been confirmed by the team. Fix it now — it's a 30-second edit — because every other document (`PROJECT_STATUS.md`, `HANDOFF.md`, `GIT_WORKFLOW.md`, `ENVIRONMENT_SETUP.md`) points back here for the roster instead of duplicating it.

| Track | Owner name | GitHub handle | Owns |
|---|---|---|---|
| ML/AI | Ankit Choubey | `ankit-choubey` | Document ingestion, MCQ generation, RAG chatbot, validation pipeline — everything in Build Guide Section 11 |
| Backend | Utkarsh **[confirm surname — GitHub handle suggests "Singh," unconfirmed]** | `UtkarshSingh-09` | API, database, competency engine, agents, orchestrator — everything in Build Guide Section 10 |
| Frontend | **[CONFIRM NAME]** | **[CONFIRM GITHUB HANDLE]** | UI, dashboards, charts, deployment — everything in Build Guide Section 9 |

**Why only 3 names when the Build Guide lists 6 (Aarth, Devraj, Mounya, Utkarsh, Likhita, Ankit)?** The Build Guide was written assuming 3 pairs. The team actually executing this sprint is these 3 people, each solo-owning what used to be a pair's combined scope. Everywhere the Build Guide says "Aarth & Devraj," "Mounya & Utkarsh," or "Likhita & Ankit," read it as the one owner above. Don't go rewrite all 500+ name mentions in that file — this table is the correction layer (the Operating Reality Patch at the top of the Build Guide says the same thing, more briefly).

**What changes because of that:**
* No pair-partner reviews your code anymore → use the Solo Builder Self-Review Checklist in `HANDOFF.md` before every push.
* The original 3-day task list (Build Guide §8) was sized for 2 people per track. One person will not finish all of it at the same pace. That is expected, not a failure — see §4 below for how to handle it.
* "All 6 members meet" anywhere in the Build Guide now means "all 3 owners meet."

---

## 1. What Is GyanSetu, in 90 Seconds

Full detail lives in `GyanSetu_IDEA.md` (8,000+ lines — don't read it cover to cover unless you're making a strategic/positioning decision). Here's what you need to build:

GyanSetu is **not** a course catalogue. The product object is **competency state**, not course completion. The one-line pitch:

> "iGOT gives you courses. GyanSetu identifies your highest-confidence competency gaps, delivers targeted interventions, proves whether you learned with validated evidence, and verifies retention over time."

The closed loop that everything else serves:

```text
ROLE → REQUIRED COMPETENCY → CURRENT EVIDENCE → COMPETENCY STATE → GAP + UNCERTAINTY
  → PRIORITY → NEXT BEST ACTION → LEARNING → ASSESSMENT → NEW EVIDENCE
  → COMPETENCY UPDATE → VERIFICATION → RETENTION
```

If a feature doesn't serve this loop, it's an enhancement, not core — see the Priority Stack (Build Guide §23) before spending time on it.

**The three pieces you're building** (Build Guide §2 has full detail):
1. **Frontend** — Next.js dashboard: login, competency dashboard, adaptive assessment, next-best-action card, scenario practical task, admin workforce view, chatbot, agent timeline.
2. **Backend** — FastAPI + PostgreSQL: auth, competency engine (evidence fusion), orchestrator + 3 agents (diagnostic, intervention, monitoring), normalized adapters for iGOT/NSSTA/TPAC.
3. **ML/AI** — Document ingestion, MCQ generation + validation, RAG chatbot, all now running on **Groq** instead of Gemini (see §5 below).

---

## 2. Document Map — What to Read, When

| Document | What it is | Frozen or living? | Read it when |
|---|---|---|---|
| `GyanSetu_IDEA.md` | Product strategy & design record, Steps 1–5 | **Frozen** | Only if you need to understand *why* a product decision was made |
| `GyanSetu_BUILD_GUIDE.md` | The technical build plan, tech stack, day-by-day plan, API contract, engineering governance | **Frozen** except the Operating Reality Patch at the very top | Your main reference while building. Read the Operating Reality Patch first — it tells you what's been superseded |
| `PROJECT_CONTEXT.md` (this file) | Onboarding + source-of-truth map | Living, but changes rarely | First, and whenever something feels contradictory between documents |
| `ENVIRONMENT_SETUP.md` | Zero-to-running setup: accounts, `.env`, install steps, Groq specifics | Living | Before Day 1 — this is "Day 0" |
| `GIT_WORKFLOW.md` | Two-repo, two-account git model | Living | Before your first commit |
| `PROJECT_STATUS.md` | What's actually built, deployed, and broken *right now* | **Living — update every session** | Start and end of every work session |
| `HANDOFF.md` | Fillable templates for session/day/final handoff | Living, templates reused | End of every session, end of every day, before the demo |

**Source-of-truth rule when documents disagree:** `PROJECT_STATUS.md` (reality right now) > `PROJECT_CONTEXT.md` / `GIT_WORKFLOW.md` / `ENVIRONMENT_SETUP.md` (current operating rules) > `GyanSetu_BUILD_GUIDE.md`'s Operating Reality Patch > the rest of `GyanSetu_BUILD_GUIDE.md` (original frozen plan) > `GyanSetu_IDEA.md` (strategic rationale, changes slowest).

---

## 3. Scope Reality for a 3-Person Team

The Build Guide's Day-by-Day Plan (§8) lists a full Morning/Afternoon/Evening task list **per pair**. With one owner per track, you will not get through all of it at pair-speed. That's fine — it was never a hard requirement that every checkbox gets ticked. What matters is that you cut **visibly, in priority order, and record it**, instead of silently running out of time on Day 3 and discovering a core piece is missing.

**Cut order (from Build Guide §23 — do not reorder this):**
1. Core Competency Loop (diagnostic → gap → recommendation → evidence → state update) — never cut this.
2. Evidence correctness (6 evidence types, "no evidence ≠ low competency").
3. Assessment validity (grounding, single correct answer, validation pipeline).
4. Integration reliability (normalized adapters, SANDBOX/REPLAY modes).
5. Security & authorization (server-side RBAC).
6. Learner & admin experience (5-metric dashboard, explainable cards).
7. RAG assistant, visual polish, agent timeline.
8. Advanced research models (deep knowledge tracing, RL, etc.) — cut this first if squeezed.

If you're behind schedule, cut from the bottom of this list, not the top, and log what you cut and why in `PROJECT_STATUS.md`'s Cut Log. A judge will respect "we made a deliberate scope decision" far more than a broken demo of something at the top of the list.

**Practical adjustment for solo ownership:** treat the Morning/Afternoon/Evening split in each day's plan as a rough backlog ordering, not a literal 3-slot schedule. Pull items top-to-bottom until you run out of time in the day, then re-baseline `PROJECT_STATUS.md` before starting the next day.

---

## 4. What Actually Changed (Summary)

Three concrete changes were made on top of the original two documents. Full detail is in the linked file for each:

1. **Team size:** 6 assumed → 3 actual. See §0 above.
2. **LLM provider:** Gemini → **Groq** (`GROQ_API_KEY`, OpenAI-compatible endpoint at `https://api.groq.com/openai/v1`, no card needed for the free tier). Full setup, exact model IDs, and current rate limits: `ENVIRONMENT_SETUP.md`. The rest of the ML/AI architecture (LangChain, ChromaDB, Sentence Transformers, local Whisper, the 4-tier fallback hierarchy, the MCQ validation pipeline) is **unchanged** — only the live LLM generation calls move providers.
3. **Git model:** one shared repo from Day 1 → **two repos, two GitHub accounts.** Private repo (`https://github.com/ankit-choubey/GyanSetu_V1.git`) for pre-hackathon scaffolding and solo practice; main repo (`https://github.com/UtkarshSingh-09/GyanSetu-.git`) is the one actually built in and judged on hackathon day. Full setup: `GIT_WORKFLOW.md`.

---

## 5. Non-Negotiable Rules (Condensed)

These are pulled from across the Build Guide because they're easy to lose in 2,700+ lines. If you remember nothing else, remember these:

* **No evidence ≠ low competency.** Missing data means "unassessed," never "failing."
* **Never claim certainty you don't have.** Show confidence/uncertainty alongside every mastery number.
* **Never fabricate.** No fake benchmark numbers, no fake latency measurements, no claiming live government integration when you're using sandbox data. Label sandbox/replay data honestly — `[SANDBOX DATA]`, `[REPLAY]`.
* **Server-side authorization on everything.** UI hiding a button is not security.
* **Never let a bad MCQ enter the assessment bank silently** — one ungrounded question corrupts the entire downstream competency estimate. Validate before storing.
* **The demo must survive 5 consecutive clean runs** with no live-internet dependency as a hard requirement, not a nice-to-have. Pre-generate and cache what the demo needs.
* **Secrets never go in source control.** Not in a commit, not in a screenshot you paste into chat, not in a public repo. See `GIT_WORKFLOW.md`.

---

## 6. Timeline

* **Day 0 (before the 3-day clock starts):** Everyone's laptop can run their piece locally, all accounts exist, all API keys work. Use `ENVIRONMENT_SETUP.md` as the checklist. Do this *before* Day 1 morning — the Build Guide's Day 1 plan assumes tools are already installed.
* **Day 1 — Foundation:** Build Guide §8, Day 1.
* **Day 2 — Integration:** Build Guide §8, Day 2.
* **Day 3 — Polish & Demo:** Build Guide §8, Day 3. End with the Final Pre-Demo Handoff in `HANDOFF.md`.

---

## 7. How AI Coding Agents Should Use This File

If you are an AI coding agent (Antigravity, Claude Code, or similar) picking up a task in this repo, Build Guide §36 already tells you to read `PROJECT_CONTEXT.md`, `PROJECT_STATUS.md`, and `HANDOFF.md` before starting. In practice:

1. Read this file for orientation and the source-of-truth order in §2.
2. Read `PROJECT_STATUS.md` for what's actually built and what's currently broken — don't assume the Build Guide's plan reflects reality.
3. Read the relevant `HANDOFF.md` entry (most recent session for your track) for open threads and known issues.
4. Read `ENVIRONMENT_SETUP.md` if your task touches dependencies, `.env`, or API keys.
5. Read `GIT_WORKFLOW.md` if your task involves committing, branching, or pushing.
6. Implement only the assigned task. Don't redesign frozen architecture (Build Guide §22 — Change Control) without an explicit change request.
7. Update `PROJECT_STATUS.md` and write a `HANDOFF.md` entry when you're done, using the Task Report format (Build Guide §45 / `HANDOFF.md` template). Never mark something done without stating what you actually verified.

---

## 8. Escalation & Contacts (3-Owner Version)

```
STUCK ON YOUR OWN TRACK
    ↓ (15 min max)
ASK THE OTHER TWO OWNERS
    ↓ (still stuck?)
ALL 3 OWNERS — 10 MIN SYNC
    ↓
FIX IT, OR CUT IT (log the cut in PROJECT_STATUS.md)
```

For domain-specific routing (who to ask about deployment vs. prompt quality vs. schema design), see Build Guide §17 — read every "Aarth/Devraj," "Mounya/Utkarsh," "Likhita/Ankit" there as the single owner from §0.

---

## 9. Open Items to Confirm

- [ ] Fill in the real Frontend owner's name and GitHub handle in §0.
- [ ] Confirm Utkarsh's full name in §0 (used in demo credits/README).
- [ ] Confirm whether the Groq API key will be one shared account (simplest, but rate limits are shared across all 3 of you) or three individual keys (see `ENVIRONMENT_SETUP.md` for the tradeoff).
- [ ] Confirm who has (or will get) collaborator/admin access on the main repo `UtkarshSingh-09/GyanSetu-` (see `GIT_WORKFLOW.md`).
- [ ] Confirm hosting picks — Render vs. Railway for backend, Supabase vs. Neon for Postgres (`ENVIRONMENT_SETUP.md` covers both, pick one per service so the URLs in `PROJECT_STATUS.md` §2 aren't ambiguous).
