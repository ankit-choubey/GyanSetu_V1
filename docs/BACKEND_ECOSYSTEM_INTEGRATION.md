# GyanSetu — Backend Ecosystem Integration Architecture
*Phase 6.x External Learning Providers, Normalization, Security & Governance*

---

## 1. Architectural Overview

GyanSetu integrates disparate external government learning portals into a unified competency development platform. To maintain reliability, institutional compliance, and data integrity, all external interactions flow through an abstracted **Intervention Adapter** layer:

```
+-----------------------------------------------------------------------------------------+
|                                  GYANSETU CORE BACKEND                                  |
|                                                                                         |
|  [NextBestActionService] <---> [EligibilityEngine] <---> [CompetencyMappingService]     |
|                                         ^                                               |
|                                         | Canonical Interventions                       |
+-----------------------------------------+-----------------------------------------------+
                                          |
                               [EcosystemSyncService]
                                          |
        +---------------------------------+---------------------------------+
        |                                 |                                 |
+-------v-------+                 +-------v-------+                 +-------v-------+
|  iGOT Adapter |                 | DIKSHA Adapter|                 | SWAYAM Adapter|
| (Karmayogi)   |                 | (School/Basic)|                 | (Higher Ed)   |
+---------------+                 +---------------+                 +---------------+
```

---

## 2. Integration Modes & Health Checks

Every adapter implements the `InterventionAdapter` base class (`backend/app/services/adapters/base_adapter.py`) and declares its current runtime `IntegrationMode`:

| Integration Mode | Behavior & Operating Guarantees | Production Transition Requirements |
|---|---|---|
| `LIVE` | Live network calls to external provider REST APIs with OAuth2 mTLS egress. | Valid production API key/client credentials, outbound firewall whitelist, signed provider contract. |
| `SANDBOX` | Deterministic official mock responses emulating external provider payloads and error conditions. | Default out-of-the-box mode for developer testing and local evaluation. |
| `REPLAY` | Historical recorded provider traces replayed for deterministic audit verification. | Seeded trace files in `data/ecosystem_traces/`. |
| `UNAVAILABLE` | Graceful offline circuit-breaking returning `HealthStatus.UNAVAILABLE` and HTTP 503 on launch. | Triggered automatically on network timeouts (> 2000ms), 5xx gateway errors, or administrative disablement. |

### Health Check Specification
- Endpoint: `GET /api/ecosystem/providers/{provider}/health`
- Checks connectivity, token validity, and response latency without downloading catalogs.

---

## 3. Canonical Normalization Contract (`CanonicalInterventionPayload`)

External catalogs from heterogeneous providers (SCORM packages, video lectures, PDF modules, interactive courses) are normalized into a single canonical contract before database insertion:

```python
@dataclass
class CanonicalInterventionPayload:
    provider: str                      # e.g., "iGOT", "DIKSHA", "SWAYAM", "INTERNAL", "NSSTA"
    provider_resource_id: str          # Unique external catalog ID (e.g., "IGOT-PUBLIC-001")
    title: str                         # Sanitized title
    description: str                   # Clean plain text description
    intervention_type: str             # "COURSE", "READING", "SIMULATION", "ASSESSMENT"
    modality: str                      # "ONLINE_SELF_PACED", "BLENDED", "IN_PERSON"
    duration_minutes: int              # Estimated time to complete
    difficulty: str                    # "easy", "medium", "hard"
    status: str = "ACTIVE"             # "ACTIVE", "STALE", "UNDER_REVIEW"
    integration_mode: str = "SANDBOX"  # "LIVE", "SANDBOX", "REPLAY", "UNAVAILABLE"
    competency_hint: str | None        # Raw external competency string
    subskill_hint: str | None          # Raw external subskill string
    prerequisites_json: str | None     # JSON string of prerequisite rules
    external_url: str | None           # Portal landing / launch URL
    provenance: str                    # e.g., "[ECOSYSTEM_SYNC:iGOT]"
    version: str = "1.0.0"             # Resource semantic version
    last_verified_at: datetime         # Timestamp of last catalog verification
    target_misconception_pattern: str  # Optional targeted error pattern
    priority: str = "MEDIUM"           # "HIGH", "MEDIUM", "LOW"
    external_metadata: dict            # Provider-specific metadata dictionary
```

---

## 4. Competency Taxonomy Mapping & Quarantine

External portals rarely use MoSPI's exact 40-competency / 160-subskill taxonomy. The `CompetencyMappingService` provides automated reconciliation:

1. **Exact & Curated Alias Normalization**:
   - String normalization (lowercase, whitespace collapse, punctuation removal).
   - Curated domain synonyms (e.g. `"cpi compilation"` $\to$ `"Index Numbers"`, `"Price relatives"`).
2. **Cross-Competency Integrity Gate**:
   - If an external title specifies a subskill that belongs to a DIFFERENT competency than its domain hint (e.g. Sampling Design combined with CPI compilation), automated mapping is rejected.
3. **Quarantine (`UNDER_REVIEW`)**:
   - Unmatched or ambiguous titles are marked `status = "UNDER_REVIEW"` with `confidence <= 0.20`.
   - Quarantined resources are excluded from learner recommendation pools and cannot be launched until an administrator manually approves or maps the record.

---

## 5. Staleness & Retention Rules

Statistical methodologies, survey classifications (e.g. NIC-2008, ASI definitions), and national standards evolve over time.
- **180-Day Staleness Policy**: Any catalog resource with `last_verified_at` older than 180 days is automatically flagged as `STALE`.
- **Launch Invariant**: `POST /api/ecosystem/resources/{id}/launch` strictly rejects any `STALE` resource with an `HTTP 400 Bad Request` ("Resource verification expired; catalog item marked STALE").

---

## 6. Secure Launch Lifecycle & Outcome Ingestion

```
[Learner] --- POST /api/ecosystem/resources/{id}/launch ---> [GyanSetu]
    <--- Returns signed launch_token (30 min exp) & URL ---

[Learner] --- Redirects to Provider with token ---> [External Provider (e.g. iGOT)]
    Learner completes training module.

[External Provider] --- POST /api/ecosystem/outcomes/webhook ---> [GyanSetu]
    1. Validates webhook signature and user_id / intervention_id.
    2. Records InterventionOutcome (COMPLETED, score, time_spent).
    3. Emits immutable Evidence record (source="TRAINING_HISTORY").
    4. Triggers Bayesian Competency State recalculation.
    5. Returns 200 OK with new_mastery.
```

### The Non-Mastery Rule
External completion alone does NOT grant automatic high mastery:
- If `status != "COMPLETED"` or `score < 0.70`, mastery is capped at $\le 0.50$.
- Full mastery requires verified post-intervention assessment or practical scenario evidence.

---

## 7. Extensibility Guide: Adding a New Provider

To add a new external training partner (e.g. `CustomProvider`):
1. Subclass `InterventionAdapter` in `backend/app/services/adapters/provider_adapters.py`.
2. Implement:
   - `get_provider_name() -> str`
   - `get_integration_mode() -> IntegrationMode`
   - `check_health() -> ProviderHealth`
   - `sync_resources() -> list[CanonicalInterventionPayload]`
   - `generate_launch_payload(user_id, intervention_id, resource_id) -> LaunchPayload`
   - `normalize_outcome(raw_payload) -> NormalizedOutcome`
3. Register the adapter in `PROVIDER_REGISTRY` in `backend/app/services/adapters/__init__.py`.
4. Run:
   ```bash
   backend/.venv/bin/pytest tests/system/test_task_6_backend_integration.py -k "test_03_provider_extensibility_contract"
   ```
