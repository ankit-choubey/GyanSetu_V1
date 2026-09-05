# PROJECT_STATUS.md — Living Status Tracker

> **This file is a snapshot of reality, not a plan.** `GyanSetu_BUILD_GUIDE.md` says what *should* happen. This file says what *has* happened, as of the last time someone updated it. If this file says something is broken and the Build Guide implies it should be working, believe this file.
>
> **Update this file at the start and end of every work session — not just end of day.** A stale status file is worse than no status file, because people will trust it and be wrong. Takes 3 minutes. Do it anyway when you're tired.

---

## Header — Update Every Time

```
LAST UPDATED:     [YYYY-MM-DD HH:MM IST]
UPDATED BY:       [Ankit / Utkarsh / Frontend owner]
CURRENT PHASE:    [ Day 0 - Setup | Day 1 - Foundation | Day 2 - Integration | Day 3 - Polish & Demo | Post-Demo ]
HOURS REMAINING UNTIL DEMO: [ __ ]
```

---

## 1. Quick Dashboard

Update the emoji, not the prose — this table should be readable in 5 seconds.

| Area | Status | Notes |
|---|---|---|
| Frontend — deployed & reachable | 🔴 Not started | |
| Backend — deployed & reachable | 🔴 Not started | |
| ML/AI — Groq key working | 🟢 Working & verified | 70/70 automated tests PASS + 50 manual |
| Database — migrated & seeded | 🔴 Not started | |
| Frontend ↔ Backend integration | 🔴 Not started | |
| Backend ↔ ML/AI integration | 🔴 Not started | |
| Full closed loop (login → assessment → gap → recommendation) | 🔴 Not started | |
| Demo rehearsed end-to-end | 🔴 Not started | |

Legend: 🔴 Not started · 🟡 In progress / partially working · 🟢 Working & verified · ⚫ Blocked

---

## 2. Environment & Deployment Status

| Service | Purpose | URL | Status | Last verified | Owner |
|---|---|---|---|---|---|
| Frontend (Vercel) | UI | `[fill in]` | 🔴 | — | Frontend owner |
| Backend (Render/Railway) | API | `[fill in]` | 🔴 | — | Utkarsh |
| Database (Supabase/Neon) | PostgreSQL | `[fill in, host only — never paste credentials here]` | 🔴 | — | Utkarsh |
| Groq | LLM inference | console.groq.com | 🔴 | — | Ankit |
| ChromaDB | Vector store | local / embedded | 🔴 | — | Ankit |
| Private repo | Pre-hackathon code | `github.com/ankit-choubey/GyanSetu_V1` | 🟢 | — | Ankit |
| Main repo | Hackathon-day code | `github.com/UtkarshSingh-09/GyanSetu-` | 🔴 | — | Utkarsh |

> Never put an actual API key, password, or connection string in this file — it may end up in the shared/public repo. Host/URL only. Full secret-handling rules: `GIT_WORKFLOW.md` and `ENVIRONMENT_SETUP.md`.

---

## 3. Task Board

Use the Task ID scheme from Build Guide §45: `FE-xxx`, `BE-xxx`, `ML-xxx`, `DB-xxx`, `API-xxx`, `EVAL-xxx`, `TEST-xxx`, `UI-xxx`, `DOC-xxx`, `DEMO-xxx`, `FINAL-xxx`. Status values from Build Guide §21: `PENDING → IN_PROGRESS → BLOCKED → DONE`. Only mark `DONE` when you've actually run and verified it — see the Solo Builder Self-Review Checklist in `HANDOFF.md`. Prefix every related git commit message with the Task ID (see `GIT_WORKFLOW.md` §6) so a commit and a status row can always be traced back to each other.

### ML/AI (Ankit)

| Task ID | Description | Status | Last updated |
|---|---|---|---|
| ML-001 | Groq API key working, test call succeeds | DONE | 2026-09-06 |
| ML-002 | PDF/PPT text extraction, tables & OCR fallback | DONE | 2026-09-06 |
| ML-003 | MCQ generation function & schema validation | DONE | 2026-09-06 |
| ML-004 | MCQ validation pipeline (grounding, distractor, dupes) | DONE | 2026-09-06 |
| ML-005 | ChromaDB local vector store & dense embeddings | DONE | 2026-09-06 |
| ML-006 | Grounded RAG chatbot with strict abstention | DONE | 2026-09-06 |
| ML-007 | Token-aware semantic chunker engine | DONE | 2026-09-06 |
| ML-008 | 3-tier Adaptive question selector & remediation | DONE | 2026-09-06 |
| ML-009 | Multi-metric MCQ quality scorer & option shuffler | DONE | 2026-09-06 |
| ML-010 | Assessment explanation & feedback generator | DONE | 2026-09-06 |
| ML-011 | FastAPI typed interface contracts | DONE | 2026-09-06 |
| TEST-ML | 70 Automated Tests (10/10 PASS) + 50 Manual Tests | DONE | 2026-09-06 |

### Backend (Utkarsh)

| Task ID | Description | Status | Last updated |
|---|---|---|---|
| DB-001 | Database models + first migration | PENDING | |
| API-001 | Auth endpoints (register/login) | PENDING | |
| API-002 | Competency state endpoint | PENDING | |
| BE-001 | Competency Engine (evidence fusion) | PENDING | |
| BE-002 | Orchestrator + 3 agents | PENDING | |
| *(add rows as needed)* | | | |

### Frontend (Frontend owner)

| Task ID | Description | Status | Last updated |
|---|---|---|---|
| FE-001 | Login page | PENDING | |
| FE-002 | Competency dashboard (mock data) | PENDING | |
| FE-003 | Assessment flow UI | PENDING | |
| FE-004 | Real API integration (mock → real) | PENDING | |
| UI-001 | Admin dashboard | PENDING | |
| *(add rows as needed)* | | | |

