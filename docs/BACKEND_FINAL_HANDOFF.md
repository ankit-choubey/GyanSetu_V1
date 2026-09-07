# GyanSetu V1 — Backend Final Architecture & Handoff Specification
**SIH 2026 PS 26101 — MoSPI DIID (Branch: `revised-backend`)**

---

## 1. Executive Summary & Status

The backend engineering implementation for **GyanSetu V1** is **100% complete, tested, audited, and frozen** as of Phase 7.x. 

All capabilities mandated by MoSPI Problem Statement 26101 have been implemented across 7 sequential, modular phases:
- **Phase 1**: Foundational Data Architecture, Competency Taxonomy, Role Mappings & Curated Knowledge Items.
- **Phase 2**: Competency State Engine, Multi-Modal Evidence Accumulation, and Adaptive Diagnostic Engine.
- **Phase 3**: Intervention Catalog, Contextual Recommendation Engine, Rejection Reason Registry & Observable Explanations.
- **Phase 4 & 6.1**: Ecosystem Adapters (DIKSHA, SWAYAM, iGOT Karmayogi, Internal, Virtual Lab) with explicit runtime modes (`LIVE`, `SANDBOX`, `REPLAY`, `UNAVAILABLE`), SSO token launch lifecycle, and non-mastery rule enforcement.
- **Phase 5**: Practical Competency Verification, Sandbox Evaluation, and Assessment Signal Fusion.
- **Phase 6**: Workforce Intelligence, Gap Triage, Four-Fifths Role Selection Parity Screening, and Candidate Ranker Plug-in Interface.
- **Phase 7.x**: Audit & Provenance Ledger, 5-Pillar Automated Data Quality Engine, Psychometric Item Response Analytics, Longitudinal Competency Trajectory & Retention Window Monitoring, Recommendation Funnel Conversion, Intervention Outcome Analytics, Centralized Policy Registry, and Operational Health Telemetry.

---

## 2. Technology Stack & Database Architecture

- **Language / Runtime**: Python 3.12 (Virtualenv: `backend/.venv`)
- **API Framework**: FastAPI with OpenAPI 3.1 documentation (`/docs`, `/redoc`, `/openapi.json`)
- **ORM & Data Modeling**: SQLAlchemy 2.0 / SQLModel with Pydantic v2
- **Database Engine**: SQLite 3 (`gyansetu.db` / `backend/gyansetu.db`), fully architected with PostgreSQL-compliant foreign keys, indices, and constraints
- **Database Migrations**: Alembic (`backend/alembic.ini`) with current head `g1a2b3c4d5e6`
- **Testing & Verification**: Pytest (asyncio/anyio), FastAPI TestClient, and specialized runtime E2E verification runners in `scripts/`

---

## 3. Handoff for AI/ML Research Team

The backend is architected to decouple production deterministic baselines from evolving AI/ML research models without breaking API contracts.

### 3.1 Candidate Plug-in Protocol
AI/ML models interface cleanly with the recommendation engine via `CandidateProvider` protocol:
- **Interface Location**: `ml_pipeline/api_interface.py` & `app/services/recommendation_ranker.py`
- **Input Context**: Learner ID, Target Competency ID, Gap Severity, Historical Evidence Vector, Subskill Coverage, Misconception Tags.
- **Output Structure**: Ranked list of candidate interventions with `intervention_id`, `score`, `confidence`, `policy_version`, and structured `rejection_reasons` for unselected options.
- **Contract Rule**: If the ML service is unavailable, latency exceeds threshold, or confidence is below policy bounds, the system automatically falls back to the deterministic production baseline (`v1.0-deterministic-baseline`).

### 3.2 Data Contracts for ML Research
- **Assessment Response Telemetry**: Stored in `assessment_responses` and `assessment_signals` (item ID, selected option, correctness, latency, attempt ID).
- **Psychometric Item Metrics**: Pre-computed via `AssessmentAnalyticsService`:
  - Empirical item difficulty: $P = \frac{\text{correct\_responses}}{\text{total\_responses}}$
  - Point-biserial discrimination index ($r_{pb}$)
  - Distractor utilization distributions
- **Competency Trajectory Vectors**: Stored in `competency_history` (previous mastery, new mastery, confidence, uncertainty $U = 1 - C$, state version, timestamp).

### 3.3 Strict Scientific & Engineering Guardrails
1. **Zero Direct DB Mutations**: AI/ML research scripts must NOT execute direct DDL mutations or runtime table alterations. All data must flow through canonical services or endpoints.
2. **Deterministic Fallbacks**: Any ML research model candidate must be registered with status `RESEARCH_CANDIDATE` in the Model Registry. The production engine runs `PRODUCTION_BASELINE` by default.
3. **Non-Causal Language Discipline**: Predictions, gains, and evaluations must be phrased as *observed associations* or *modelled estimations*, never claiming direct causal proof without randomized controlled evidence.

---

## 4. Handoff for Frontend Engineering Team

The backend exposes **99 fully documented REST endpoints** registered under `/api`.

### 4.1 Base URLs & Documentation
- Base URL (Local Dev): `http://localhost:8000`
- Swagger UI Documentation: `http://localhost:8000/docs`
- ReDoc Documentation: `http://localhost:8000/redoc`
- OpenAPI JSON Schema: `http://localhost:8000/openapi.json`

### 4.2 Authentication & Authorization Headers
All secured endpoints require standard JWT Bearer tokens:
```http
Authorization: Bearer <jwt_access_token>
```
Tokens are acquired via `POST /api/auth/login`.

### 4.3 Core Learner User Flows & Endpoints

