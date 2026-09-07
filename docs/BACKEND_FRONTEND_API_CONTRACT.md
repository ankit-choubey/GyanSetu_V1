# GyanSetu — Backend-to-Frontend API Contract
*Phase 5.x RESTful Endpoints, Request/Response Schemas, Auth & Error Specifications*

---

## 1. General Principles

### 1.1 Base URL & Authentication
- **API Prefix**: `/api`
- **Authentication**: Bearer Token in `Authorization` header (`Authorization: Bearer <JWT>`).
- **Data Exchange**: JSON (`Content-Type: application/json`) unless uploading files (`multipart/form-data`).
- **Date Format**: ISO 8601 UTC (`YYYY-MM-DDTHH:MM:SS.mmmmmm` or `YYYY-MM-DDTHH:MM:SSZ`).

### 1.2 Error Response Format
All 4xx and 5xx responses conform to the standard FastAPI error schema:

```json
{
  "detail": "Descriptive human-readable explanation of error or validation failure."
}
```

Validation errors (422) include field-level pointers:
```json
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 3 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

---

## 2. Scenario Endpoints (`/api/scenarios`)

Interactive, situated case-studies for practical application of statistical competencies.

### 2.1 List Available Scenarios
- **Method**: `GET /api/scenarios`
- **Access**: Authenticated (Learner / Admin)
- **Query Parameters**:
  - `competency_id` (optional `int`): Filter by competency ID.
  - `scenario_type` (optional `str`): Filter by type (`SURVEY_DESIGN`, `DATA_VALIDATION`, `ANALYSIS_INTERPRETATION`, `DISSEMINATION_ETHICS`).
  - `difficulty` (optional `str`): Filter by difficulty (`easy`, `medium`, `hard`).
- **Response 200 OK**:
```json
[
  {
    "id": 1,
    "title": "PLFS Non-Response Imputation in Periodic Labour Force Survey",
    "description": "Design an imputation and non-response adjustment workflow for quarterly urban frame non-contacts.",
    "scenario_type": "SURVEY_DESIGN",
    "competency_id": 1,
    "subskill_id": 2,
    "difficulty": "medium",
    "context_data": {
      "survey": "PLFS",
      "round": "2025-Q3",
      "urban_non_contact_rate": 0.082
    },
    "expected_outcomes": [
      "Selection of class mean imputation for continuous variables",
      "Adjustment of sampling weights for non-contact units"
    ],
    "evaluation_rubric": {
      "passing_threshold": 0.70,
      "dimensions": {
        "methodology": 0.40,
        "bias_mitigation": 0.30,
        "variance_estimation": 0.30
      }
    },
    "created_at": "2026-09-07T12:00:00"
  }
]
```

### 2.2 Get Scenario Details
- **Method**: `GET /api/scenarios/{scenario_id}`
- **Access**: Authenticated
- **Response 200 OK**: Single `ScenarioRead` object.
- **Response 404 Not Found**: `{"detail": "Scenario not found."}`

### 2.3 Create Scenario (Admin Only)
- **Method**: `POST /api/scenarios`
- **Access**: Admin only (`role == "ADMINISTRATOR"`)
- **Request Body**:
```json
{
  "title": "ASI Gross Output Valuation and Intermediate Consumption Deflation",
  "description": "Evaluate deflators for manufacturing units in ASI Annual Survey of Industries.",
  "scenario_type": "ANALYSIS_INTERPRETATION",
  "competency_id": 1,
  "subskill_id": 1,
  "difficulty": "hard",
  "context_data": {"industry": "NIC-2008 Division 10"},
  "expected_outcomes": ["Correct selection of WPI vs CPI deflator"],
  "evaluation_rubric": {"passing_threshold": 0.75}
}
```
- **Response 201 Created**: Returns created `ScenarioRead`.
- **Response 403 Forbidden**: If non-admin attempts creation.

### 2.4 Start Scenario Attempt
- **Method**: `POST /api/scenarios/{scenario_id}/start`
- **Access**: Authenticated Learner
- **Headers**:
  - `Idempotency-Key` (optional `str`): Unique UUID to prevent duplicate attempts on double-click.
- **Response 201 Created / 200 OK**:
```json
{
  "id": "scen_att_a1b2c3d4e5f6",
  "scenario_id": 1,
  "user_id": 42,
  "status": "IN_PROGRESS",
  "started_at": "2026-09-07T14:30:00",
  "idempotency_key": "user42-scen1-run1"
}
```

### 2.5 Submit Scenario Response
- **Method**: `POST /api/scenarios/attempts/{attempt_id}/submit`
- **Access**: Authenticated Attempt Owner (Strict Learner Isolation)
- **Request Body**:
```json
{
  "response_text": "We apply class-mean imputation grouped by district and strata, then re-weight using inverse response probabilities.",
  "structured_data": {
    "imputation_method": "class_mean",
    "strata_key": "district_urban",
    "weight_adjustment": "ratio_raking"
  }
}
```
- **Response 200 OK**:
```json
{
  "attempt_id": "scen_att_a1b2c3d4e5f6",
  "status": "COMPLETED",
  "score": 0.85,
  "passed": true,
  "feedback": "Methodology conforms to MoSPI survey standards with correct variance estimation.",
  "dimension_scores": {
    "methodology": 0.90,
    "bias_mitigation": 0.80,
    "variance_estimation": 0.85
  },
  "evidence_id": 312,
  "competency_update": {
    "competency_id": 1,
    "new_mastery": 0.85,
    "new_confidence": 0.88,
    "status": "ASSESSED"
  }
}
```
- **Response 403 Forbidden**: If another learner attempts to submit for an attempt they do not own.

### 2.6 Get Scenario Attempt Results
- **Method**: `GET /api/scenarios/attempts/{attempt_id}`
- **Access**: Authenticated Attempt Owner or Admin
- **Response 200 OK**: Full attempt record with responses and evaluation details.

---

## 3. Content Ingestion Endpoints (`/api/content`)

Modular document ingestion, chunking, taxonomy mapping, and candidate assessment review.

### 3.1 Upload Document Asset
- **Method**: `POST /api/content/upload`
- **Access**: Admin / Ingestion Operator
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary file upload (PDF, DOCX, TXT, CSV, JSON; max 50MB).
  - `title` (optional `str`): Human-readable document title.
  - `description` (optional `str`): Summary of document purpose.
- **Response 201 Created**:
```json
{
  "id": "asset_7a8b9c0d1e",
  "title": "NSSTA Training Programme Calendar 2026-27",
  "file_name": "nssta_calendar_2026.pdf",
  "mime_type": "application/pdf",
  "file_size": 184520,
  "checksum_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "status": "UPLOADED",
  "version": 1,
  "created_at": "2026-09-07T15:00:00"
}
```
- **Response 400 Bad Request**: On empty file, file > 50MB, or unsupported media type.

### 3.2 List Content Assets
- **Method**: `GET /api/content`
- **Access**: Authenticated
- **Query Parameters**:
  - `status` (optional `str`): Filter by status (`UPLOADED`, `PROCESSING`, `EXTRACTED`, `STRUCTURED`, `MAPPED`, `READY`, `FAILED`, `RETIRED`).
  - `skip` (`int`, default 0), `limit` (`int`, default 50).
- **Response 200 OK**: List of `ContentAssetRead`.

### 3.3 Trigger Asset Processing
- **Method**: `POST /api/content/{asset_id}/process`
- **Access**: Admin / Ingestion Operator
- **Query Parameters**:
  - `auto_generate_items` (`bool`, default `false`): Whether to automatically generate candidate MCQ items.
- **Response 202 Accepted**:
```json
{
  "job_id": "job_99a88b77c6",
  "asset_id": "asset_7a8b9c0d1e",
  "job_type": "FULL_PIPELINE",
  "status": "QUEUED",
  "created_at": "2026-09-07T15:01:00"
}
```

### 3.4 Get Extracted Chunks
- **Method**: `GET /api/content/{asset_id}/chunks`
- **Access**: Authenticated
- **Response 200 OK**:
```json
[
  {
    "id": 101,
    "asset_id": "asset_7a8b9c0d1e",
    "chunk_index": 0,
    "chunk_type": "TEXT",
    "content": "Section 3.1: Stratified Random Sampling in Large-Scale Household Surveys...",
    "competency_id": 1,
    "subskill_id": 2,
    "token_count": 240,
    "metadata": {"relevance_score": 0.88}
  }
]
```

### 3.5 Retry Failed Job
- **Method**: `POST /api/content/jobs/{job_id}/retry`
- **Access**: Admin only
- **Response 200 OK**: Updated `ProcessingJobRead` with incremented retry count and re-queued status.

### 3.6 Retire Content Asset
- **Method**: `POST /api/content/{asset_id}/retire`
- **Access**: Admin only
- **Response 200 OK**: Updated `ContentAssetRead` with `status: "RETIRED"`.

---

## 4. Practical Learning Endpoints (`/api/practical`)

Official statistics simulation and practical task verification.

### 4.1 List Practical Tasks
- **Method**: `GET /api/practical/tasks`
- **Access**: Authenticated
- **Query Parameters**:
  - `competency_id` (optional `int`)
  - `difficulty` (optional `str`)
- **Response 200 OK**: List of `PracticalTaskRead`.

### 4.2 Start Practical Attempt
- **Method**: `POST /api/practical/tasks/{task_id}/start`
- **Access**: Authenticated Learner
- **Headers**:
  - `Idempotency-Key` (optional `str`)
- **Response 201 Created**:
```json
{
  "id": "pr_att_e9d8c7b6a5",
  "task_id": 1,
  "user_id": 42,
  "status": "IN_PROGRESS",
  "sandbox_dataset_ref": "sandbox://mospi/plfs/2026_q1_simulated.parquet",
  "started_at": "2026-09-07T16:00:00"
}
```

### 4.3 Submit Practical Work
- **Method**: `POST /api/practical/attempts/{attempt_id}/submit`
- **Access**: Authenticated Attempt Owner (Strict Learner Isolation)
- **Request Body**:
```json
{
  "code_submission": "def compute_gross_output(sales, stock_change): return sales + stock_change",
  "output_artifacts": {
    "gross_output_valuation": 154200.0,
    "intermediate_consumption": 84200.0,
    "gross_value_added": 70000.0
  },
  "execution_metrics": {
    "runtime_ms": 120,
    "rows_processed": 5000
  }
}
```
- **Response 200 OK**:
```json
{
  "attempt_id": "pr_att_e9d8c7b6a5",
  "score": 1.0,
  "passed": true,
  "status": "COMPLETED",
  "dimension_scores": {
    "calculation_accuracy": 1.0,
    "deflation_consistency": 1.0
  },
  "feedback": "All calculated metrics match the authoritative benchmark within acceptable tolerance (1%).",
  "evidence_id": 314,
  "new_mastery": 0.92
}
```
- **Note on Failures**: If `passed == false`, the competency state respects the **Non-Mastery Rule**: mastery score is NOT incremented, preserving un-mastered status.
- **Note on Review**: If submissions are flagged as ambiguous, `status` transitions to `REVIEW_REQUIRED`.

---

## 5. Summary of Frontend Status Code Expectations

| Status Code | Meaning | Frontend Action |
|---|---|---|
| `200 OK` | Successful read / submission | Display results, update learner state indicators. |
| `201 Created` | Successful creation / attempt start | Redirect to attempt runner workspace. |
| `202 Accepted` | Async ingestion pipeline queued | Poll status or await WebSocket / SSE notification. |
| `400 Bad Request` | Invalid parameters, file size, or checksum collision | Display validation message to user. |
| `401 Unauthorized` | Missing or expired JWT token | Redirect user to login flow. |
| `403 Forbidden` | Learner isolation violation or non-admin access | Show unauthorized access banner. |
| `404 Not Found` | Scenario, task, or asset does not exist | Show 404 empty state. |
| `422 Unprocessable` | Schema / type mismatch on payload | Highlight invalid fields in the form. |

---

## 6. Ecosystem Integration Endpoints (`/api/ecosystem`)

Connect external training providers (iGOT Karmayogi, DIKSHA, SWAYAM, MoSPI Internal, NSSTA) into GyanSetu.

### 6.1 Discover Providers
- **Method**: `GET /api/ecosystem/providers`
- **Access**: Authenticated
- **Response 200 OK**:
```json
[
  {
    "provider_name": "iGOT",
    "integration_mode": "SANDBOX",
    "capabilities": ["sync", "launch", "outcome_reporting", "health_check"],
    "is_available": true
  }
]
```

### 6.2 Provider Health Check
- **Method**: `GET /api/ecosystem/providers/{provider}/health`
- **Access**: Authenticated
- **Response 200 OK**:
```json
{
  "provider": "iGOT",
  "status": "HEALTHY",
  "checked_at": "2026-09-08T00:30:00Z",
  "latency_ms": 42.5,
  "mode": "SANDBOX"
}
```

### 6.3 Synchronize Catalog (Admin Only)
- **Method**: `POST /api/ecosystem/sync`
- **Access**: Admin only (`role == "ADMINISTRATOR"`)
- **Query Parameter**: `provider` (optional `str`, defaults to syncing all providers)
- **Response 200 OK**:
```json
{
  "iGOT": {
    "provider": "iGOT",
    "mode": "SANDBOX",
    "added_count": 5,
    "updated_count": 0,
    "skipped_count": 0,
    "rejected_count": 1,
    "total_processed": 6,
    "synced_at": "2026-09-08T00:30:00Z"
  }
}
```

### 6.4 Launch External Resource
- **Method**: `POST /api/ecosystem/resources/{intervention_id}/launch`
- **Access**: Authenticated Learner
- **Response 200 OK**:
```json
{
  "intervention_id": 42,
  "launch_url": "https://igotkarmayogi.gov.in/learn/course/IGOT-001?auth_token=eyJhbGci...",
  "launch_token": "eyJhbGci...",
  "provider": "iGOT",
  "expires_in_seconds": 1800
}
```
- **Response 400 Bad Request**: Raised if resource is `STALE` (> 180 days) or `UNDER_REVIEW`.
- **Response 503 Service Unavailable**: Raised if provider is unavailable.

### 6.5 Webhook Outcome Ingestion
- **Method**: `POST /api/ecosystem/outcomes/webhook`
- **Access**: Authenticated / Provider Webhook Secret
- **Request Body**:
```json
{
  "user_id": 1,
  "intervention_id": 42,
  "provider": "iGOT",
  "provider_activity_id": "ACT-109283",
  "status": "COMPLETED",
  "score": 0.88,
  "time_spent_minutes": 45,
  "completed_at": "2026-09-08T00:35:00Z"
}
```
- **Response 200 OK**:
```json
{
  "status": "RECORDED",
  "outcome_id": 108,
  "evidence_id": 512,
  "mastery_updated": true,
  "new_mastery": 0.74
}
```

---

## 7. Workforce Intelligence Endpoints (`/api/workforce`)

Organizational aggregations, gap distributions, and institutional fairness audits.

### 7.1 Workforce Overview
- **Method**: `GET /api/workforce/overview`
- **Access**: Admin or Supervisor only (`role in ["ADMINISTRATOR", "SUPERVISOR"]`)
- **Query Parameter**: `cohort_id` (optional `str`), `role_id` (optional `int`)
- **Response 200 OK**:
```json
{
  "total_workforce": 120,
  "active_assessed_learners": 95,
  "assessed_ratio": 0.792,
  "average_mastery": 0.684,
  "average_confidence": 0.712,
  "roles_summary": [
    {
      "role_id": 1,
      "role_name": "Junior Statistical Officer",
      "headcount": 45,
      "avg_mastery": 0.65,
      "privacy_suppressed": false
    }
  ]
}
```
- **Privacy Suppression Note**: If any group has fewer than 5 learners ($N < 5$), metrics are masked with `"privacy_suppressed": true` and numeric averages are omitted.

### 7.2 Institutional Fairness Audit
- **Method**: `GET /api/workforce/fairness`
- **Access**: Admin only (`role == "ADMINISTRATOR"`)
- **Response 200 OK**:
```json
{
  "metric": "FOUR_FIFTHS_RULE",
  "role_selection_disparity": [
    {
      "role_name": "Junior Statistical Officer",
      "qualified_ratio": 0.82,
      "adverse_impact_flag": false
    }
  ],
  "demographic_screening": {
    "status": "DEMOGRAPHIC_DATA_ABSENT",
    "notes": "No synthetic or fabricated demographic data was generated. Compliance screening relies strictly on institutional role distribution."
  }
}
```

---

## 8. Recommendation & Explainability Endpoints (`/api/recommendations`)

Personalized next best actions grounded in observable gap and evidence signals.

### 8.1 Request Next Best Action
- **Method**: `POST /api/recommendations/next`
- **Access**: Authenticated Learner
- **Request Body**:
```json
{
  "competency_id": 1,
  "subskill_id": 2,
  "target_duration_minutes": 30
}
```
- **Response 200 OK**:
```json
{
  "recommendation_id": "rec_f8a9b2c3d4",
  "selected_intervention": {
    "id": 12,
    "title": "Stratified Sampling Allocation Fundamentals",
    "provider": "INTERNAL",
    "modality": "ONLINE_SELF_PACED",
    "duration_minutes": 25,
    "difficulty": "medium"
  },
  "explanation": {
    "primary_reason": "Remediates identified competency gap in Sampling Design (current mastery 0.35)",
    "competency_gap": 0.65,
    "evidence_support": "Triggered by incorrect response in Diagnostic session evaluating stratified variance estimation",
    "priority": "HIGH"
  },
  "status": "PROPOSED",
  "created_at": "2026-09-08T00:40:00Z"
}
```

### 8.2 Get Recommendation Details & Explanation
- **Method**: `GET /api/recommendations/{recommendation_id}`
- **Method**: `GET /api/recommendations/{recommendation_id}/explanation`
- **Access**: Authenticated Recommendation Owner (Strict Learner Isolation)
- **Response 200 OK**: Inspectable explanation and candidate rejection rationale.

### 8.3 Submit Recommendation Feedback
- **Method**: `POST /api/recommendations/{recommendation_id}/feedback`
- **Access**: Authenticated Recommendation Owner
- **Request Body**:
```json
{
  "action": "ACCEPT",
  "notes": "Enrolled for this morning."
}
```
- **Allowed Actions**: `ACCEPT`, `START`, `COMPLETE`, `SKIP`, `REJECT`.
- **Response 200 OK**: Idempotent feedback response reflecting current status (`ACCEPTED`, `STARTED`, `COMPLETED`, `SKIPPED`, `REJECTED`).

