> ## ⚠️ OPERATING REALITY PATCH — READ THIS BEFORE ANYTHING BELOW
>
> **This patch is the only part of this file that is allowed to change.** Everything below the horizontal rule at the end of this patch is the original, frozen Build Guide exactly as originally written. It is **still the correct architecture, tech design, day-by-day plan, and engineering-rigor reference** — nothing about *what* to build has changed. What changed is *who* is building it, *which LLM provider* it calls, and *which repo* the code lands in. Do not bulk-edit the frozen body of this document to "fix" the three items below — that is explicitly against Change Control (§22). Corrections live here and in the three companion files this patch points to.
>
> **Start at `PROJECT_CONTEXT.md`, not here, if this is your first time opening this project.** This patch is a summary for people already mid-document; `PROJECT_CONTEXT.md` is the full onboarding flow.
>
> ---
>
> ### PATCH 1 of 3 — Team: 3 solo owners, not 3 pairs of 6
>
> This guide was written assuming 6 builders in 3 pairs. The team actually executing is **3 people, each solo-owning what used to be a pair's combined scope.**
>
> | Wherever this guide says... | Read it as... | GitHub handle |
> |---|---|---|
> | "Aarth & Devraj" / "Aarth" / "Frontend pair" | The one Frontend owner | *(TBD — see `PROJECT_CONTEXT.md` §0)* |
> | "Mounya & Utkarsh" / "Mounya" / "Backend pair" | Utkarsh (Backend owner) | `UtkarshSingh-09` |
> | "Likhita & Ankit" / "Likhita" / "ML/AI pair" | Ankit Choubey (ML/AI owner) | `ankit-choubey` |
> | "all 6 builders" / "all 6 members" | All 3 owners | — |
> | Any pair peer-review step (§7's "Lightweight Peer-Review Workflow", §7's account of who reviews whom) | The Solo Builder Self-Review Checklist in `HANDOFF.md` §1 — there is no peer to review your code, so the checklist replaces the peer | — |
>
> This is a **read-time mental substitution, not a find-and-replace task.** Nobody needs to go through 500+ name mentions in this file and edit them. The full rationale, the reason only 3 names appear instead of 6, and the scope-cut consequence of going from pair-speed to solo-speed live in `PROJECT_CONTEXT.md` §0 and §3 — read those before you assume you have to finish 100% of any given day's task list.
>
> ---
>
> ### PATCH 2 of 3 — LLM provider: Groq, not Gemini
>
> Every mention of **Gemini** in this document (Tech Stack table, 4-Tier Fallback Hierarchy, Debugging & Troubleshooting, Fallback Plans, Common Mistakes, Glossary — 20 mentions total) should be read as **Groq**. Specifically:
>
> | This guide says... | Read it as... |
> |---|---|
> | "Google Gemini API" / "Gemini API" / "Gemini" | **Groq API** — an OpenAI-compatible chat completions endpoint at `https://api.groq.com/openai/v1`, running open-weight models (Llama, GPT-OSS, Qwen) on Groq's LPU hardware |
> | `.env` variable `GEMINI_API_KEY` | `.env` variable **`GROQ_API_KEY`** |
> | "Tier 1: LIVE LLM (Gemini API)" in the 4-Tier Fallback Hierarchy (§3) | "Tier 1: LIVE LLM (**Groq** API)" — Tiers 2–4 (validated cache → curated question bank → deterministic rule response) are **unchanged** |
> | Any specific Gemini model name you might have expected (there weren't any hardcoded in this guide, but if a coding agent invents one) | Use the model IDs pinned in `ENVIRONMENT_SETUP.md` §3 — do not guess a model name |
>
> **Everything else about the ML/AI architecture is unchanged:** LangChain, ChromaDB, PyMuPDF, python-pptx, local Whisper, local Sentence Transformers, scikit-learn, the MCQ validation pipeline, the grounding rules, the "never fall back to ungrounded generation" rule — none of that moved. Only the live LLM generation calls move providers. Full setup steps, account creation, exact model IDs, and current free-tier limits: `ENVIRONMENT_SETUP.md` §3.
>
> ---
>
> ### PATCH 3 of 3 — Git: two repos, two accounts, not one shared repo
>
> §7's "GitHub & Version Control Checkpoints" and the "How to Push to GitHub" steps (originally: one shared repo, feature branches, PR into `main`) are superseded by a **two-repo, two-account model**:
>
> * **Private repo** — `https://github.com/ankit-choubey/GyanSetu_V1.git` — pre-hackathon scaffolding, solo practice, throwaway experiments. Not judged.
> * **Main repo** — `https://github.com/UtkarshSingh-09/GyanSetu-.git` — the repo actually built in during the 3-day hackathon window and submitted for judging.
>
> The underlying engineering discipline this guide asks for — branch before you touch shared code, commit messages tied to Task IDs, `git revert` instead of force-fixing a broken `main`, CI gates before merge — **all of that still applies, just inside the main repo, on hackathon day.** Full command-by-command setup (multi-account auth, `.gitignore`, migrating scaffolding out of the private repo cleanly, secrets hygiene, branch strategy for 3 solo owners): `GIT_WORKFLOW.md`.
>
> ---
>
> ### Everything below this line is the original, frozen Build Guide.

---
# GyanSetu — Complete Build Guide & Workflow

> **Builders (Frontend):** Aarth & Devraj
> **Builders (Backend):** Mounya & Utkarsh
> **Builders (ML/AI):** Likhita & Ankit Choubey
> **Timeline:** 3 Working Days | Free Tier Only | Agentic IDE Access
> **Last Updated:** September 2026

---

# TABLE OF CONTENTS

### PART I: Core System, Implementation & Workflow
1. [What Is GyanSetu? (Plain English)](#1-what-is-gyansetu-plain-english)
2. [What Are We Actually Building?](#2-what-are-we-actually-building)
3. [Tech Stack — Final Decision](#3-tech-stack--final-decision)
4. [Complete System Architecture](#4-complete-system-architecture)
5. [The Full Workflow — Start to End](#5-the-full-workflow--start-to-end)
6. [Who Builds What — Team Ownership](#6-who-builds-what--team-ownership)
7. [How The 3 Pairs Connect](#7-how-the-3-pairs-connect)
8. [Day-by-Day Build Plan (3 Days)](#8-day-by-day-build-plan-3-days)
9. [Frontend Guide (Aarth & Devraj)](#9-frontend-guide-aarth--devraj)
10. [Backend Guide (Mounya & Utkarsh)](#10-backend-guide-mounya--utkarsh)
11. [ML/AI Guide (Likhita & Ankit)](#11-mlai-guide-likhita--ankit)
12. [API Contract — How Frontend Talks to Backend](#12-api-contract--how-frontend-talks-to-backend)
13. [Debugging & Troubleshooting](#13-debugging--troubleshooting)
14. [Fallback Plans — When Things Break](#14-fallback-plans--when-things-break)
15. [What Breaks If You Skip Something](#15-what-breaks-if-you-skip-something)
16. [Verification Checklist — How to Know It Works](#16-verification-checklist--how-to-know-it-works)
17. [Contact Matrix — Who to Ask When Stuck](#17-contact-matrix--who-to-ask-when-stuck)
18. [Common Mistakes to Avoid](#18-common-mistakes-to-avoid)
19. [Demo Script — What the Judge Sees](#19-demo-script--what-the-judge-sees)
20. [Glossary — Hard Words Made Simple](#20-glossary--hard-words-made-simple)

---
### PART II: Engineering, Evaluation & Execution Rigor
21. [Formal Status System & Sprint Truth](#21-formal-status-system--sprint-truth)
22. [Final Architecture Freeze & Change Control](#22-final-architecture-freeze--change-control)
23. [Priority Stack & Final Engineering Priorities](#23-priority-stack--final-engineering-priorities)
24. [Evaluation Integrity and Anti-Circularity](#24-evaluation-integrity-and-anti-circularity)
25. [Lightweight Experiment Framework & Registry](#25-lightweight-experiment-framework--registry)
26. [Evidence & Artifact Requirements](#26-evidence--artifact-requirements)
27. [Claim Integrity & The Final "Do Not Claim" List](#27-claim-integrity--the-final-do-not-claim-list)
28. [Data, Content, Model & Prompt Version Provenance](#28-data-content-model--prompt-version-provenance)
29. [Decision Audit Trail](#29-decision-audit-trail)
30. [Security Rules & Server-Side Authorization](#30-security-rules--server-side-authorization)
31. [Reproducibility Requirements & 5-Run Verification](#31-reproducibility-requirements--5-run-verification)
32. [End-to-End System Gates](#32-end-to-end-system-gates)
33. [Performance Accountability](#33-performance-accountability)
34. [Technology Adoption Gate](#34-technology-adoption-gate)
35. [Independent Technical Review](#35-independent-technical-review)
36. [Antigravity Implementation Rules](#36-antigravity-implementation-rules)
37. [Cloud / Local Execution Rule](#37-cloud--local-execution-rule)
38. [Final Evidence Package](#38-final-evidence-package)
39. [Final Engineering Checklist (ENG-01 to ENG-28)](#39-final-engineering-checklist)
40. [Competency-Engine Evaluation Ladder (E0 to E4)](#40-competency-engine-evaluation-ladder)
41. [RAG, Content Ingestion & Adaptive-Assessment Evaluation](#41-rag-content-ingestion--adaptive-assessment-evaluation)
42. [Retention, Recommendation & Multilingual Architecture](#42-retention-recommendation--multilingual-architecture)
43. [Complete Failure Taxonomy (G1 to G16) & Closed-Loop Metrics](#43-complete-failure-taxonomy-g1-to-g16--closed-loop-metrics)
44. [API Contract Governance & Normalized Adapter Contracts](#44-api-contract-governance--normalized-adapter-contracts)
45. [Task Reporting, CI Quality Gates & Step 6 Handoff](#45-task-reporting-ci-quality-gates--step-6-handoff)

---

# 1. What Is GyanSetu? (Plain English)

GyanSetu is **NOT another learning website** where government employees just watch courses and get a certificate.

GyanSetu is:
> **An extensible, evidence-driven competency intelligence and capability platform for India's Official Statistical workforce.**

The central product object is:
> **Competency state — not course completion.**

### The Definitive GyanSetu Closed Loop
```text
ROLE
 ↓
REQUIRED COMPETENCY
 ↓
CURRENT EVIDENCE
 ↓
COMPETENCY STATE
 ↓
GAP + UNCERTAINTY
 ↓
PRIORITY
 ↓
NEXT BEST ACTION
 ↓
iGOT / NSSTA / TPAC / PRACTICE / LAB
 ↓
LEARNING
 ↓
ASSESSMENT
 ↓
NEW EVIDENCE
 ↓
COMPETENCY UPDATE
 ↓
VERIFICATION
 ↓
RETENTION
 ↓
WORKFORCE INTELLIGENCE
```

Think of the contrast with legacy LMS platforms:

```text
Regular LMS: "You completed 14 courses. Good job."

GyanSetu:    "For your role as Junior Statistical Officer (JSO):
             - Estimated mastery in Sampling Design is 0.52 (Confidence: Medium, Evidence: 2 assessments).
             - Highest-confidence actionable gap: Variance Estimation in Stratified Sampling.
             - Recommended Next Best Action: NSSTA Practical Task on Neyman Allocation.
             - Post-intervention assessment will generate new application evidence.
             - Retention verification will be evaluated after an appropriate delay."
```

### Exact Gap Language
Avoid hand-waving claims like *"AI magically knows your exact weakness."*  
Use defensible, precise phrasing:  
> **"The system identifies the highest-confidence actionable subskill gap supported by the available evidence (e.g., Variance Estimation in Stratified Sampling)."**

### Retention Demonstration Principle
Retention inherently requires an **appropriate delay** to be scientifically meaningful. We do not pretend during a 10-minute presentation that the team waited seven real days.  
In the hackathon demonstration, retention verification is demonstrated honestly via:  
`[REPLAY — HISTORICAL SANDBOX EVENT]` or `[SANDBOX DATA]` badges.

### The One-Liner for Judges

> "iGOT gives you courses. GyanSetu identifies your highest-confidence competency gaps, delivers targeted interventions, proves whether you learned with validated evidence, and verifies retention over time."

---

# 2. What Are We Actually Building?

For the SIH MVP (Minimum Viable Product — the smallest version that still shows the full idea), we need these pieces:

```text
PIECE 1: Frontend (Next.js 14+ / Aarth & Devraj)
├── Secure Login & Role-Based Profile (JSO, SSO, Director)
├── Competency Dashboard (Mastery estimate, confidence, coverage, recency, diversity)
├── Diagnostic Assessment UI (Adaptive quiz, immediate feedback)
├── Explainable Next-Best-Action Card (12 reasoning fields)
├── Practical Task UI (Progressive 3-tier task: Scenario-Based Type A)
├── Admin Workforce Intelligence (Aggregated competency radar, no autonomous HR decisions)
├── Multilingual UI (Externalized strings supporting English + Hindi initial)
├── Virtual Assistant UI (Grounded RAG chatbot with citation & abstention)
└── Agent Activity Timeline (Audit trail of autonomous decisions)

PIECE 2: Backend (FastAPI + SQLModel / Mounya & Utkarsh)
├── Server-Side RBAC & Auth (/api/v1/ protected endpoints)
├── Competency Graph Engine (Roles → Competencies → Subskills)
├── Multi-Source Evidence Engine (Fuses 6 distinct evidence types; No evidence ≠ Low competency)
├── Orchestrator (Coordinates Diagnostic, Intervention, Monitoring agents)
├── Normalized Provider Adapters (iGOT, NSSTA, TPAC with LIVE/SANDBOX/REPLAY modes)
├── Assessment Bank Service (Pre-generated & validated question bank)
├── Safe State Engine (Atomic updates; no partial writes on DB failure)
└── Lightweight Decision Audit Logger

PIECE 3: ML/AI Pipeline (LangChain + Gemini / Likhita & Ankit)
├── Document Ingestion (PyMuPDF, python-pptx with 9 failure handling categories)
├── Partial Extraction Tracker (Coverage percentage, missing page visibility)
├── Video Ingestion Pipeline (Video → Audio → ASR Whisper → Timestamped Transcript → Mapping)
├── Concept-to-Competency Mapper (Traceable mappings with confidence estimates)
├── MCQ Generation & Quality Governance (Factual grounding, single correct answer)
├── Distractor Validator (Plausible but demonstrably incorrect under stated assumptions)
├── 4-Tier LLM Fallback (LIVE LLM → VALIDATED CACHE → CURATED BANK → DETERMINISTIC FALLBACK)
└── Grounded RAG Service (Strict abstention fallback: "Insufficient verified information")
```

### Progressive Practical Task (Virtual Lab Clarification)
Arbitrary code execution sandboxes introduce severe infrastructure, latency, and security failure modes during hackathons. GyanSetu uses a clear 3-tier practical task model:
* **Practical Task Type A — Scenario-Based Practical Task (Core Prototype):**  
  Presents a statistical problem, dataset summary, methodology choices, result interpretations, and justification questions. System evaluates decision quality against a structured rubric. Generates **application/practical evidence** without arbitrary code execution.
* **Practical Task Type B — Structured Interactive Task (Enhancement):**  
  Uses controlled parameter sliders and interactive calculations on small controlled datasets.
* **Practical Task Type C — Executable Laboratory (Extension):**  
  Full Dockerized Python/R code execution sandbox. Only activated if infrastructure and security justify it.
> **Terminology Rule:** Never claim a scenario-based task is an "executable Python laboratory." Say: *"A scenario-based practical task provides application evidence without requiring arbitrary code execution."*

---

# 3. Tech Stack — Final Decision

> **Rule: Everything must work on FREE TIER. No paid APIs unless absolutely necessary.**

## Frontend — Aarth's Stack

| Tool | Why | Free Tier? |
|------|-----|-----------|
| **Next.js 14+ (App Router)** | React framework, easy routing, SSR for fast loading | ✅ Yes |
| **Tailwind CSS** | Fast styling, responsive, looks modern quickly | ✅ Yes |
| **Recharts / Chart.js** | For competency dashboards, radar charts, progress bars | ✅ Yes |
| **Framer Motion** | Smooth animations for the "wow" factor at demo | ✅ Yes |
| **Vercel** | Deploy the frontend for free | ✅ Yes (hobby tier) |

### What is Next.js?
Next.js is a framework (a pre-built project structure) built on top of React. It handles routing (moving between pages), server-side rendering (pages load faster because the server does some work before sending to the browser), and API routes. You write React components but get a lot of stuff for free.

### What is Tailwind CSS?
Instead of writing CSS files, you add classes directly to your HTML like `class="bg-blue-500 text-white p-4"`. It's faster to build with and keeps things consistent.

---

## Backend — Mounya's Stack

| Tool | Why | Free Tier? |
|------|-----|-----------|
| **FastAPI (Python)** | Fast, easy, auto-generates API docs, async support | ✅ Yes |
| **PostgreSQL** | Relational database — stores users, competencies, evidence | ✅ Yes (Supabase or Neon free tier) |
| **SQLAlchemy / SQLModel** | ORM — lets you use Python objects instead of raw SQL | ✅ Yes |
| **Alembic** | Database migrations — safely update your DB schema | ✅ Yes |
| **Redis** (optional) | Caching — makes frequent queries faster | ✅ Yes (Upstash free tier) |
| **Render / Railway** | Deploy the backend for free | ✅ Yes |

### What is FastAPI?
FastAPI is a Python web framework. You write Python functions and decorate them with `@app.get("/users")` or `@app.post("/assessment")` and they become API endpoints (URLs that the frontend can call to send/receive data). It automatically creates documentation at `/docs`.

### What is an ORM?
ORM = Object Relational Mapper. Instead of writing SQL like `SELECT * FROM users WHERE id=5`, you write Python like `User.get(id=5)`. SQLModel is the easiest one for FastAPI.

### What is a migration?
When you change your database structure (add a column, rename a table), Alembic creates a "migration file" that safely applies the change without losing existing data.

---

## ML/AI — Likhita's Stack

| Tool | Why | Free Tier? |
|------|-----|-----------|
| **Google Gemini API** | LLM for MCQ generation, concept extraction, chatbot | ✅ Yes (free tier. Treat rate limit as an operational constraint; demo relies on pre-generated validated cache) |
| **LangChain** | Framework to chain LLM calls with retrieval, prompts | ✅ Yes |
| **ChromaDB** | Vector database for document search (RAG) | ✅ Yes (local/embedded) |
| **PyMuPDF (fitz)** | PDF text extraction | ✅ Yes |
| **python-pptx** | PowerPoint text extraction | ✅ Yes |
| **Whisper (tiny/base)** | Speech-to-text for video transcription | ✅ Yes (local model) |
| **Sentence Transformers** | Text embeddings for similarity search | ✅ Yes (local model) |
| **scikit-learn** | For competency estimation model (simple ML) | ✅ Yes |

### What is an LLM?
Large Language Model. Think ChatGPT. It takes text in and produces text out. We use it to generate questions, extract concepts from documents, and power the chatbot. Gemini is Google's free one.

### What is RAG?
RAG = Retrieval Augmented Generation. Instead of the LLM making stuff up, we first SEARCH our documents for relevant chunks, then give those chunks to the LLM and say "answer based on THIS." This is how we ground the chatbot in actual training materials.

### What is a Vector Database?
Regular databases search by exact words. Vector databases convert text into numbers (vectors/embeddings) and search by MEANING. So "sampling design" would match "survey methodology" even though the words are different. ChromaDB is a simple one that runs locally.

### What is an Embedding?
An embedding converts text into a list of numbers (like [0.23, -0.45, 0.67, ...]) that captures the MEANING of the text. Similar meanings → similar numbers → we can find related content.

---

## Shared Tools

| Tool | Purpose |
|------|---------|
| **Git + GitHub** | Version control — everyone pushes code here |
| **Docker** (optional) | Containerization — makes "it works on my machine" problems go away |
| **Postman / Thunder Client** | Test API endpoints without the frontend |

### 4-Tier Fallback Hierarchy for LLM & Services
```text
Tier 1: LIVE LLM (Gemini API)
  ↓ (rate limit / network timeout / quota exhaustion)
Tier 2: VALIDATED CACHE (Pre-generated & validated response bank)
  ↓ (cache miss / offline demo mode)
Tier 3: CURATED QUESTION BANK (Hand-verified statistical assessment items)
  ↓ (unsupported query / document unavailable)
Tier 4: DETERMINISTIC FALLBACK (Rule-based explainable answer / "Insufficient verified information")
```

---

# 4. Complete System Architecture

This is the master diagram. Print this and stick it on your wall.

```
                        ┌─────────────────────────┐
                        │      FRONTEND (Aarth)    │
                        │      Next.js + Tailwind  │
                        │                          │
                        │  • Login/Profile         │
                        │  • Competency Dashboard  │
                        │  • Assessment UI         │
                        │  • Recommendations       │
                        │  • Virtual Lab           │
                        │  • Admin Dashboard       │
                        │  • Chatbot               │
                        │  • Agent Timeline        │
                        └────────────┬─────────────┘
                                     │
                              HTTP / REST API
                           (JSON back and forth)
                                     │
                        ┌────────────▼─────────────┐
                        │    BACKEND (Mounya)       │
                        │    FastAPI + PostgreSQL    │
                        │                           │
                        │  ┌─────────────────────┐  │
                        │  │    ORCHESTRATOR      │  │
                        │  │    (Routes requests) │  │
                        │  └──────────┬──────────┘  │
                        │             │              │
                        │  ┌──────────┼──────────┐   │
                        │  ↓          ↓          ↓   │
                        │ DIAG     INTERV     MONITOR │
                        │ AGENT    AGENT      AGENT   │
                        │  │          │          │    │
                        │  └──────────┼──────────┘   │
                        │             ↓              │
                        │  ┌─────────────────────┐   │
                        │  │ COMPETENCY ENGINE   │   │
                        │  │ (Evidence Fusion)    │   │
                        │  └─────────────────────┘   │
                        │             │              │
                        │     ┌───────┼───────┐      │
                        │     ↓       ↓       ↓      │
                        │   iGOT   NSSTA    TPAC     │
                        │  Adapter Adapter  Adapter   │
                        │  (sandbox mode)             │
                        │                             │
                        │          PostgreSQL          │
                        │   (users, evidence, etc.)    │
                        └────────────┬────────────────┘
                                     │
                              Internal API calls
                        (Python function calls / HTTP)
                                     │
                        ┌────────────▼─────────────┐
                        │     ML/AI (Likhita)       │
                        │     LangChain + Gemini    │
                        │                           │
                        │  • Document ingestion     │
                        │  • Concept extraction     │
                        │  • MCQ generation         │
                        │  • MCQ validation         │
                        │  • RAG chatbot            │
                        │  • Competency mapping     │
                        │  • Adaptive assessment    │
                        │                           │
                        │     ChromaDB (vectors)    │
                        └───────────────────────────┘
```

### How they connect:

1. **Frontend → Backend**: HTTP REST API calls. Aarth's Next.js app sends requests like `POST /api/assessment/submit` and gets back JSON responses.

2. **Backend → ML/AI**: Python function calls. Mounya imports Likhita's modules and calls them directly. Example: `from ml.mcq_generator import generate_mcqs`. Alternatively, Likhita can also expose her ML functions as FastAPI endpoints that Mounya calls internally.

3. **Backend → Database**: SQLModel ORM queries. Mounya's code talks to PostgreSQL through Python objects. All state updates are atomic; on DB failure, no partial competency state is written.

4. **ML/AI → Vector DB**: ChromaDB queries. Likhita's code searches for relevant document chunks when generating questions or answering chatbot queries.

### Security & Prompt-Injection Boundary
* All uploaded PDFs, PPTs, transcripts, and external API responses are treated as **UNTRUSTED DOMAIN CONTENT**.
* Untrusted content is parsed strictly as data and isolated from system prompts. It can never override system instructions, role permissions, or assessment grading rubrics.

---

# 5. The Full Workflow — Start to End

This is the complete flow of what happens when a government officer uses GyanSetu.

```
STEP 1: OFFICER LOGS IN
         │
         ↓
STEP 2: PROFILE IS LOADED
         • Name, designation, department, role
         • Past training history (if available)
         │
         ↓
STEP 3: SYSTEM FINDS REQUIRED COMPETENCIES
         • Looks up role in Competency Graph
         • Example: "Statistical Analyst" needs:
           - Sampling Design
           - Data Quality
           - Python for Analytics
           - Statistical Modelling
         │
         ↓
STEP 4: DIAGNOSTIC ASSESSMENT STARTS
         • Diagnostic Agent selects questions
         • Questions ADAPT based on answers
         • If you get easy ones right → harder ones
         • If you get them wrong → system identifies the weak subskill
         • 5-10 minutes, not a full exam
         │
         ↓
STEP 5: COMPETENCY STATE IS CALCULATED
         • Evidence Engine fuses all evidence:
           - Profile evidence (role, experience)
           - Assessment evidence (quiz scores)
           - Each competency gets:
             → Estimated Mastery (how good you are)
             → Confidence (how sure the system is)
             → Evidence Coverage (how much we've tested)
         │
         ↓
STEP 6: GAPS ARE IDENTIFIED AND PRIORITIZED
         • System finds: "Variance Estimation is weak"
         • Not just "Sampling is weak" — the SPECIFIC subskill
         • Priority = role importance × gap size × uncertainty
         │
         ↓
STEP 7: NEXT-BEST-ACTION IS RECOMMENDED
         • Intervention Agent evaluates options:
           - iGOT course on sampling?
           - NSSTA practical programme?
           - Virtual lab exercise?
         • Picks the BEST option based on gap type
         • Shows WHY it recommended this
         │
         ↓
STEP 8: LEARNER DOES THE LEARNING/PRACTICE
         • Takes the recommended course
         • OR does a virtual lab (practical task)
         • OR completes a scenario assessment
         │
         ↓
STEP 9: POST-ASSESSMENT
         • New assessment after learning
         • Tests the SAME subskill that was weak
         • Different questions, same competency
         │
         ↓
STEP 10: COMPETENCY STATE UPDATES
         • Evidence Engine recalculates
         • Dashboard shows: "Variance Estimation improved"
         • Confidence goes UP because more evidence exists
         │
         ↓
STEP 11: MONITORING AGENT WATCHES
         • Schedules a retention check (delayed re-test)
         • If learner forgets → re-intervene
         • If learner retains → mark as stable
         │
         ↓
STEP 12: WORKFORCE DASHBOARD
         • Admin sees aggregate view ([SANDBOX DATA]):
           "41% of the sandbox Statistical Officer sample shows a Python capability gap"
         • Helps plan training priorities based on verified capability gaps
```

### The Closed Loop (This Is the Innovation)

```text
    ┌──────────────────────────────────────────────────────────┐
    │                                                          │
    ↓                                                          │
  TEST ──→ FIND GAP ──→ NEXT BEST ACTION ──→ FIX ──→ RE-TEST ──┘
```

This closed loop NEVER stops. That's what makes it fundamentally different from "you completed a course, bye."

### Key Engineering Definitions for the Loop
1. **Real-Time Definition:**  
   *Real-time* means: Learner submits answer → Event recorded → Competency Engine recalculates state → Gap & uncertainty updated → Recommendation ranking re-evaluated → Dashboard refreshed instantly.  
   *Retention is inherently delayed; real-time does not mean instant forgetting prediction.*
2. **Competency Closure:**  
   Do not imply permanent mastery. Phrased as: *"The currently identified gap meets configured verification criteria based on available evidence."* State may decay over time.
3. **Learner Feedback:**  
   Feedback from learners or admins is **evidence, not automatic ground truth**. It is logged for structured review; one user complaint never automatically updates model weights.
4. **The Hero Moment:**  
   ```text
   BEFORE:       Subskill gap identified (Mastery: 0.42, Confidence: Low, Evidence Count: 1)
   INTERVENTION: Targeted NSSTA Practical Module completed
   NEW EVIDENCE: Validated application scenario passed (Score: 85%)
   AFTER:        Mastery updated to 0.74, Confidence updated to High, Evidence Coverage expanded.
   ```

---

# 6. Who Builds What — Team Ownership

## Aarth & Devraj — Frontend (Web Dev)

```
OWNS:
├── All UI pages and components
├── API integration (calling Mounya's endpoints)
├── State management (what data is loaded where)
├── Charts and visualizations
├── Responsive design
├── Animations and micro-interactions
├── Deployment on Vercel
└── UI/UX decisions

DOES NOT OWN:
├── Database design (that's Mounya)
├── AI logic (that's Likhita)
└── API design (decides with Mounya)
```

## Mounya & Utkarsh — Backend (FastAPI + Python)

```
OWNS:
├── FastAPI server setup
├── All API endpoints
├── Database schema design
├── Competency graph data structure
├── Evidence engine (competency calculation)
├── Orchestrator logic (routing to agents)
├── Agent logic (diagnostic, intervention, monitoring)
├── User authentication
├── Integration adapters (iGOT/NSSTA sandbox)
├── Deployment on Render/Railway
└── Connecting Likhita's ML code to API endpoints

DOES NOT OWN:
├── UI design (that's Aarth)
├── ML model training (that's Likhita)
└── LLM prompts (that's Likhita)
```

## Likhita & Ankit Choubey — ML/AI

```
OWNS:
├── Document ingestion pipeline (PDF/PPT → text)
├── Concept extraction from documents
├── MCQ generation pipeline
├── MCQ validation pipeline
├── Question quality scoring
├── RAG chatbot (retrieval + generation)
├── Content-to-competency mapping
├── Embedding model setup
├── ChromaDB vector store
├── LLM prompt engineering
└── Adaptive question selection algorithm

DOES NOT OWN:
├── API endpoints (that's Mounya)
├── Database design (that's Mounya)
└── UI (that's Aarth)
```

---

# 7. How The 3 Pairs Connect

This is the most important section. If you don't understand this, the project will break.

## Connection 1: Aarth (Frontend) ↔ Mounya (Backend)

```
HOW THEY TALK: REST API over HTTP

EXAMPLE:
Aarth's code:
  fetch("http://backend-url/api/users/profile", {
    method: "GET",
    headers: { "Authorization": "Bearer token123" }
  })

Mounya's code:
  @app.get("/api/users/profile")
  async def get_profile(current_user: User = Depends(get_current_user)):
      return {"name": "Officer A", "role": "Statistical Analyst", ...}

WHAT MOVES BETWEEN THEM: JSON data
  {
    "name": "Officer A",
    "role": "Statistical Analyst",
    "competencies": [
      {"name": "Sampling Design", "mastery": 0.72, "confidence": 0.85}
    ]
  }
```

### Rules for This Connection
1. **Agree on the API contract FIRST** (see Section 12)
2. Mounya should have endpoints ready (even with fake data) by end of Day 1
3. Aarth should use mock/fake data while Mounya builds the real endpoints
4. **CORS must be enabled** on Mounya's FastAPI server (see debugging section)

---

## Connection 2: Mounya (Backend) ↔ Likhita (ML/AI)

```
HOW THEY TALK: Direct Python imports OR internal HTTP calls

OPTION A — Direct Import (RECOMMENDED for 3-day sprint):
  # In Mounya's code
  from ml_pipeline.mcq_generator import generate_mcqs
  from ml_pipeline.chatbot import get_chatbot_response
  from ml_pipeline.document_processor import process_document

OPTION B — Separate ML Service (if Likhita deploys separately):
  # In Mounya's code
  import httpx
  response = await httpx.post("http://ml-service/generate-mcqs", json={...})
```

### Rules for This Connection
1. **Likhita must define clear function signatures** by end of Day 1
2. Example function signature:

```python
# Likhita writes this
def generate_mcqs(
    content: str,          # The text from the document
    competency: str,       # Which skill to test
    num_questions: int,    # How many MCQs to generate
    difficulty: str        # "easy" / "medium" / "hard"
) -> list[dict]:
    """
    Returns:
    [
        {
            "question": "What is stratified sampling?",
            "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
            "correct_answer": "B",
            "explanation": "...",
            "difficulty": "medium",
            "competency": "Sampling Design",
            "subskill": "Stratified Sampling",
            "source_reference": "Page 23, paragraph 2",
            "quality_score": 0.87
        }
    ]
    """
```

3. **Mounya calls Likhita's functions**, wraps them in API endpoints, and sends results to Aarth
4. **Likhita should NOT worry about API endpoints** — just write clean Python functions

---

## Connection 3: The Data Flow (All 3 Together)

```text
Step 1: Aarth & Devraj's UI shows "Upload Document" button
        → User uploads an official MoSPI curriculum PDF / guidelines

Step 2: Frontend sends file to Backend
        → POST /api/v1/content/upload (multipart/form-data)

Step 3: Mounya & Utkarsh's backend validates file, saves securely, calls ML pipeline
        → process_document(file_path) with 9 failure handling categories
        → Likhita & Ankit's code extracts text, checks extraction coverage, extracts concepts

Step 4: ML service calls MCQ generator with factual grounding & distractor checks
        → generate_mcqs(extracted_text, "Sampling Design", 5, "medium")
        → Stores validated items in the assessment bank / cache

Step 5: Backend commits validated items to PostgreSQL assessment bank

Step 6: Backend returns structured JSON response with extraction coverage metrics
        → { "status": "success", "mcqs_generated": 5, "coverage": 0.95 }

Step 7: Frontend displays: "5 MCQs generated & validated! Ready for assessment."
```

---

## Normalized Integration Adapter Contract (iGOT / NSSTA / TPAC)

All external learning providers normalize into this strict common resource model:
```json
{
  "provider": "igot",
  "resource_id": "crs_samp_01",
  "resource_type": "course",
  "title": "Stratified Sampling Fundamentals",
  "description": "Comprehensive module on stratification and allocation methods.",
  "competencies": ["Sampling Design"],
  "subskills": ["Stratified Sampling", "Variance Estimation in Stratified Sampling"],
  "prerequisites": ["Basic Probability"],
  "duration_minutes": 90,
  "modality": "online",
  "language": "en",
  "availability_status": "available",
  "source_mode": "SANDBOX",
  "provenance": {
    "source_type": "official_metadata",
    "source_reference": "MoSPI Training Calendar 2026"
  },
  "version": "RESOURCE-v001"
}
```
* **Provider Modes:** `LIVE`, `SANDBOX`, `REPLAY`.
* The Intervention Agent must **ONLY** rank and recommend resources returned by this adapter. It must never invent a course.

## Lightweight Peer-Review Workflow (For all 6 Builders)
To ensure stability without corporate bureaucracy, the 6 builders operate on clear pair-review rules:
* **No Direct Merges to `main`:** Every change is made in a feature branch.
* **Domain Pair Reviews:**
  * Aarth reviews Devraj's PRs (and vice-versa).
  * Utkarsh reviews Mounya's PRs (and vice-versa).
  * Ankit reviews Likhita's PRs (and vice-versa).
* **Cross-Team Approval:** Any PR modifying API contracts (`/api/v1/`) or database schemas requires sign-off from both Backend and Frontend.
* **Rollback Discipline:** If a merged commit breaks integration, immediately run `git revert <commit_hash>`. Never leave `main` in a broken state.

---

## What If Something Breaks in the Connection?

### Aarth can't reach Mounya's API

```
SYMPTOMS:
  - "Network Error" in browser console
  - CORS error (red text about "Access-Control-Allow-Origin")
  - Connection refused

FIXES:
  1. Check if Mounya's server is running
  2. Check the URL — is it http://localhost:8000 or the deployed URL?
  3. CORS fix — Mounya adds this to FastAPI:
     from fastapi.middleware.cors import CORSMiddleware
     app.add_middleware(
         CORSMiddleware,
         allow_origins=["*"],  # For development only!
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
  4. If still broken → Aarth contacts Devraj, Mounya contacts Utkarsh
```

### Mounya can't call Likhita's ML functions

```
SYMPTOMS:
  - ImportError: No module named 'ml_pipeline'
  - Function returns None or crashes
  - Gemini API returns error

FIXES:
  1. Check if Likhita's code is in the right folder
  2. Check if requirements are installed: pip install -r requirements.txt
  3. Check if .env has the GEMINI_API_KEY
  4. If Gemini rate limit hit → wait 60 seconds, or use cached responses
  5. If still broken → Mounya contacts Utkarsh, Likhita contacts Ankit
```

### Likhita's ML function gives bad results

```
SYMPTOMS:
  - MCQs have wrong answers
  - Questions don't make sense
  - Competency mapping is wrong
  - Quality score is always low

FIXES:
  1. Check the prompt — is it clear and specific?
  2. Check the input text — is the PDF extraction working?
  3. Add more validation rules
  4. Try a different prompt template
  5. If still broken → Likhita contacts Ankit
```

---

# 8. Day-by-Day Build Plan (3 Days)

## DAY 1 — Foundation Day (The Skeleton)

### Goal: By end of Day 1, all three pieces should be individually working

```
AARTH (Frontend):
  Morning:
    ☐ Initialize Next.js project with Tailwind
    ☐ Create folder structure (pages, components, utils)
    ☐ Build login page
    ☐ Build main layout with sidebar navigation
  Afternoon:
    ☐ Build competency dashboard page (with MOCK data)
    ☐ Build assessment page (with MOCK questions)
    ☐ Set up API utility function (fetch wrapper)
  Evening:
    ☐ Build admin dashboard skeleton
    ☐ Deploy to Vercel (even if incomplete)
  
  VERIFY: Can you see the login page and dashboard with fake data?
  PAIR CHECK: Aarth and Devraj verify the deployment together

MOUNYA (Backend):
  Morning:
    ☐ Initialize FastAPI project
    ☐ Set up PostgreSQL database (Supabase or Neon)
    ☐ Create database models:
      - User
      - Role
      - Competency
      - SubSkill
      - Evidence
      - CompetencyState
      - AssessmentItem
      - Intervention
    ☐ Run first migration with Alembic
  Afternoon:
    ☐ Create API endpoints:
      - POST /api/auth/login
      - POST /api/auth/register
      - GET /api/users/profile
      - GET /api/competencies/{role_id}
      - POST /api/assessment/submit
      - GET /api/dashboard/learner
    ☐ Add CORS middleware
    ☐ Seed database with sample competency data
  Evening:
    ☐ Test all endpoints with Postman/docs
    ☐ Deploy to Render/Railway
    ☐ Share API URL with Aarth

  VERIFY: Can you open /docs and see all endpoints? Can you register a user?
  PAIR CHECK: Mounya and Utkarsh verify the database schema and API design together

LIKHITA (ML/AI):
  Morning:
    ☐ Set up Python environment
    ☐ Get Gemini API key, test a simple call
    ☐ Build document ingestion:
      - PDF → text (PyMuPDF)
      - PPT → text (python-pptx)
    ☐ Test with a sample PDF
  Afternoon:
    ☐ Build MCQ generation function
      - Prompt engineering for Gemini
      - Structured output parsing (JSON)
      - Basic validation (correct answer exists, 4 options)
    ☐ Build concept extraction function
  Evening:
    ☐ Set up ChromaDB
    ☐ Build basic RAG pipeline (embed documents, search)
    ☐ Write clear function signatures for Mounya

  VERIFY: Can you give a PDF and get back 5 valid MCQs?
  PAIR CHECK: Likhita and Ankit verify MCQ quality and prompt engineering together
```

### Day 1 Integration Checkpoint (End of Day)

```
ALL 6 TEAM MEMBERS meet and verify:
  ☐ Aarth can call Mounya's API and get a response
  ☐ Mounya can call Likhita's function and get MCQs back
  ☐ Database has sample data
  ☐ Frontend shows SOMETHING (even with mock data)
  ☐ All three pieces are deployed/runnable
```

---

## DAY 2 — Integration Day (Connect Everything)

### Goal: By end of Day 2, the full loop should work end-to-end with real data

```
AARTH (Frontend):
  Morning:
    ☐ Replace ALL mock data with real API calls to Mounya
    ☐ Build assessment flow:
      - Start assessment → show questions → submit answers → show results
    ☐ Build competency state display (mastery, confidence, coverage bars)
  Afternoon:
    ☐ Build recommendation display (next-best-action card)
    ☐ Build chatbot UI (floating chat window)
    ☐ Build file upload component (for document ingestion)
  Evening:
    ☐ Build agent activity timeline
    ☐ Polish animations and micro-interactions
    ☐ Build admin dashboard charts (aggregate competency distribution)

  VERIFY: Can a user log in, take a test, see their gaps, and get a recommendation?
  PAIR CHECK: Aarth and Devraj verify full user flow together

MOUNYA (Backend):
  Morning:
    ☐ Implement Competency Engine:
      - Evidence fusion (combine assessment scores into mastery estimate)
      - Confidence calculation (more evidence = higher confidence)
      - Coverage tracking
    ☐ Implement Orchestrator:
      - When assessment submitted → calculate competency → find gaps
  Afternoon:
    ☐ Implement Diagnostic Agent logic:
      - Select next question based on current evidence
      - Stop when enough evidence collected
    ☐ Implement Intervention Agent logic:
      - Given a gap → rank available interventions
      - Return next-best-action with explanation
    ☐ Connect to Likhita's MCQ generation (real calls)
  Evening:
    ☐ Implement chatbot endpoint (calls Likhita's RAG)
    ☐ Implement document upload endpoint (calls Likhita's ingestion)
    ☐ Implement admin analytics endpoints
    ☐ Seed more realistic data

  VERIFY: Can you trigger the full flow via API calls?
  PAIR CHECK: Mounya and Utkarsh verify the competency calculation logic together

LIKHITA (ML/AI):
  Morning:
    ☐ Improve MCQ generation:
      - Add source grounding check
      - Add distractor validation
      - Add difficulty estimation
      - Add duplicate detection
    ☐ Build content-to-competency mapping
  Afternoon:
    ☐ Build adaptive question selection:
      - If learner gets easy right → pick harder
      - If learner gets hard wrong → identify weak subskill
    ☐ Improve RAG chatbot:
      - Better prompts
      - Source attribution ("Based on page 23...")
  Evening:
    ☐ Build MCQ quality scoring
    ☐ Build explanation generation for assessment results
    ☐ Test all functions end-to-end with Mounya's integration

  VERIFY: Are generated MCQs consistently correct and properly validated?
  PAIR CHECK: Likhita and Ankit verify validation pipeline and question quality together
```

### Day 2 Integration Checkpoint (End of Day)

```
THE FULL DEMO LOOP MUST WORK:
  ☐ Officer logs in → sees profile
  ☐ System shows required competencies for their role
  ☐ Officer takes diagnostic assessment (adaptive questions)
  ☐ System shows competency state with mastery + confidence
  ☐ System identifies specific gap and recommends action
  ☐ Officer can use chatbot to ask questions
  ☐ Admin can upload a document and MCQs are generated
  ☐ Admin dashboard shows aggregate competency data

IF ANY STEP BREAKS → fix it NOW, not tomorrow
```

---

## DAY 3 — Polish & Demo Day

### Goal: Make it demo-ready, beautiful, and bulletproof

```
AARTH (Frontend):
  Morning:
    ☐ Fix all UI bugs found during testing
    ☐ Add loading states, error states, empty states
    ☐ Polish the competency radar chart
    ☐ Add the "hero moment" transition:
      - Before: Gap shown
      - After: Gap improved (with animation)
    ☐ Mobile responsiveness check
  Afternoon:
    ☐ Build the virtual lab UI (even if simplified):
      - Show a statistical dataset
      - User selects a method
      - System evaluates their choice
    ☐ Add multilingual toggle (Hindi option — even if only labels)
    ☐ Final deploy to Vercel
  Evening:
    ☐ REHEARSE THE DEMO 5 consecutive times
    ☐ Fix any crashes found during rehearsal
    ☐ Take screenshots for documentation

  VERIFY: Does the demo flow work 5 consecutive times in a row without crashing?
  PAIR CHECK: Aarth and Devraj do the final review together

MOUNYA (Backend):
  Morning:
    ☐ Fix all API bugs found during testing
    ☐ Add Monitoring Agent logic:
      - After assessment → schedule retention check
      - Track intervention history
    ☐ Add better error handling to all endpoints
    ☐ Add API response validation
  Afternoon:
    ☐ Implement virtual lab evaluation endpoint
    ☐ Add workforce analytics:
      - Aggregate competency distribution by role
      - Top gaps across organization
    ☐ Add LIVE/SANDBOX/REPLAY labels to integration responses
  Evening:
    ☐ Load test with demo data
    ☐ Final deploy to Render/Railway
    ☐ Make sure nothing crashes during demo flow

  VERIFY: Can the demo flow run end-to-end 5 consecutive times without errors?
  PAIR CHECK: Mounya and Utkarsh do the final review together

LIKHITA (ML/AI):
  Morning:
    ☐ Fix any MCQ quality issues found during testing
    ☐ Add scenario-based questions (not just fact recall)
    ☐ Improve chatbot responses
    ☐ Add explanation quality
  Afternoon:
    ☐ Pre-generate a set of high-quality MCQs for demo
      (don't rely on live generation during demo — have backup)
    ☐ Pre-embed demo documents in ChromaDB
    ☐ Test chatbot with likely judge questions
  Evening:
    ☐ Final testing with Mounya
    ☐ Prepare backup data if APIs fail during demo
    ☐ Document all prompts used

  VERIFY: Do MCQs make sense? Does the chatbot give good answers?
  PAIR CHECK: Likhita and Ankit do the final ML review together
```

---

# 9. Frontend Guide (Aarth & Devraj)

## Workflow Diagram

```text
AARTH & DEVRAJ'S WORKFLOW
  ↓
Build UI Components & Layouts
  ↓
Integrate Mock Data APIs
  ↓
Replace with Real Backend APIs (from Mounya/Utkarsh)
  ↓
Polish Animations & Responsive Design
  ↓
Final Deployment to Vercel
```

## Project Structure

```
gyansetu-frontend/
├── app/
│   ├── layout.tsx              # Main layout with sidebar
│   ├── page.tsx                # Landing/login page
│   ├── dashboard/
│   │   └── page.tsx            # Learner dashboard
│   ├── assessment/
│   │   └── page.tsx            # Assessment flow
│   ├── lab/
│   │   └── page.tsx            # Virtual lab
│   ├── admin/
│   │   └── page.tsx            # Admin dashboard
│   └── api/                    # Next.js API routes (if needed)
├── components/
│   ├── CompetencyRadar.tsx     # Radar chart for competencies
│   ├── SkillGapCard.tsx        # Shows a single skill gap
│   ├── AssessmentQuestion.tsx  # Renders one MCQ
│   ├── RecommendationCard.tsx  # Shows next-best-action
│   ├── AgentTimeline.tsx       # Shows agent activity
│   ├── ChatBot.tsx             # Floating chatbot
│   └── Sidebar.tsx             # Navigation sidebar
├── utils/
│   ├── api.ts                  # API call helper functions
│   └── types.ts                # TypeScript type definitions
├── public/                     # Static files
├── tailwind.config.ts
├── next.config.js
└── package.json
```

## Key Design Principles

1. **Dark theme** — premium look, easier on eyes
2. **Glassmorphism** for cards (semi-transparent backgrounds with blur)
3. **Gradient accents** — use brand colors (deep blue → teal gradient)
4. **Micro-animations** on data changes (numbers should animate up/down)
5. **Loading skeletons** — never show a blank screen

## Aarth's Verification Steps

```
☐ 1. Open browser DevTools (F12) → Console tab
      No red errors? ✓

☐ 2. Network tab → check API calls
      All returning 200? ✓
      Any 404 or 500? Fix the URL or tell Mounya

☐ 3. Responsive check → resize browser to mobile width
      Nothing overflows? ✓

☐ 4. Login → Dashboard → Assessment → Result → Recommendation
      Full flow works without refresh? ✓

☐ 5. Deploy to Vercel → open on phone
      Works on mobile? ✓

☐ 6. Type invalid data → does the form show errors?
      Not crash? ✓
```

---

# 10. Backend Guide (Mounya & Utkarsh)

## Workflow Diagram

```text
MOUNYA & UTKARSH'S WORKFLOW
  ↓
Database Schema & Migrations
  ↓
Core API Endpoints (Auth, Profile)
  ↓
Integrate ML Functions (from Likhita/Ankit)
  ↓
Competency Engine & Agents Logic
  ↓
Final Deployment to Render/Railway
```

## Project Structure

```
gyansetu-backend/
├── app/
│   ├── main.py                 # FastAPI app entry point
│   ├── config.py               # Environment variables
│   ├── database.py             # Database connection
│   ├── models/
│   │   ├── user.py             # User model
│   │   ├── competency.py       # Competency, SubSkill models
│   │   ├── evidence.py         # Evidence model
│   │   ├── assessment.py       # AssessmentItem model
│   │   └── intervention.py     # Intervention model
│   ├── routers/
│   │   ├── auth.py             # /api/auth/* endpoints
│   │   ├── users.py            # /api/users/* endpoints
│   │   ├── competency.py       # /api/competency/* endpoints
│   │   ├── assessment.py       # /api/assessment/* endpoints
│   │   ├── content.py          # /api/content/* endpoints (upload)
│   │   ├── chatbot.py          # /api/chatbot/* endpoints
│   │   └── admin.py            # /api/admin/* endpoints
│   ├── services/
│   │   ├── orchestrator.py     # Routes to correct agent
│   │   ├── diagnostic_agent.py # Selects questions, identifies gaps
│   │   ├── intervention_agent.py # Recommends next action
│   │   ├── monitoring_agent.py # Tracks retention
│   │   └── competency_engine.py # Evidence fusion + mastery calculation
│   └── utils/
│       ├── security.py         # JWT auth
│       └── validators.py       # Input validation
├── ml_pipeline/                # Likhita's code goes here
│   ├── __init__.py
│   ├── document_processor.py
│   ├── mcq_generator.py
│   ├── concept_extractor.py
│   ├── chatbot.py
│   └── competency_mapper.py
├── migrations/                 # Alembic migrations
├── seed_data/                  # JSON files with sample data
├── requirements.txt
├── .env
└── Dockerfile (optional)
```

## Competency Engine — The Most Important Function

This is the brain of the system. It calculates the competency state.

### The 6 Distinct Evidence Types
Evidence must NEVER be collapsed into an undifferentiated number. Store each type explicitly:
1. `KNOWLEDGE_ASSESSMENT` (Multiple-choice diagnostic items)
2. `APPLICATION_SCENARIO` (Scenario-based practical tasks)
3. `PRACTICAL_TASK` (Interactive calculations or lab submissions)
4. `TRAINING_HISTORY` (Completed prior training records)
5. `SELF_REPORT` (Learner confidence survey)
6. `WORKPLACE_SIGNAL` (Supervisor feedback / task assignment metrics)

### Core Rules for Competency Engine:
1. **No Evidence ≠ Low Competency:** If an officer has no recorded evidence for a subskill, their mastery is **Unknown**, and confidence is **Zero**. Never assign a failing grade for lack of data.
2. **Conflicting Evidence Flagging:** If a learner scores 95% on knowledge MCQs but fails the scenario practical task, do not average them into mediocrity. Flag as `CONFLICTING_EVIDENCE` and request an application assessment.
3. **Safe Database Failure Handling:** If the database connection drops during an assessment submission, **NEVER write partial competency state**. Roll back the transaction, return a structured error, and keep the user in read-only sandbox mode.

```python
# app/services/competency_engine.py
# E0 = heuristic baseline (start here, NOT calibrated ground truth)

EVIDENCE_WEIGHTS = {
    "APPLICATION_SCENARIO": 0.35,  # Scenario-based practical decisions
    "PRACTICAL_TASK": 0.30,        # Controlled calculation / interactive task
    "KNOWLEDGE_ASSESSMENT": 0.20, # Validated diagnostic MCQs
    "TRAINING_HISTORY": 0.10,     # Verified iGOT/NSSTA completions
    "WORKPLACE_SIGNAL": 0.05,     # Supervisor verification
    "SELF_REPORT": 0.02           # Self-declared proficiency (lowest weight)
}

def calculate_competency_state(learner_id: str, competency_id: str) -> dict:
    """
    Combines multi-source evidence for a learner on a competency into a single state estimate.
    """
    evidence_list = get_evidence(learner_id, competency_id)

    if not evidence_list:
        return {
            "mastery": None,
            "confidence": 0.0,
            "coverage": 0.0,
            "evidence_count": 0,
            "evidence_diversity": 0,
            "message": "No evidence recorded. Status: Unassessed (Not low competency)."
        }

    # Weight evidence by recency and source reliability
    weighted_scores = []
    total_weight = 0.0
    for e in evidence_list:
        days_old = (now() - e.timestamp).days
        recency_weight = max(0.3, 1.0 - (days_old * 0.01))
        type_weight = EVIDENCE_WEIGHTS.get(e.evidence_type, 0.10)
        eff_weight = recency_weight * type_weight
        weighted_scores.append(e.score * eff_weight)
        total_weight += eff_weight

    mastery = sum(weighted_scores) / total_weight if total_weight > 0 else 0.0
    
    # Multidimensional confidence model (considers evidence volume + source diversity)
    evidence_count = len(evidence_list)
    distinct_types = len(set(e.evidence_type for e in evidence_list))
    diversity_bonus = min(0.20, distinct_types * 0.05)
    count_factor = min(0.50, evidence_count * 0.10)
    confidence = min(0.95, round(0.30 + count_factor + diversity_bonus, 2))
    
    coverage = len(set(e.subskill for e in evidence_list)) / total_subskills

    return {
        "mastery": round(mastery, 2),
        "confidence": round(confidence, 2),
        "coverage": round(coverage, 2),
        "evidence_count": evidence_count,
        "evidence_diversity": distinct_types,
        "last_assessed": max(e.timestamp for e in evidence_list),
        "status": "verified" if (mastery >= 0.70 and confidence >= 0.60) else "developing"
    }
```

### Lightweight Decision Audit Logger
Every state recalculation produces an immutable audit record:
```python
# app/services/audit_logger.py
import uuid
from datetime import datetime

def log_competency_decision(officer_id: str, subskill_id: str, old_state: dict, new_state: dict, trigger_event: str):
    audit_record = {
        "decision_id": f"DEC-{uuid.uuid4().hex[:8]}",
        "timestamp": datetime.utcnow().isoformat(),
        "officer_id": officer_id,
        "subskill_id": subskill_id,
        "trigger_event": trigger_event,
        "old_mastery": old_state.get("mastery"),
        "new_mastery": new_state.get("mastery"),
        "confidence": new_state.get("confidence"),
        "engine_version": "E0-Heuristic-v1"
    }
    return audit_record
```

> **If this function is wrong, EVERYTHING downstream is wrong.** The dashboard shows wrong data, the recommendations are wrong, the admin analytics are wrong. This is the ONE function that must be correct.

## Mounya's Verification Steps

```
☐ 1. Start the server: uvicorn app.main:app --reload
      No crash? ✓

☐ 2. Open http://localhost:8000/docs
      See all endpoints listed? ✓

☐ 3. Try POST /api/auth/register with test data
      Returns 201 Created? ✓

☐ 4. Try GET /api/competency/1
      Returns competency data? ✓

☐ 5. Try POST /api/assessment/submit with answers
      Returns competency state? ✓

☐ 6. Check database: SELECT * FROM users;
      Data is stored? ✓

☐ 7. Call from Aarth's frontend (different port/domain)
      CORS works? ✓
      No "blocked by CORS policy" error? ✓

☐ 8. Call Likhita's function directly:
      from ml_pipeline.mcq_generator import generate_mcqs
      result = generate_mcqs("test text", "Sampling", 3, "easy")
      Returns a list of dicts? ✓
```

---

# 11. ML/AI Guide (Likhita & Ankit)

## Workflow Diagram

```text
LIKHITA & ANKIT'S WORKFLOW
  ↓
Document Ingestion & Chunking
  ↓
Prompt Engineering (MCQs & Concepts)
  ↓
Validation Pipelines (Filter Bad MCQs)
  ↓
RAG Chatbot Setup (ChromaDB)
  ↓
Expose Clean Python Functions to Backend
```

## Project Structure

```
ml_pipeline/
├── __init__.py
├── document_processor.py      # PDF/PPT → text
├── concept_extractor.py       # Text → concepts
├── competency_mapper.py       # Concepts → competencies
├── mcq_generator.py           # Generate MCQs from text
├── mcq_validator.py           # Validate generated MCQs
├── chatbot.py                 # RAG chatbot
├── adaptive_selector.py       # Pick next question based on evidence
├── prompts/
│   ├── mcq_prompt.txt         # Prompt template for MCQ generation
│   ├── concept_prompt.txt     # Prompt template for concept extraction
│   └── chatbot_prompt.txt     # System prompt for chatbot
├── vector_store/
│   └── chroma_db/             # ChromaDB data directory
├── config.py                  # API keys, model settings
└── requirements.txt
```

## MCQ Generation Prompt (Critical)

The quality of MCQs depends almost entirely on this prompt. Get it wrong and the whole assessment system is useless.

```python
MCQ_PROMPT = """
You are an expert assessment designer for India's Official Statistical System.

Given the following training material excerpt, generate {num_questions} multiple-choice 
questions that test the competency: {competency}

Rules:
1. Each question MUST be answerable ONLY from the given text (no outside knowledge)
2. Each question MUST have exactly ONE correct answer (no hidden second correct answer, no ambiguous wording)
3. Distractors (wrong answers) must be PLAUSIBLE but demonstrably incorrect under the stated assumptions/source
4. Questions should test UNDERSTANDING, not just memorization
5. Include the specific source reference (which part of the text the answer comes from)
6. Rate difficulty as "easy", "medium", or "hard"
7. Map each question to a specific subskill

Training Material:
{content}

Output format (JSON array):
[
  {{
    "question": "...",
    "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
    "correct_answer": "B",
    "explanation": "...",
    "difficulty": "medium",
    "competency": "{competency}",
    "subskill": "...",
    "source_reference": "...",
    "cognitive_level": "application"
  }}
]

IMPORTANT: Output ONLY valid JSON. No markdown, no explanation before or after.
"""
```

### What Breaks If the Prompt Is Bad

| Problem | Cause | Fix |
|---------|-------|-----|
| MCQ has 2 correct answers | Prompt doesn't enforce "exactly ONE correct" | Add explicit constraint in prompt + validation |
| Answers not from the text | LLM hallucinating | Add "ONLY from the given text" + source check |
| All questions are too easy | No difficulty guidance | Add difficulty distribution requirement |
| Questions repeat concepts | No diversity requirement | Add "cover different subskills" instruction |
| JSON parsing fails | LLM adds text around JSON | Add "Output ONLY valid JSON" + strip non-JSON |

## MCQ Validation Pipeline

```python
def validate_mcq(mcq: dict, source_text: str) -> dict:
    """
    Validates a generated MCQ.
    Returns the MCQ with a quality_score and validation_status.
    """
    issues = []

    # Check 1: Does it have all required fields?
    required = ["question", "options", "correct_answer", "explanation"]
    for field in required:
        if field not in mcq:
            issues.append(f"Missing field: {field}")

    # Check 2: Exactly 4 options?
    if len(mcq.get("options", [])) != 4:
        issues.append("Must have exactly 4 options")

    # Check 3: Correct answer is one of the options?
    if mcq.get("correct_answer") not in ["A", "B", "C", "D"]:
        issues.append("Correct answer must be A, B, C, or D")

    # Check 4: Is the answer grounded in source text?
    # (Use embedding similarity to check if answer content
    #  is actually present in the source material)
    answer_text = mcq["options"][ord(mcq["correct_answer"])-ord("A")]
    similarity = compute_similarity(answer_text, source_text)
    if similarity < 0.3:
        issues.append("Answer may not be grounded in source material")

    # Check 5: Are distractors different enough from correct answer?
    # (If they're too similar, question is ambiguous)
    # ...

    quality_score = max(0, 1.0 - (len(issues) * 0.2))
    
    return {
        **mcq,
        "quality_score": quality_score,
        "validation_status": "pass" if quality_score >= 0.6 else "fail",
        "issues": issues
    }
```

### What Breaks If You Skip Validation

- **Bad MCQs enter the assessment bank** → learner's competency is estimated WRONG
- **Wrong competency estimation** → wrong gap identification → wrong recommendation
- **Wrong recommendation** → learner wastes time on the wrong thing
- **The entire closed loop becomes unreliable**

This is a chain reaction. One bad MCQ can corrupt the entire competency state.

### Psychometric Threshold Rule
> **Do NOT hard-code universal psychometric thresholds (e.g., p-value 0.30–0.85, discrimination > 0.30) before response data exists!**  
* **Before response data exists:** Rely on content validation, expert review, estimated difficulty, and grounding checks.
* **After sufficient response data exists:** Calculate empirical difficulty (p-value), point-biserial discrimination, and psychometric models (IRT). Step 6 determines the formal threshold criteria.

### Content Processing Failure Categories (9 Explicit Classes)
The ingestion pipeline must categorize document extraction results into 9 explicit states:
`UNSUPPORTED_FORMAT`, `CORRUPTED_FILE`, `EMPTY_CONTENT`, `OCR_FAILURE`, `ASR_FAILURE`, `PARTIAL_EXTRACTION`, `PROCESSING_TIMEOUT`, `MAPPING_FAILURE`, `UNKNOWN_PROCESSING_ERROR`.
* **Partial Extraction Visibility:** If a document is partially extracted, track: successful pages, failed pages, OCR used, coverage percentage. **If extraction coverage is insufficient, DO NOT generate trusted assessments.** The user must see an incomplete content warning.

### Video Ingestion Pipeline
```text
VIDEO FILE (.mp4) → AUDIO EXTRACTION → LOCAL WHISPER ASR → TIMESTAMPED TRANSCRIPT
→ STRUCTURING & CHUNKING → CONCEPT EXTRACTION → COMPETENCY MAPPING
```
Preserve timestamps for every extracted concept. If ASR transcript confidence is low, flag for review rather than generating ungrounded questions.

### Grounded RAG Failure & Strict Abstention
If ChromaDB is unavailable or retrieval produces chunks below the similarity threshold:
* **DO NOT fall back to direct Gemini generation without document grounding!**
* The chatbot must explicitly return: *"I don't have enough verified information in the official training materials to answer this question accurately."*

## Likhita's Verification Steps

```
☐ 1. Test PDF extraction:
      python -c "from document_processor import extract_text; print(extract_text('sample.pdf')[:200])"
      Returns readable text? ✓

☐ 2. Test MCQ generation:
      python -c "from mcq_generator import generate_mcqs; print(generate_mcqs('...', 'Sampling', 3, 'medium'))"
      Returns valid JSON list? ✓
      Each MCQ has all required fields? ✓
      Correct answers are actually correct? ✓ (CHECK MANUALLY)

☐ 3. Test RAG chatbot:
      python -c "from chatbot import ask; print(ask('What is stratified sampling?'))"
      Returns a coherent answer? ✓
      Cites a source? ✓

☐ 4. Test with 10 MCQs:
      - Are at least 8 out of 10 factually correct? ✓
      - Do the distractors make sense? ✓
      - Are sources referenced? ✓

☐ 5. Test with a real NSSTA/statistics document:
      MCQs are domain-relevant? ✓
      Not just generic trivia? ✓
```

---

# 12. API Contract — How Frontend Talks to Backend

**API Contract Rules:**
Every endpoint must specify: endpoint, HTTP method, authentication requirement, authorization requirement, request schema, response schema, error schema, success status code, failure status codes, example request, example response.

* **API version:** v1
* **Error Format:** Use structured JSON errors, e.g.:
```json
{
  "error": {
    "code": "ASSESSMENT_NOT_FOUND",
    "message": "Assessment does not exist",
    "request_id": "req_123"
  }
}
```
*Do not expose stack traces to frontend users.*

**Aarth and Mounya MUST agree on these endpoints before coding separately.**

## Authentication

```
POST /api/auth/register
  Body: { "email": "...", "password": "...", "name": "...", "role_id": 1 }
  Response: { "user_id": 1, "token": "jwt_token_here" }

POST /api/auth/login
  Body: { "email": "...", "password": "..." }
  Response: { "token": "jwt_token_here" }
```

## Profile

```
GET /api/users/profile
  Headers: { "Authorization": "Bearer <token>" }
  Response: {
    "id": 1,
    "name": "Officer A",
    "designation": "Statistical Analyst",
    "department": "MoSPI",
    "role": "Statistical Analyst",
    "experience_years": 5
  }
```

## Competency

```
GET /api/competency/state
  Headers: { "Authorization": "Bearer <token>" }
  Response: {
    "competencies": [
      {
        "id": 1,
        "name": "Sampling Design",
        "domain": "Statistical",
        "mastery": 0.72,
        "confidence": 0.85,
        "coverage": 0.6,
        "last_assessed": "2026-09-03",
        "gap": "Variance Estimation",
        "status": "needs_improvement"
      }
    ]
  }
```

## Assessment

```
GET /api/assessment/start?competency_id=1
  Response: {
    "assessment_id": "abc123",
    "questions": [
      {
        "id": "q1",
        "question": "What is stratified sampling?",
        "options": ["A. ...", "B. ...", "C. ...", "D. ..."],
        "difficulty": "medium",
        "competency": "Sampling Design",
        "subskill": "Stratified Sampling"
      }
    ]
  }

POST /api/assessment/submit
  Body: {
    "assessment_id": "abc123",
    "answers": [
      { "question_id": "q1", "selected": "B", "time_taken_seconds": 45 }
    ]
  }
  Response: {
    "score": 0.7,
    "competency_update": {
      "mastery_before": 0.65,
      "mastery_after": 0.72,
      "confidence_before": 0.5,
      "confidence_after": 0.75,
      "identified_gaps": ["Variance Estimation"],
      "next_best_action": {
        "type": "nssta_programme",
        "name": "Advanced Sampling Methods",
        "reason": "Addresses identified gap in variance estimation"
      }
    },
    "agent_activity": [
      { "agent": "Diagnostic", "action": "Uncertainty identified in Variance Estimation" },
      { "agent": "Competency Engine", "action": "Evidence state updated" },
      { "agent": "Intervention", "action": "NSSTA programme ranked highest" },
      { "agent": "Monitoring", "action": "Retention check scheduled in 7 days" }
    ]
  }
```

## Chatbot

```
POST /api/chatbot/ask
  Body: { "message": "What is stratified sampling?", "context": "assessment" }
  Response: {
    "reply": "Stratified sampling is a method where...",
    "sources": [
      { "document": "NSSTA Sampling Guide.pdf", "page": 23 }
    ]
  }
```

## Content Upload

```
POST /api/content/upload
  Body: FormData with file
  Response: {
    "content_id": "doc123",
    "status": "processing",
    "concepts_found": 12,
    "mcqs_generated": 5,
    "competencies_mapped": ["Sampling Design", "Data Quality"]
  }
```

## Admin Analytics

```
GET /api/admin/workforce
  Response: {
    "total_officers": 150,
    "competency_distribution": [
      { "competency": "Sampling Design", "avg_mastery": 0.68, "gap_count": 45 },
      { "competency": "Python", "avg_mastery": 0.82, "gap_count": 12 }
    ],
    "top_gaps": ["Data Quality", "AI/ML", "Statistical Modelling"],
    "training_effectiveness": {
      "improved_after_intervention": 72,
      "no_change": 18,
      "declined": 10
    }
  }
```

---

# 13. Debugging & Troubleshooting

## For Aarth (Frontend)

### Problem: "Page is blank / white screen"

```
STEP 1: Open browser console (F12 → Console)
STEP 2: Read the red error message
STEP 3: Common causes:
  - "Cannot read property of undefined" → You're trying to access
    data that hasn't loaded yet. Add a loading check:
    if (!data) return <LoadingSpinner />
  - "Module not found" → You forgot to install a package
    npm install <package-name>
  - "Hydration error" → Server and client rendered different HTML
    Wrap dynamic content in useEffect

STILL STUCK? → Contact Devraj with a screenshot of the console error
```

### Problem: "API call returns 404"

```
STEP 1: Check the URL. Is it /api/users/profile or /api/user/profile?
        One letter difference = broken.
STEP 2: Check if Mounya's server is running
STEP 3: Check if you're using the right base URL
        - Local: http://localhost:8000
        - Deployed: https://gyansetu-backend.onrender.com
STEP 4: Open Mounya's /docs page and check the exact endpoint path

STILL STUCK? → Contact Mounya and Devraj
```

### Problem: "CORS error"

```
WHAT IS CORS? Cross-Origin Resource Sharing. Browsers block requests from
one domain (your frontend) to another domain (your backend) unless the
backend explicitly allows it.

FIX: Mounya needs to add CORS middleware to FastAPI.
This is a BACKEND fix, not a frontend fix.

STILL STUCK? → Contact Mounya
```

---

## For Mounya (Backend)

### Problem: "Database connection failed"

```
STEP 1: Check your .env file:
        DATABASE_URL=postgresql://user:pass@host:5432/dbname
STEP 2: Is the database server running? (Supabase/Neon dashboard → check status)
STEP 3: Are the credentials correct? Copy-paste from the provider dashboard.
STEP 4: Is your IP whitelisted? Some providers require this.

STILL STUCK? → Contact Utkarsh
```

### Problem: "Migration failed"

```
STEP 1: alembic current  → shows current migration state
STEP 2: alembic heads    → shows latest migration
STEP 3: If out of sync:
        alembic stamp head  → force-set to latest
        alembic upgrade head → apply all pending
STEP 4: If table already exists:
        Drop the table manually (ONLY in development!)
        Re-run migration

STILL STUCK? → Contact Utkarsh
```

### Problem: "Likhita's function crashes when I call it"

```
STEP 1: Can you import it?
        python -c "from ml_pipeline.mcq_generator import generate_mcqs"
        If ImportError → check __init__.py files and folder structure

STEP 2: Does it work standalone?
        python -c "from ml_pipeline.mcq_generator import generate_mcqs; print(generate_mcqs('test', 'Sampling', 1, 'easy'))"
        If it works here but not in FastAPI → it's an async/sync issue

STEP 3: Is it a timeout?
        Gemini API calls can take 5-10 seconds. Use async:
        result = await asyncio.to_thread(generate_mcqs, ...)

STEP 4: Is the Gemini API key set?
        Check .env: GEMINI_API_KEY=your_key_here

STILL STUCK? → Contact both Likhita and Utkarsh
```

---

## For Likhita (ML/AI)

### Problem: "Gemini API returns error"

```
STEP 1: Check your API key. Go to Google AI Studio → verify key is active.
STEP 2: Rate limit hit? Free tier = 15 requests per minute.
        → Add time.sleep(4) between calls
        → Or batch your requests
STEP 3: "Safety filter" blocked the response?
        → Your prompt might contain something flagged
        → Rephrase the prompt to be more neutral
STEP 4: Model returns garbage / not JSON?
        → Add "Output ONLY valid JSON" to end of prompt
        → Try json.loads() in a try/except and retry on failure

STILL STUCK? → Contact Ankit
```

### Problem: "MCQs are wrong / bad quality"

```
STEP 1: Is the input text clean? Check document_processor output.
        - If text has formatting artifacts → clean them
        - If text is from a scan → OCR might have errors

STEP 2: Is the prompt specific enough?
        Bad:  "Generate questions from this text"
        Good: "Generate 3 medium-difficulty MCQs testing the competency
               'Sampling Design', specifically the subskill 'Stratified
               Sampling'. Each question must have exactly ONE correct
               answer derivable from the given text."

STEP 3: Is the context window too large?
        → Chunk the text into 1000-2000 character pieces
        → Generate MCQs per chunk

STEP 4: Run validation on every MCQ before storing.

STILL STUCK? → Contact Ankit
```

### Problem: "RAG chatbot gives wrong answers"

```
STEP 1: Check ChromaDB — are documents actually embedded?
        collection.count()  → should be > 0

STEP 2: Check retrieval — is the right chunk being found?
        results = collection.query(query_texts=["stratified sampling"], n_results=3)
        print(results["documents"])
        → Are these relevant chunks?

STEP 3: If wrong chunks → re-embed with better chunking
        → Chunks too big = diluted meaning
        → Chunks too small = missing context
        → Sweet spot: 500-1000 characters with 100 char overlap

STEP 4: If right chunks but wrong answer → improve the prompt:
        "Answer ONLY based on the following context. If the answer
         is not in the context, say 'I don't have enough information
         about this topic.'"

STILL STUCK? → Contact Ankit
```

---

# 14. Fallback Plans — When Things Break

| What Fails | Fallback | Who Fixes |
|------------|----------|-----------|
| **Gemini API down / 429 quota** | Follow 4-tier hierarchy: Check validated cache → Curated question bank in DB → Deterministic rule response. Zero live LLM calls required. | Likhita (pre-generates & validates demo bank on Day 2) |
| **ChromaDB crashes / unavailable** | Fall back to keyword/structured document search. If unavailable, return *"Insufficient verified information in official sources."* **NEVER fall back to ungrounded Gemini generation.** | Ankit |
| **Database down / connection fails** | Read-only sandbox mode using local seeded JSON data. Abort all state writes safely; never write partial competency states. | Mounya & Utkarsh |
| **iGOT / NSSTA API unavailable** | Adapter automatically switches `source_mode` to `SANDBOX` or `REPLAY`. | Utkarsh |
| **Vercel deploy fails** | Run frontend locally: `npm run dev` on a laptop (localhost:3000) | Aarth & Devraj |
| **Render deploy fails** | Run backend locally: `uvicorn app.main:app --port 8000` on a laptop | Mounya & Utkarsh |
| **MCQ generation produces poor items** | Use the pre-validated question bank for the live demo. Show generation pipeline in sandbox mode. | Likhita & Ankit |
| **Internet down at demo venue** | Platform is 100% local/offline capable: embedded ChromaDB, local Whisper, seeded PostgreSQL, cached assessment items. | All 6 builders |
| **One person gets sick / absent** | Pair programming model ensures paired co-owner can run and explain every subsystem. | All 3 pairs |

### The Golden Rule of Fallbacks

> **Always have a backup for the demo. If it CAN fail during the presentation, it WILL fail.**

Pre-record a video of the full working flow on Day 2 evening as the ultimate backup.

---

# 15. What Breaks If You Skip Something

This section explains the chain reactions. Read this carefully.

### If you don't build the Competency Engine properly...

```
Competency Engine (broken)
    → Wrong mastery scores on dashboard
    → Wrong gap identification
    → Wrong recommendations
    → Useless admin analytics
    → Judge sees: "This doesn't actually work"
```

**Impact: CRITICAL. This is the #1 priority for Mounya.**

---

### If you don't validate MCQs...

```
Unvalidated MCQs
    → MCQ has wrong correct answer
    → Learner's evidence is corrupted
    → Competency state is wrong
    → System recommends wrong intervention
    → Entire closed loop is unreliable
```

**Impact: CRITICAL. This is the #1 priority for Likhita.**

---

### If the frontend doesn't show confidence/uncertainty...

```
No confidence display
    → Judge thinks we're claiming certainty
    → "How do you KNOW this officer is 68% competent?"
    → We can't defend the claim
    → We look like every other generic platform
```

**Impact: HIGH. This is what makes us DIFFERENT from other teams.**

---

### If you skip the agent activity timeline...

```
No agent timeline
    → Judge doesn't see the AI agents working
    → Platform looks like a regular dashboard
    → We lose the "agentic AI" differentiator
```

**Impact: MEDIUM. This is a visual differentiator for the demo.**

---

### If you skip the admin dashboard...

```
No admin dashboard
    → "Where's the workforce intelligence?"
    → Missing a PS requirement
    → Judge marks us down for incomplete solution
```

**Impact: HIGH. This is explicitly required by the problem statement.**

---

### If you don't add CORS on the backend...

```
No CORS
    → Frontend literally cannot call the backend
    → NOTHING works
    → Demo is dead
```

**Impact: IMMEDIATE BLOCKER. Add this in the first 5 minutes of Day 1.**

---

# 16. Verification Checklist — How to Know It Works

## End-of-Day Verification (All 6 People Together)

### Day 1 Checkpoint

```
☐ Frontend: Login page renders
☐ Frontend: Dashboard shows fake data
☐ Frontend: Deployed on Vercel (URL works)
☐ Backend: /docs page shows all endpoints
☐ Backend: Register + Login works
☐ Backend: GET /api/competency/state returns data
☐ Backend: Deployed on Render (URL works)
☐ Backend: CORS is enabled
☐ ML: PDF → text extraction works
☐ ML: generate_mcqs() returns valid MCQs
☐ ML: ChromaDB has at least 1 document embedded
☐ INTEGRATION: Frontend can call backend API ← MOST IMPORTANT
☐ INTEGRATION: Backend can call ML function
```

### Day 2 Checkpoint

```
☐ Full flow: Login → Profile → Assessment → Result → Recommendation
☐ Competency state updates after assessment
☐ Agent timeline shows activity
☐ Chatbot answers questions
☐ Document upload generates MCQs
☐ Admin dashboard shows aggregate data
☐ No API errors in browser console
☐ All deployments are updated
```

### Day 3 Checkpoint (Pre-Demo)

```
☐ Demo flow works 5 consecutive times in a row without errors
☐ Virtual lab is functional (even if simplified)
☐ Backup data is prepared (pre-generated MCQs, cached responses)
☐ Demo video recorded as backup
☐ Team knows the demo script (who says what, who clicks what)
☐ All 6 members have reviewed the final product
```

## GitHub & Version Control Checkpoints (For all 6 Builders)

Since all 6 of you are building this together, code management is critical. 

### How to Check Code Before Pushing
1. **Local Test:** Never push broken code. Run your piece locally (`npm run dev`, `uvicorn app.main:app`, or your ML tests).
2. **Pair Verification:** Aarth & Devraj, Mounya & Utkarsh, Likhita & Ankit should check each other's work. If the pair agrees it works, it's ready.

### How to Push to GitHub
1. Create a branch: `git checkout -b feature/login-page`
2. Commit your code: `git commit -m "Add working login page"`
3. Push to GitHub: `git push origin feature/login-page`
4. Create a Pull Request (PR).

### How to Review & Merge
1. **Frontend:** Devraj reviews Aarth's code (or vice versa).
2. **Backend:** Utkarsh reviews Mounya's code (or vice versa).
3. **ML/AI:** Ankit reviews Likhita's code (or vice versa).
4. **Cross-Team:** If a PR touches the API contract, BOTH Frontend and Backend pairs must approve it.
5. Once approved, merge it into the `main` branch.

### What to Do If Something Fails (Reverting)
If a bad PR gets merged and breaks the `main` branch:
1. Don't panic.
2. Find the bad commit hash on GitHub.
3. Run `git revert <commit-hash>` to create a new commit that undoes the breaking changes.
4. Push the revert. Your `main` branch is instantly back to a working state.
5. Discuss what went wrong as a pair before trying again.

---

# 17. Contact Matrix — Who to Ask When Stuck

```
AARTH OR DEVRAJ ARE STUCK ON:
  ├── API integration → Ask Mounya & Utkarsh
  └── Deployment → Check Vercel logs, debug together

MOUNYA OR UTKARSH ARE STUCK ON:
  ├── API design → Agree together
  ├── ML integration → Ask Likhita & Ankit
  └── Deployment → Check Render logs, debug together

LIKHITA OR ANKIT ARE STUCK ON:
  ├── Prompt engineering → Experiment together
  ├── Integration points → Ask Mounya & Utkarsh
  └── Quality drops → Review Gemini outputs together

GENERAL PROBLEMS:
  ├── "Team communication" → Group chat
  ├── "Feature scope" → Devraj + Ankit + Utkarsh decide what to cut
  └── "Fundamental architecture question" → All 6 members meet
```

### Escalation Rule

```
TRY TO FIX IT YOURSELF (15 minutes max)
    ↓ Still stuck?
ASK YOUR REVIEWER (15 minutes max)
    ↓ Still stuck?
ASK THE OTHER TWO BUILDERS (maybe they faced the same thing)
    ↓ Still stuck?
ALL 6 MEMBERS — 10 MINUTE EMERGENCY MEETING
    ↓ Decide to:
EITHER fix it OR cut the feature and use a fallback
```

**Never spend more than 30 minutes stuck on one problem without asking someone.**

---

# 18. Common Mistakes to Avoid

### 1. Building features nobody asked for

```
DON'T: "Let me add blockchain competency certificates"
DO:    Build the closed loop FIRST. Then add extras if time permits.
```

### 2. Spending too long on design

```
DON'T: Spend 4 hours perfecting button animations
DO:    Get the flow working first. Polish on Day 3.
```

### 3. Not testing the integration early

```
DON'T: Build everything separately and integrate on Day 3
DO:    Connect frontend → backend on Day 1 evening. Even with fake data.
```

### 4. Hardcoding API URLs

```
DON'T: fetch("http://localhost:8000/api/users")
DO:    fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/users`)
       (This way it works in both local and deployed environments)
```

### 5. Not handling errors

```
DON'T: Just call the API and assume it always works
DO:    try/catch every API call. Show error messages in the UI.
```

### 6. Ignoring the Gemini rate limit

```
DON'T: Call Gemini 50 times in a loop
DO:    15 requests per minute max. Add delays. Cache results.
```

### 7. Not seeding the database

```
DON'T: Demo with an empty database
DO:    Pre-load roles, competencies, sample officers, sample evidence
```

### 8. Using real data without permission

```
DON'T: Scrape iGOT or private government sites for data
DO:    Use synthetic/sandbox data. Label it clearly as [SANDBOX DATA]
```

### 9. Calling a scenario MCQ an "executable Python laboratory"

```
DON'T: Tell judges: "This multiple-choice scenario is our Python sandbox lab."
DO:    Say: "This is a scenario-based practical task that generates application evidence without requiring arbitrary code execution."
```

### 10. Claiming live government integration when using mock data

```
DON'T: Say: "We are live-connected to the production iGOT Karmayogi servers."
DO:    Display [SANDBOX] or [REPLAY] badge and explain the normalized adapter architecture.
```

### 11. Confusing sprint task status with product truth

```
DON'T: Mark a feature "Production Ready" just because the sprint ticket is marked "Done."
DO:    Enforce the formal status system: OFFICIAL REQUIREMENT, CORE MVP, RESEARCH CANDIDATE, MEASURED RESULT.
```

---

# 19. Demo Script — What the Judge Sees

> Total demo time: ~8-10 minutes | Strict Demo Honesty & 5-Run Verified

### Minute 0-1: Context & Honest Sandbox Grounding

> "Judges, iGOT delivers training courses. GyanSetu identifies highest-confidence competency gaps, delivers targeted interventions, proves learning with validated evidence, and verifies retention over time. Everything demonstrated today uses official public MoSPI curricula and synthetic sandbox officer profiles."  
*(Point to `[SANDBOX DATA]` badge on UI)*

### Minute 1-3: Officer Journey (5-Point Competency Profile)

1. Log in as **Officer Sharma (Junior Statistical Officer, MoSPI)**.
2. Show the competency dashboard — radar chart + detail cards.
3. Highlight: *"Notice we don't just show a raw percentage score. We show: 1. Mastery: 0.42, 2. Confidence: Low, 3. Evidence Coverage: 25%, 4. Recency: 3 days, 5. Evidence Diversity: 1 source."*
4. Highlight the identified gap: *"Highest-confidence actionable gap: Variance Estimation in Stratified Sampling."*

### Minute 3-5: Diagnostic Assessment (Validated Bank)

1. Start diagnostic assessment. Questions are served from the pre-generated, validated assessment bank (zero live LLM latency or quota risk).
2. Items pass factual grounding and distractor plausibility checks.
3. Sharma answers the stratified allocation question incorrectly.
4. Real-time update: Engine recalculates belief state. The gap is empirically confirmed.

### Minute 5-6: Explainable Next Best Action

1. Show Next Best Action card.
2. Highlight the 12 explainability fields:
   - Reason: Directly targets identified subskill gap
   - Role relevance: High (core JSO survey duty)
   - Prerequisites: Satisfied
   - Modality: Scenario-based practical task from NSSTA catalog.

### Minute 6-7: The Hero Moment (Application Evidence)

1. Officer Sharma completes the **Scenario-Based Practical Task (Type A)**: analyzes sample variance across strata, selects Neyman Allocation, and justifies the decision.
2. System evaluates decision against rubric and generates `APPLICATION_SCENARIO` evidence.
3. **The Hero Moment:**
   - Mastery jumps from 0.42 → 0.74!
   - Confidence increases to High!
   - Evidence diversity updates to 2 distinct types!
   - Status updates to: *"Verified under configured criteria"*.

### Minute 7-8: Content Ingestion & Grounded RAG

1. Show document ingestion with 9 failure handling categories and partial extraction coverage tracker.
2. Ask Virtual Assistant a domain question from official MoSPI manual; show verified citation.
3. Ask out-of-domain question; demonstrate honest abstention: *"I don't have enough verified information in official sources."*

### Minute 8-9: Retention Replay & Admin Workforce Intelligence

1. Switch to Retention Verification tab. Point to `[REPLAY — HISTORICAL SANDBOX EVENT]` badge:
   - *"Retention requires an appropriate delay. We do not pretend we waited 7 days on stage. This replay demonstrates our scheduled re-assessment mechanism on historical sandbox data."*
2. Switch to Director view:
   - Show anonymized workforce competency distribution: *"41% of the sandbox Statistical Officer sample shows a capability gap in Sampling."*
   - Show training effectiveness: *"Observed pre/post improvement of 72% across evaluated sandbox trainees."* (No unverified causal claims).

### Minute 9-10: Architecture & Resilience

1. Show system architecture diagram (8 frozen layers + normalized adapters).
2. Highlight: 100% localhost runnable, zero single-point-of-failure on external APIs, and verified by 5 consecutive clean runs.

---

# 20. Glossary — Hard Words Made Simple

| Hard Term | Simple Meaning |
|-----------|---------------|
| **Competency** | A specific skill that someone needs for their job |
| **Subskill** | A smaller piece of a competency (like "Variance Estimation" is a subskill of "Sampling Design") |
| **Mastery** | How good someone is at a competency (estimated, not certain) |
| **Confidence** | How sure the SYSTEM is about its mastery estimate (not how confident the LEARNER is) |
| **Evidence** | Anything that tells us about someone's competency — test scores, lab results, training history |
| **Evidence Fusion** | Combining multiple pieces of evidence into one estimate |
| **Competency State** | The full picture: mastery + confidence + coverage + recency |
| **Gap** | The difference between what's required and what's demonstrated |
| **Intervention** | Any action taken to fix a gap — course, training, lab exercise |
| **Next-Best-Action** | The single most useful thing the learner should do right now |
| **Closed Loop** | Test → Find Gap → Fix → Re-test → Confirm. Repeats forever. |
| **Adaptive Assessment** | Questions that get harder/easier based on your answers |
| **RAG** | Retrieval Augmented Generation — search documents first, then ask AI |
| **Embedding** | Converting text into numbers that capture meaning |
| **Vector Database** | A database that searches by meaning, not exact words |
| **ORM** | Object Relational Mapper — lets you use Python objects instead of SQL |
| **Migration** | A controlled way to change database structure without losing data |
| **CORS** | Cross-Origin Resource Sharing — browser security that blocks cross-site requests unless allowed |
| **JWT** | JSON Web Token — a secure way to prove "I am logged in" |
| **API Endpoint** | A URL that the frontend calls to send/receive data from the backend |
| **REST API** | A standard way to structure APIs using HTTP methods (GET, POST, PUT, DELETE) |
| **Free Tier** | The free usage level of a cloud service (limited but enough for demo) |
| **Seed Data** | Pre-loaded test data so the database isn't empty |
| **Sandbox** | A safe/fake version of a real system, used for testing |
| **Orchestrator** | The agent that decides which other agent should handle a request |
| **Agent** | An AI module with a specific job (diagnostic, intervention, monitoring) |
| **Competency Engine** | The backend service that calculates mastery from evidence (NOT an agent) |
| **iGOT** | The government's existing learning platform (we INTEGRATE with it, not replace) |
| **NSSTA** | National Statistical Systems Training Academy — MoSPI's training institution |
| **TPAC** | Training Programme Advisory Committee — plans training programs |
| **KCM** | Karmayogi Competency Model — the government's existing competency framework |

---
---

# PART II: ENGINEERING, EVALUATION & EXECUTION RIGOR

# 21. Formal Status System & Sprint Truth

GyanSetu enforces a strict boundary separating **Product & Engineering Truth** from **Sprint Task Status**:

### Product & Engineering Truth (System Governance)
* **OFFICIAL REQUIREMENT** = Mandatory requirement from the problem statement; must satisfy.
* **FROZEN** = Locked architecture, boundary, or design; do not change silently.
* **CORE MVP** = Must be fully functional before any enhancement is touched.
* **ENHANCEMENT** = Implement only after Core MVP passes all verification gates.
* **RESEARCH CANDIDATE** = Advanced exploratory methods (e.g., DKT, IRT, Bandits, RL). Conditional on Step 6.
* **TARGET** = Desired design aspiration; NEVER present as an achieved metric.
* **MEASURED RESULT** = Produced by an actual reproducible experiment with verifiable code/logs.
* **OPTIONAL** = Nice to have if surplus time permits.

### Sprint Task Status (Execution Tracking)
* `PENDING` → `IN_PROGRESS` → `BLOCKED` → `DONE` (Only mark `DONE` when unit tests and pair review pass).
* *Rule: Never mix sprint status with product truth. A ticket marked 'DONE' does not mean a RESEARCH CANDIDATE has become an OFFICIAL REQUIREMENT.*

**Component Status Mapping:**

| Component | Status | Owner | Acceptance Gate | Dependencies | Evidence Required |
| :--- | :--- | :--- | :--- | :--- | :--- |
| Authentication | CORE MVP | Mounya | Gate B | DB | Tests passing |
| Officer Profile | CORE MVP | Aarth | Gate A | Auth | UI + DB tests |
| Competency Graph | CORE MVP | Utkarsh | Gate A | DB | Deterministic calc |
| Competency Engine | CORE MVP | Utkarsh | Gate A | Graph | E0 reproducible |
| Evidence Engine | CORE MVP | Utkarsh | Gate A | DB | Tests passing |
| Diagnostic Agent | CORE MVP | Likhita | Gate B | Comp Engine | Validation checks |
| Adaptive Assessment | ENHANCEMENT | Ankit | Gate D | Diagnostic | Improvement measured |
| Intervention Agent | CORE MVP | Likhita | Gate A | Diagnostic | Explainable UI |
| Monitoring Agent | CORE MVP | Utkarsh | Gate A | Intervention | Retention metrics |
| RAG Chatbot | ENHANCEMENT | Ankit | Gate D | Vector DB | RAG eval passed |
| Document Ingestion | CORE MVP | Ankit | Gate C | Vector DB | Latency < 10s |
| MCQ Generation | CORE MVP | Likhita | Gate B | Content | Validation pass |
| MCQ Validation | CORE MVP | Likhita | Gate B | Generation | >0.6 quality |
| Content-to-Competency Mapping | CORE MVP | Ankit | Gate A | Graph | Manual review |
| Virtual Lab | ENHANCEMENT | Aarth | Gate D | DB | Demo works |
| Admin Dashboard | CORE MVP | Aarth | Gate A | Profile | Auth checks |
| Agent Activity Timeline | ENHANCEMENT | Aarth | Gate D | Logging | Valid JSON |
| iGOT Adapter | RESEARCH CANDIDATE | Mounya | Gate D | Auth | Simulated API |
| NSSTA Adapter | RESEARCH CANDIDATE | Mounya | Gate D | Auth | Simulated API |
| TPAC Adapter | RESEARCH CANDIDATE | Mounya | Gate D | Auth | Simulated API |
| Redis | ENHANCEMENT | Utkarsh | Gate B | Docker | Cache hit logs |
| Framer Motion | ENHANCEMENT | Aarth | Gate E | React | 60fps |
| Advanced ML experiments | RESEARCH CANDIDATE | Ankit | Gate D | ML Pipeline | EXP registry |

---

# 22. Final Architecture Freeze & Change Control

**Authoritative GyanSetu Architecture:**

Frontend
↓
API Layer
↓
Backend Orchestrator
↓
Diagnostic / Intervention / Monitoring Services
↓
Competency + Evidence Engine
↓
PostgreSQL / Evidence Store
↓
ML/AI Services
↓
Content / Vector Store

This is the frozen conceptual architecture. No major subsystem is added to GyanSetu solely because it is technically interesting.

Any proposed architectural change must explicitly use this change-request format:
```text
CHANGE-ID:
PROPOSED CHANGE:
AFFECTED COMPONENTS:
PROBLEM BEING SOLVED:
CURRENT BASELINE:
EXPECTED BENEFIT:
EVIDENCE:
COMPLEXITY IMPACT:
LATENCY IMPACT:
COST IMPACT:
RISK:
REPLACED/REMOVED COMPONENT:
DECISION:
```
No silent architecture changes. The architecture should evolve only when measurable evidence justifies the change.

---

# 23. Priority Stack & Final Engineering Priorities

When development time, compute, or reliability become constrained, engineering decisions strictly follow this priority stack:

1. **CORE COMPETENCY LOOP:** Diagnostic → Subskill Gap Identification → Intervention Recommendation → Evidence Fusion → State Update.
2. **EVIDENCE CORRECTNESS:** Multi-source evidence fusion, 6 distinct evidence types, enforcing `No evidence ≠ low competency`.
3. **ASSESSMENT VALIDITY:** Factual grounding, single correct answer, plausible distractors, cache-first serving.
4. **INTEGRATION RELIABILITY:** Normalized adapter schema for iGOT/NSSTA/TPAC, `LIVE`/`SANDBOX`/`REPLAY` provider modes.
5. **SECURITY & AUTHORIZATION:** Server-side RBAC on `/api/v1/`, prompt-injection boundary, no exposed credentials.
6. **LEARNER & ADMIN EXPERIENCE:** 5-metric dashboard (mastery, confidence, coverage, recency, diversity), explainable cards.
7. **RAG / ASSISTANT / VISUAL POLISH:** Grounded chatbot with strict abstention, responsive charts, clean animations.
8. **ADVANCED RESEARCH MODELS:** Deep knowledge tracing, reinforcement learning, predictive forecasting (evaluated in Step 6).

*Rule: Never sacrifice the core competency loop for a flashy feature.*

---

# 24. Evaluation Integrity and Anti-Circularity

For all competency, recommendation, retrieval, adaptive-assessment, and model experiments, enforce:
TRAIN / ADAPTATION → VALIDATION → HIDDEN / OOD TEST

**Rules:**
* Validation data cannot silently become training data.
* Hidden evaluation data must remain isolated.
* Evaluation questions/content used to select or tune a model cannot also be used as the final proof of that model.
* Recommendation policies must not be optimized directly against the final evaluation set.
* Prompt tuning must not use hidden evaluation answers.
* Benchmark/test content must be versioned.
* Model selection decisions must reference the correct evaluation split.

If a hidden/OOD split is not available for a particular MVP experiment, clearly mark the limitation instead of pretending anti-circularity has been fully achieved.

---

# 25. Formal Experiment Framework & Registry

Every non-trivial AI/ML component must follow:
BASELINE → COMPONENT IMPROVEMENT → CONTROLLED EXPERIMENT → ABLATION → MEASURED BENEFIT → LATENCY / COMPLEXITY / COST → KEEP / REMOVE

**Experiment Registry (`experiments/EXP-xxx.json`):**
```json
{
  "experiment_id": "",
  "objective": "",
  "git_commit": "",
  "config": "",
  "seed": "",
  "dataset_version": "",
  "content_version": "",
  "question_bank_version": "",
  "competency_graph_version": "",
  "prompt_version": "",
  "model_version": "",
  "feature_version": "",
  "evaluation_split": "",
  "environment": "",
  "hardware": "",
  "runtime_seconds": "",
  "latency_metrics": {},
  "performance_metrics": {},
  "cost_metrics": {},
  "artifacts": [],
  "artifact_hashes": [],
  "plots": [],
  "baseline_result": "",
  "component_result": "",
  "ablation_result": "",
  "conclusion": "",
  "decision": ""
}
```
Valid decisions: `KEEP`, `REMOVE`, `REVISE`, `BLOCK`. An experiment without reproducible configuration, version information, and stored artifacts is not sufficient evidence for a measured claim.

---

# 26. Evidence & Artifact Requirements

For every meaningful model or system experiment, require an evidence record. Cloud execution is valid only when the produced artifacts are preserved.
Do not allow statements such as: "The cloud training worked."
Instead require:
```text
EXP-ID:
MODEL:
DATASET:
COMMIT:
CONFIG:
SEED:
RUNTIME:
METRICS:
ARTIFACT LOCATION:
ARTIFACT HASH:
CONCLUSION:
```

---

# 27. Claim Integrity & The Final "Do Not Claim" List

Every builder and presenter must strictly abide by the **15 Forbidden Claims**:
1. Never claim 100% competency accuracy. (Say: *"Probabilistic estimate with explicit confidence intervals."*)
2. Never claim zero hallucinations in LLM generation. (Say: *"Grounded in official documents with validation and abstention."*)
3. Never claim perfect personalization. (Say: *"Targeted intervention matching identified subskill gaps."*)
4. Never claim exact psychological state or fatigue detection. (Say: *"Heuristic engagement signals."*)
5. Never claim causal learning impact without a formal control-group evaluation design. (Say: *"Observed pre/post improvement."*)
6. Never claim live iGOT government API connectivity without an authorized API key. (Say: *"Normalized adapter running in sandbox mode."*)
7. Never claim access to private NSSTA or TPAC trainee databases. (Say: *"Synthetic sandbox data modeled on public curriculum."*)
8. Never claim real national workforce statistics from synthetic sandbox data. (Say: *"Demonstration on synthetic sample data."*)
9. Never claim empirical psychometric validity before collecting learner response data. (Say: *"Content validation with post-response calibration planned."*)
10. Never claim permanent competency closure. (Say: *"Verified under configured criteria; subject to periodic retention checks."*)
11. Never claim exact forgetting prediction curves. (Say: *"Configured retention re-assessment interval."*)
12. Never claim a scenario-based task is an executable Python sandbox. (Say: *"Scenario-based practical task providing application evidence."*)
13. Never claim cached or replayed questions were generated live. (Say: *"Pre-generated and validated assessment bank."*)
14. Never claim the hackathon prototype is a production national-scale deployment. (Say: *"Architecture prototype demonstrating core loop."*)
15. Never hide system uncertainties or low-confidence states from the user.

---

# 28. Data, Content, Model & Prompt Version Provenance

Every output, recommendation, and competency calculation must be traceable:
`CONTENT-v001`, `QUESTION-BANK-v001`, `COMPETENCY-GRAPH-v001`, `PROMPT-v001`, `MODEL-v001`, `EVALUATION-SET-v001`, `API-SCHEMA-v001`, `FEATURE-v001`, `POLICY-v001`.

**Traceability Chain:**
INPUT → SOURCE / CONTENT → EVIDENCE → ASSESSMENT → COMPETENCY ESTIMATE → KNOWLEDGE GAP → RECOMMENDATION → INTERVENTION → POST-ASSESSMENT → RETENTION / OUTCOME

### Content Currency & Expiration Rule
* Do NOT impose an arbitrary universal 12-month expiration on training content.
* For official statistical, regulatory, and methodological materials: **Authoritative supersession and official status take precedence over arbitrary age**.
* Lifecycle: `ACTIVE` → `PENDING_REVIEW` → `SUPERSEDED` / `RETIRED`. Traceability to superseded versions is preserved.

---

# 29. Decision Audit Trail

Every meaningful GyanSetu decision should be traceable using fields conceptually equivalent to:
```json
{
  "request_id": "",
  "user_id": "",
  "decision_id": "",
  "decision_type": "",
  "decision": "",
  "score": "",
  "reason_codes": [],
  "intent_drift": "",
  "model_version": "",
  "feature_version": "",
  "content_version": "",
  "competency_graph_version": "",
  "prompt_version": "",
  "policy_version": "",
  "timestamp": ""
}
```
Do not log sensitive content unnecessarily. The objective is reproducibility and explainability, not indiscriminate logging.

---

# 30. Security Rules & Server-Side Authorization

**Authorization:**
Authentication alone is not sufficient. Authorization must be enforced **server-side** for every protected endpoint. UI visibility is not a security boundary.
* **Officer**: can access only own profile, own competency state, own assessments, assigned interventions.
* **Trainer**: can access assigned learners only, view training-related learner progress, cannot access unrestricted workforce data.
* **Admin**: can access aggregate workforce analytics, manage competency/content data according to permissions.

**Prompt Injection:**
Treat all uploaded, retrieved, imported, or externally supplied content as **untrusted data**.
They must never override: SYSTEM INSTRUCTIONS, TRUSTED APPLICATION DATA, authorization rules, assessment rules, safety rules. Documents can provide domain knowledge only.

**Secrets:**
Never store API keys, production credentials, passwords, or private tokens inside source code or committed configuration.

---

# 31. Reproducibility Requirements

The complete end-to-end GyanSetu workflow must execute successfully for **five consecutive runs** without manual database edits, source-code changes between runs, or hidden backend intervention.

Every reproducibility run should record:
```text
RUN-ID
COMMIT
CONFIG
DATA VERSION
MODEL VERSION
PROMPT VERSION
ENVIRONMENT
RESULT
FAILURES
```

---

# 32. End-to-End System Gates

Every component added to the system must support the core loop or a clearly defined supporting engineering requirement.
* **GATE A — Core Loop**: Can the complete loop execute?
* **GATE B — Baseline**: Does the E0 baseline produce reproducible outputs?
* **GATE C — Evaluation**: Are controlled measurements available?
* **GATE D — Advanced Features**: Do proposed advanced techniques improve the baseline enough to justify their complexity?
* **GATE E — Submission**: Are artifacts, documentation, reproducibility, security, and evidence complete?

If a gate fails, do not continue silently as though it passed.

---

# 33. Performance Accountability

Measure: `p50 latency`, `p95 latency`, `p99 latency`, `throughput`, `error rate`, `resource usage`, `model runtime`, `retrieval runtime`, `database latency`, `generation latency`.

Every optimization must compare BASELINE vs OPTIMIZED and include: benefit, latency change, complexity change, cost change.

---

# 34. Technology Adoption Gate

Every new model, framework, subsystem, or technology must answer:
1. WHAT PROBLEM DOES IT SOLVE?
2. WHAT IS THE BASELINE?
3. WHAT MEASURABLE BENEFIT IS EXPECTED?
4. WHAT IS THE MEASURED BENEFIT?
5. WHAT IS THE COMPLEXITY COST?
6. WHAT IS THE LATENCY COST?
7. WHAT IS THE IMPLEMENTATION RISK?
8. IS IT WORTH KEEPING?

If evidence is unavailable, classify it as RESEARCH CANDIDATE and do not allow it to displace the working baseline.

---

# 35. Independent Technical Review

The reviewer must be independent from the implementation task and inspect: implementation correctness, requirement coverage, security, data leakage, evaluation integrity, reproducibility, unsupported claims, missing tests, unrealistic assumptions, architectural violations, documentation accuracy.

Classify findings as BLOCKING, NON-BLOCKING, or OPTIONAL.
Do not allow a reviewer to silently rewrite architecture. The reviewer reports defects; the implementation agent fixes them under the governing specification.

---

# 36. Antigravity Implementation Rules

For every implementation task:
1. Read: `PROJECT_CONTEXT.md`, `PROJECT_STATUS.md`, `HANDOFF.md`, and the assigned task/specification section.
2. Implement only the assigned task.
3. Do not redesign unrelated architecture.
4. Do not silently change APIs or interfaces.
5. Preserve unrelated working functionality.
6. Add/update tests where the task requires them.
7. Run the relevant tests before declaring completion.
8. Never fabricate experiment results, benchmark numbers, security results, latency measurements, cloud execution results, or evaluation outcomes.
9. Update project status/handoff information when required.
10. Clearly report changed files, tests run, tests passed/failed, known limitations, evidence produced.

**Operating Rule**: Implement the assigned change against the frozen GyanSetu architecture. Do not introduce architecture redesign unless the change-control process explicitly authorizes it.

---

# 37. Cloud / Local Execution Rule

GyanSetu must remain locally reproducible wherever practical. Cloud execution may be used for compute-heavy experiments but must follow:
LOCAL CODE / GIT → CLOUD EXECUTION → ARTIFACT STORAGE → METRICS → EXPERIMENT MANIFEST → COMMIT / VERSION METADATA

No cloud run becomes valid evidence without preserved artifacts. The final demonstration must not depend on live internet access, external Kaggle/Colab, or inaccessible third-party services. Prepare an offline demonstration path.

---

# 38. Final Evidence Package

**Recommended Structure:**
```
artifacts/
├── experiments/
├── metrics/
├── manifests/
├── models/
├── plots/
├── evaluation/
├── sample_data/
├── screenshots/
├── demo/
└── README.md
```
The README must identify: project version, git commit, architecture version, dataset/content versions, model versions, prompt version, experiment IDs, how to reproduce, known limitations. Do not include real sensitive government/user data.

---

# 39. Final Engineering Checklist

Do not mark checklist items as complete unless the document or repository contains evidence supporting completion.
* ENG-01 Architecture frozen
* ENG-02 Source-of-truth hierarchy defined
* ENG-03 Priority levels defined
* ENG-04 Core loop reproducible
* ENG-05 E0 baseline implemented
* ENG-06 Advanced models evaluated against baseline
* ENG-07 Controlled experiments recorded
* ENG-08 Ablations recorded
* ENG-09 Dataset/content versioned
* ENG-10 Question bank versioned
* ENG-11 Competency graph versioned
* ENG-12 Prompt versioned
* ENG-13 Model versioned
* ENG-14 Feature/policy versioning present where needed
* ENG-15 Anti-circularity enforced
* ENG-16 Audit trail present
* ENG-17 Authorization enforced server-side
* ENG-18 Prompt-injection boundary documented
* ENG-19 Structured observability present
* ENG-20 p50/p95/p99 measured
* ENG-21 Cloud experiments preserve artifacts
* ENG-22 No unsupported measured claims
* ENG-23 Independent review process defined
* ENG-24 Offline demo/artifact pack available
* ENG-25 No PII / live unauthorized system interaction
* ENG-26 Final five-run reproducibility check passed
* ENG-27 End-to-end traceability verified
* ENG-28 APIs/contracts versioned where appropriate

---

# 40. Competency-Engine Evaluation Ladder

**Evaluation Stages:**
* **E0 = Baseline** (The current heuristic baseline, not calibrated ground truth)
* **E1 = Evidence-weighted competency estimation**
* **E2 = Multi-source evidence fusion**
* **E3 = Adaptive assessment-aware estimation**
* **E4 = Final selected model**

All versions must use the same API contract. No advanced competency model automatically becomes the production/final model merely because it exists.

---

# 41. RAG, Content Ingestion & Adaptive-Assessment Evaluation

**RAG Test Categories:** RAG-FACTUAL, RAG-CITATION, RAG-GROUNDEDNESS, RAG-ABSTENTION, RAG-RETRIEVAL.
* **Strict Abstention Rule:** The chatbot must prefer an explicit *"I don't have enough verified information in official sources"* response rather than hallucinate or fall back to ungrounded LLM generation.

**Content Ingestion Failure Governance:**
* 9 explicit failure categories: `UNSUPPORTED_FORMAT`, `CORRUPTED_FILE`, `EMPTY_CONTENT`, `OCR_FAILURE`, `ASR_FAILURE`, `PARTIAL_EXTRACTION`, `PROCESSING_TIMEOUT`, `MAPPING_FAILURE`, `UNKNOWN_PROCESSING_ERROR`.
* **Partial Extraction Visibility:** Track successful pages, failed pages, and coverage percentage. If extraction coverage is insufficient, DO NOT generate trusted assessment items.

**Video Ingestion Pipeline:**
* Audio extraction → Local Whisper ASR → Timestamped transcript → Chunking → Concept extraction → Competency mapping. Low-confidence transcripts trigger review rather than silent errors.

**Adaptive-Assessment Evaluation:**
Compare approaches: A. Fixed assessment baseline, B. Difficulty-adaptive, C. Difficulty + subskill adaptive. Adopt adaptive selection only if it reduces assessment burden by ≥ 30% without loss of diagnostic precision.

---

# 42. Retention, Recommendation & Multilingual Architecture

**Retention Evaluation:**
* Retention requires an appropriate delay and cannot be measured instantaneously.
* The system evaluates retention by scheduling delayed re-assessments. In the hackathon prototype, this is demonstrated via `[REPLAY — HISTORICAL SANDBOX EVENT]`.

**Explainable Recommendations:**
Every recommendation must expose 12 reasoning attributes: selected action, justification, role relevance, competency alignment, subskill coverage, prerequisites, gap severity, evidence confidence, learner state, modality, availability, and expected outcome.
* *Causality Rule:* Avoid claiming "Training X caused a 72% improvement." Use: *"The evaluated learners showed an observed pre/post improvement."*

**Multilingual Architecture:**
* Externalized UI strings and localized content models supporting English and Hindi initially, built on an extensible multi-language architecture that preserves statistical terminology without translation drift.

---

# 43. Complete Failure Taxonomy (G1 to G16) & Closed-Loop Metrics

**Failure Handling Closed Loop:** Detect → Diagnose → Safe Action → Log Event → Structured Review

The complete 16-class failure taxonomy:
* **G1:** INSUFFICIENT EVIDENCE → Lower confidence, prompt for diagnostic assessment.
* **G2:** CONFLICTING EVIDENCE → Flag contradiction (e.g. high quiz vs low scenario), trigger practical verification.
* **G3:** LOW-QUALITY ASSESSMENT ITEM → Quarantine item in bank, serve pre-validated replacement.
* **G4:** INCORRECT COMPETENCY MAPPING → Flag mapping for administrator / curriculum review.
* **G5:** STALE COMPETENCY STATE → Trigger scheduled retention verification.
* **G6:** RECOMMENDATION MISMATCH → Re-rank interventions using alternate modality.
* **G7:** AMBIGUOUS LEARNER RESPONSE → Request clarification or alternative question.
* **G8:** RAG RETRIEVAL FAILURE → Strict abstention (*"Insufficient verified information"*).
* **G9:** MODEL UNCERTAINTY → Widen confidence band, request additional evidence.
* **G10:** INSUFFICIENT CONTENT COVERAGE → Mark content incomplete; do not generate trusted items.
* **G11:** EXTERNAL INTEGRATION FAILURE → Switch adapter mode to `SANDBOX` or `REPLAY`.
* **G12:** CONTENT PROCESSING FAILURE → Log failure category (1 of 9), notify content uploader.
* **G13:** TRANSLATION / TERMINOLOGY DRIFT → Revert to standard official statistical vocabulary.
* **G14:** AUTHORIZATION FAILURE → Reject with 403 Forbidden; log security audit event.
* **G15:** DATABASE FAILURE → Abort transaction; enter safe read-only sandbox mode.
* **G16:** API CONTRACT FAILURE → Return structured error envelope with `request_id`.

---

# 44. API Contract Governance

UI hiding is NOT authorization. Every protected FastAPI endpoint must enforce authorization on the server.
**API Contract Rules:**
Every endpoint must specify: endpoint, HTTP method, authentication requirement, authorization requirement, request schema, response schema, error schema, success status code, failure status codes, example request, example response. Use structured JSON errors. Do not expose stack traces to frontend users.

---

# 45. Task Reporting, CI Quality Gates & Step 6 Handoff

**Task IDs:** FE-xxx, BE-xxx, ML-xxx, DB-xxx, API-xxx, EVAL-xxx, TEST-xxx, UI-xxx, DOC-xxx, DEMO-xxx, FINAL-xxx.  
Every completed task must report: `TASK_ID`, `STATUS`, `WHAT_CHANGED`, `FILES_CHANGED`, `COMMANDS_RUN`, `TESTS`, `RESULTS`, `KNOWN_ISSUES`, `ARTIFACTS`, `NEXT_TASK`. Never mark "done" without verification evidence.

**CI Quality Gates:** GitHub Actions: `lint` → `type check` → `unit tests` → `contract tests` → `build`.

### Formal Handoff to Step 6 (Data & Mathematical Grounding)
The architectural, structural, governance, and failure boundaries of GyanSetu are now **FROZEN**.  
Step 6 focuses purely on the mathematical, statistical, and empirical questions:
1. What statistical distributions best model competency uncertainty given limited evidence?
2. What empirical sample sizes are required before computing item discrimination?
3. How are multi-source evidence weights calibrated against actual MoSPI training curricula?
4. How do we rigorously validate the pre-generated assessment bank against official MoSPI documentation?
*Key Step 6 Rule:* Which mathematical, ML, and evaluation mechanisms can actually be defended using the data GyanSetu can realistically obtain? Do not add another feature until that question is answered.

---

# FINAL NOTE

This document is the **single source of truth** for all 6 builders during the 3-day hackathon sprint.

**The Golden Engineering Principles:**
1. **Make the closed loop work first** (Diagnostic → Gap → Next Best Action → New Evidence → State Update).
2. **Be completely honest in the demonstration** (Label sandbox data, show replay badges, admit AI uncertainties).
3. **Never depend on live, un-cached external AI generation on stage.**
4. **Follow the pair-review workflow** and ensure 5 consecutive successful runs before presenting.

Build with rigor, pair review every commit, and deliver a platform that sets the standard for public-sector competency intelligence.

---

> Document prepared by the team planning session. Consolidates GyanSetu Steps 1-5 (FROZEN), Master Governance Hardening, and the Teammate Final Gap Closure & Corrections Patch.