### Cross-cutting

| Task ID | Description | Status | Last updated |
|---|---|---|---|
| TEST-001 | Day 1 integration checkpoint (Build Guide §16) | PENDING | |
| TEST-002 | Day 2 integration checkpoint | PENDING | |
| TEST-003 | Day 3 — 5 consecutive clean demo runs | PENDING | |
| DEMO-001 | Demo script rehearsed | PENDING | |
| DEMO-002 | Backup demo video recorded | PENDING | |
| DOC-001 | Final README / evidence package (Build Guide §38) | PENDING | |

---

## 4. Component Status Mapping (from Build Guide §21, now with live status)

| Component | Design Status | Owner | Current Status | Last Updated |
|---|---|---|---|---|
| Authentication | CORE MVP | Utkarsh | PENDING | |
| Officer Profile | CORE MVP | Frontend owner | PENDING | |
| Competency Graph | CORE MVP | Utkarsh | PENDING | |
| Competency Engine | CORE MVP | Utkarsh | PENDING | |
| Evidence Engine | CORE MVP | Utkarsh | PENDING | |
| Diagnostic Agent | CORE MVP | Ankit | PENDING | |
| Adaptive Assessment | ENHANCEMENT | Ankit | PENDING | |
| Intervention Agent | CORE MVP | Ankit | PENDING | |
| Monitoring Agent | CORE MVP | Utkarsh | PENDING | |
| RAG Chatbot | ENHANCEMENT | Ankit | PENDING | |
| Document Ingestion | CORE MVP | Ankit | PENDING | |
| MCQ Generation | CORE MVP | Ankit | PENDING | |
| MCQ Validation | CORE MVP | Ankit | PENDING | |
| Content-to-Competency Mapping | CORE MVP | Ankit | PENDING | |
| Virtual Lab (Scenario Task A) | ENHANCEMENT | Frontend owner | PENDING | |
| Admin Dashboard | CORE MVP | Frontend owner | PENDING | |
| Agent Activity Timeline | ENHANCEMENT | Frontend owner | PENDING | |
| iGOT/NSSTA/TPAC Adapters | RESEARCH CANDIDATE | Utkarsh | PENDING | |

> Design Status (CORE MVP / ENHANCEMENT / RESEARCH CANDIDATE) comes from the frozen plan and doesn't change. Current Status is the only column you update here.

---

## 5. Integration Checkpoints

### Day 1 Checkpoint (Build Guide §16)
```
☐ Frontend: Login page renders
☐ Frontend: Dashboard shows fake data
☐ Frontend: Deployed on Vercel (URL works)
☐ Backend: /docs page shows all endpoints
☐ Backend: Register + Login works
☐ Backend: Deployed on Render (URL works)
☐ Backend: CORS is enabled
☐ ML: PDF → text extraction works
☐ ML: generate_mcqs() returns valid MCQs via Groq
☐ ML: ChromaDB has at least 1 document embedded
☐ INTEGRATION: Frontend can call backend API ← MOST IMPORTANT
☐ INTEGRATION: Backend can call ML function
☐ GIT: Today's work is pushed to the main repo (UtkarshSingh-09/GyanSetu-), not just the private repo
```
**Result:** [ PASS / PARTIAL / FAIL ] — **Notes:**

### Day 2 Checkpoint
```
☐ Full flow: Login → Profile → Assessment → Result → Recommendation
☐ Competency state updates after assessment
☐ Chatbot answers questions
☐ Document upload generates MCQs
☐ Admin dashboard shows aggregate data
☐ No API errors in browser console
```
**Result:** [ PASS / PARTIAL / FAIL ] — **Notes:**

### Day 3 Checkpoint (Pre-Demo)
```
☐ Demo flow works 5 consecutive times without errors
☐ Backup data prepared (pre-generated MCQs, cached chatbot answers)
☐ Demo video recorded as backup
☐ All 3 owners have reviewed the final product
```
**Result:** [ PASS / PARTIAL / FAIL ] — **Notes:**

---

## 6. Blockers Log

| # | Blocker | Raised by | Raised on | Status | Resolution |
|---|---|---|---|---|---|
| 1 | *(example)* Groq free-tier rate limit hit during batch MCQ generation | Ankit | | Open | |

---

## 7. Cut Log

Anything intentionally dropped from scope, per the Priority Stack cut order in `PROJECT_CONTEXT.md` §3. This is what you show a judge instead of a silent gap: "we made a deliberate call."

| # | Feature cut | Priority Stack tier | Reason | Date |
|---|---|---|---|---|
| *(example)* | Advanced adaptive assessment (difficulty + subskill) | Tier 8 (Advanced Research) | Time — core loop took priority | |

---

## 8. Decisions Log (lightweight version of Build Guide §29)

| Decision ID | Date | Decision | Why |
|---|---|---|---|
| DEC-001 | | | |

---

## 9. Reproducibility Run Log (Build Guide §31 — 5 consecutive runs before demo)

| Run # | Date/Time | Result | Failures (if any) |
|---|---|---|---|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

All 5 must pass before you consider the demo safe.

---

## 10. How to Update This File

1. At the **start** of a session: read the Quick Dashboard and Blockers Log so you know what's actually true before you start coding.
2. At the **end** of a session: update your track's Task Board rows, the Quick Dashboard, and the header. If you found something broken that isn't yours to fix, add it to the Blockers Log and mention it in the group chat — don't just leave it for someone to discover later.
3. At the **end of each day**: fill in the relevant Integration Checkpoint and write a `HANDOFF.md` entry.
4. If you cut a feature: log it in the Cut Log immediately, not retroactively on Day 3.