| User Flow | HTTP Method & Path | Description |
|---|---|---|
| **Authentication** | `POST /api/auth/login` | Log in with email/password; returns access token & user profile. |
| **Current User** | `GET /api/auth/me` | Fetches active learner identity and role. |
| **Role Competencies** | `GET /api/competencies/{role_id}` | Competency catalog and subskills for the user's role. |
| **Diagnostic Session** | `POST /api/diagnostic/session/start` | Initiates adaptive diagnostic assessment session. |
| **Diagnostic Item** | `GET /api/diagnostic/session/{id}/next-question` | Fetches next adaptive question. |
| **Diagnostic Submit** | `POST /api/diagnostic/session/{id}/submit-response` | Submits learner response. |
| **Diagnostic Finalize** | `POST /api/diagnostic/session/{id}/finalize` | Computes diagnostic convergence and updates competency states. |
| **Recommendations** | `GET /api/recommendations/nba` | Next-Best-Action recommendation with observable explanations. |
| **Resource Launch** | `POST /api/ecosystem/launch/{id}` | Launches external or internal learning resource via SSO token. |
| **Outcome Recording** | `POST /api/ecosystem/outcomes` | Records completion status, score, and updates evidence. |
| **Competency Overview** | `GET /api/competency/timeline` | Multi-competency progression timeline for authenticated learner. |
| **Competency Detail** | `GET /api/competency/timeline/{id}` | Detailed chronological state transitions ($U = 1 - C$) for a competency. |

### 4.4 Administrative & Governance Endpoints

| Governance Domain | HTTP Method & Path | Description |
|---|---|---|
| **Audit Ledger** | `GET /api/admin/audit-logs` | Paginated immutable audit trail with multi-filter support. |
| **Audit Summary** | `GET /api/admin/audit-logs/summary` | Distribution of audit actions, success rates, and actors. |
| **Data Quality Scan** | `GET /api/admin/data-quality` | Full 5-pillar system diagnostic scan (health score 0–100%). |
| **Data Quality Summary**| `GET /api/admin/data-quality/summary` | Categorized issue counts and breakdown. |
| **Category Diagnostic**| `GET /api/admin/data-quality/{cat}` | Targeted diagnostic (taxonomy, evidence, assessment, intervention, state). |
| **Item Bank Analytics** | `GET /api/admin/assessment/items/analytics` | Item catalog response statistics, difficulty, discrimination, flags. |
| **Item Quality Detail** | `GET /api/admin/assessment/items/{id}/quality` | Quality review flags and lifecycle recommendations. |
| **Learner Trajectory** | `GET /api/admin/analytics/learners/{id}/longitudinal` | Administrative multi-competency longitudinal overview. |
| **Recommendation Funnel**| `GET /api/admin/analytics/recommendations`| Funnel conversion (proposed $\to$ accepted $\to$ completed $\to$ rejected). |
| **Intervention Outcomes**| `GET /api/admin/analytics/interventions/outcomes`| Observed gains, provider metrics, and causal disclaimers. |
| **Policy Registry** | `GET /api/admin/policies` | Read operational governance policies, thresholds, and versions. |
| **Policy Update** | `POST /api/admin/policies/{key}` | Update policy threshold with mandatory justification & audit logging. |
| **System Status** | `GET /api/admin/system-status` | Record counts, database latency, and subsystem health. |
| **Public Health Probe** | `GET /api/health` | Liveness and readiness probe for deployment orchestrators. |
| **Provider Health** | `GET /api/health/providers` | Real-time ecosystem provider status and active integration modes. |

---

## 5. Security, Privacy & Ethical Guardrails

1. **Learner Data Isolation**: Personal endpoints (`/api/competency/timeline`) enforce caller isolation by deriving learner ID strictly from the verified JWT payload. Learner A cannot inspect Learner B's progression.
2. **Role-Based Access Control (RBAC)**: All administrative routes (`/api/admin/*`, `/api/workforce/*`) unconditionally enforce administrator role validation. Non-admin tokens receive `403 Forbidden`.
3. **Small-Cell Privacy Suppression ($N < 5$)**: Any cohort or group aggregation where sample size $N < 5$ is suppressed with status `INSUFFICIENT_DATA` to prevent individual re-identification.
4. **Zero Demographic Fabrication**: The database schema and user models strictly contain **zero demographic proxies** (no fields for caste, religion, inferred gender, ethnicity, or synthetic socio-economic tiers).
5. **Non-Mastery Rule**: External learning resource completion without practical verification or assessment evidence cannot update mastery beyond the `NON_MASTERY_CAP` ($0.50$).

---

## 6. How to Run & Verify

### 6.1 Starting Local Development Server
```bash
# Activate virtual environment
source backend/.venv/bin/activate

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 6.2 Running the Master Phase 7 Verification Suite
```bash
# Execute master verification scorecard runner
PYTHONPATH=backend:. backend/.venv/bin/python scripts/verify_backend_7x.py
```

### 6.3 Running Dedicated Phase 7 Pytest Test Cases
```bash
PYTHONPATH=backend:. backend/.venv/bin/pytest backend/tests/test_task_7_*.py tests/system/test_task_7_*.py -v
```

---

## 7. Handoff Checklist & Sign-off

- [x] Database migration head `g1a2b3c4d5e6` applied and verified against fresh builds.
- [x] All 78 Phase 7.x pytest cases passing (100%).
- [x] All specialized runtime E2E verification scripts passing (100%).
- [x] All 99 OpenAPI endpoint routes mounted and operational.
- [x] Strict RBAC and learner tenant isolation verified.
- [x] Small-cell privacy suppression ($N < 5$) active.
- [x] Zero demographic fabrication verified in models and schemas.
- [x] Non-causal association phrasing strictly enforced.
- [x] Documentation complete across `docs/BACKEND_FINAL_HANDOFF.md`, `docs/ENGINEERING_VERIFICATION.md`, and integration contracts.
