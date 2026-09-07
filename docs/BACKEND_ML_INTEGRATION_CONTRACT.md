# GyanSetu — Backend-to-ML Integration Contract
*Phase 5.x Service Boundaries, Schemas, Fallbacks & Quality Gates*

---

## 1. Architectural Philosophy & Separation of Concerns

GyanSetu enforces a strict separation between the **authoritative backend system-of-record** and **interchangeable AI/ML intelligence providers**:

```
+-----------------------------------------------------------------------------------+
|                           BACKEND SYSTEM OF RECORD                                |
|                                                                                   |
|  - Relational Integrity (PostgreSQL / SQLite via SQLModel/SQLAlchemy)             |
|  - Idempotency & Concurrency Isolation                                           |
|  - Strict Role-Based Access Control (RBAC) & Learner Isolation                   |
|  - Canonical Taxonomy Verification (MoSPI Official Statistics Framework)          |
|  - Immutable Evidence Ledger & Deterministic Competency State Machine             |
+-----------------------------------------+-----------------------------------------+
                                          |
                        Boundary Protocols & Pydantic DTOs
                                          |
+-----------------------------------------v-----------------------------------------+
|                        PLUGGABLE INTELLIGENCE ADAPTERS                            |
|                                                                                   |
|  - Scenario Generation & Evaluation (Deterministic / LLM)                         |
|  - Content Ingestion: Extraction, Semantic Chunking & Taxonomy Mapping            |
|  - Automated Assessment Candidate Generation                                      |
|  - Practical Learning & Official Simulation Evaluation                            |
|  - Adaptive Diagnostic Selection & Bayesian Competency Estimation                 |
+-----------------------------------------------------------------------------------+
```

### Core Invariants
1. **Zero Raw ML Authority**: ML services NEVER directly write to the database or mutate learner competency state. They emit structured Pydantic DTOs that the backend validates, checks against canonical taxonomy, gates for quality, and persists via atomic database transactions.
2. **Deterministic Fallbacks**: Every boundary interface MUST provide an offline, deterministic fallback implementation that requires zero external API keys, runs in milliseconds, and guarantees system resilience.
3. **Evidence Immutability**: All evidence produced by ML evaluators is immutably recorded in the `Evidence` ledger with explicit provenance headers (`[LLM_EVALUATION]`, `[PRACTICAL_EVALUATION]`, `[SANDBOX DATA]`).
4. **Canonical Taxonomy Compliance**: Any competency or subskill referenced by an ML provider MUST exist in the authoritative database taxonomy. Hallucinated or non-canonical identifiers trigger an immediate rejection (`CandidateValidationError`).

---

## 2. Scenario Intelligence Boundary

Defined in `backend/app/services/scenarios/scenario_interfaces.py`.

### 2.1 Scenario Generator Interface (`ScenarioGenerator`)

```python
class ScenarioGenerator(Protocol):
    def generate(
        self,
        competency_id: int,
        subskill_id: int | None = None,
        difficulty: str = "medium",
        domain: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> ScenarioCandidate:
        ...
```

#### Input Parameters
| Parameter | Type | Validation / Constraints |
|---|---|---|
| `competency_id` | `int` | Must exist in authoritative `competencies` table. |
| `subskill_id` | `int \| None` | Optional. If provided, must belong to `competency_id`. |
| `difficulty` | `str` | Must be one of: `'beginner'`, `'intermediate'`, `'advanced'`, `'easy'`, `'medium'`, `'hard'`. |
| `domain` | `str \| None` | Domain hint (e.g., `'STATISTICAL'`). |
| `context` | `dict \| None` | Contextual parameters (e.g., role requirements, survey context). |

#### Output Schema: `ScenarioCandidate`
```python
class ScenarioCandidate(BaseModel):
    title: str = Field(..., min_length=3, max_length=200)
    description: str = Field(..., min_length=5)
    scenario_type: str  # SURVEY_DESIGN, DATA_VALIDATION, ANALYSIS_INTERPRETATION, DISSEMINATION_ETHICS
    competency_id: int
    subskill_id: int | None = None
    difficulty: str = "medium"
    context_data: dict[str, Any] = Field(default_factory=dict)
    expected_outcomes: list[str] = Field(default_factory=list)
    evaluation_rubric: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

#### Implementations & Fallbacks
- **`DeterministicScenarioGenerator`** (Default baseline): Generates structured MoSPI official statistics operational scenarios (e.g., PLFS non-response handling, ASI gross output imputation) using curated procedural templates.
- **`LLMScenarioGenerator`** (Pluggable): Uses LLM prompting with strict JSON schema enforcement; automatically falls back to `DeterministicScenarioGenerator` on API timeout, rate limit, or schema validation error.

---

### 2.2 Scenario Evaluator Interface (`ScenarioEvaluator`)

```python
class ScenarioEvaluator(Protocol):
    def evaluate(
        self,
        scenario: Scenario,
        response: ScenarioResponse,
    ) -> ScenarioEvaluationResult:
        ...
```

#### Output Schema: `ScenarioEvaluationResult`
```python
class ScenarioEvaluationResult(BaseModel):
    score: float = Field(..., ge=0.0, le=1.0)
    passed: bool
    feedback: str = Field(..., min_length=1)
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    evidence_payload: dict[str, Any] = Field(default_factory=dict)
    suggested_remediation: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

#### Backend Quality Gates & Evidence Emission
When an evaluation result is received:
1. `score` is clamped to $[0.0, 1.0]$. Values outside trigger `ValueError`.
2. Score is compared against `scenario.evaluation_rubric["passing_threshold"]` (default 0.70) to verify `passed`.
3. Backend records a `ScenarioEvaluation` row.
4. Backend emits an `Evidence` record with:
   - `evidence_type = EvidenceType.APPLICATION_SCENARIO`
   - `confidence_score = 0.85`
   - `reliability_status = "RELIABLE"`
   - `provenance = "[SCENARIO_EVALUATION:{evaluator_class}]"`
5. Real-time competency state recalculation is executed via `recalculate_competency_state()`.

---

## 3. Content Ingestion Pipeline Boundaries

Defined in `backend/app/services/content/content_interfaces.py`.

The ingestion pipeline transforms raw unstructured documents (PDF, DOCX, TXT, CSV, JSON) into structured knowledge chunks, taxonomy-mapped assets, and candidate assessment items:

```
[Uploaded Asset] -> [ContentExtractor] -> [ContentParser] -> [ContentChunker] -> [ContentMapper] -> [AssessmentGenerator] -> [Quality Gate] -> [Ready Asset]
```

### 3.1 Content Extractor (`ContentExtractor`)

```python
class ContentExtractor(Protocol):
    def extract(self, file_path: Path, mime_type: str) -> ExtractedDocument:
        ...
```

#### Output Schema: `ExtractedDocument`
```python
class ExtractedDocument(BaseModel):
    title: str
    text_content: str
    pages: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    word_count: int = 0
```

### 3.2 Content Chunker (`ContentChunker`)

```python
class ContentChunker(Protocol):
    def chunk(self, doc: ExtractedDocument, max_chunk_size: int = 1500, overlap: int = 200) -> list[ChunkCandidate]:
        ...
```

#### Output Schema: `ChunkCandidate`
```python
class ChunkCandidate(BaseModel):
    chunk_index: int
    content: str
    chunk_type: str = "TEXT"  # TEXT, TABLE, FORMULA, SECTION
    start_char: int | None = None
    end_char: int | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
```

### 3.3 Content Mapper (`ContentMapper`)

Maps extracted text chunks to canonical MoSPI competencies and subskills.

```python
class ContentMapper(Protocol):
    def map_chunk(
        self,
        chunk: ChunkCandidate,
        available_competencies: list[dict[str, Any]],
    ) -> TaxonomyMappingCandidate:
        ...
```

#### Output Schema: `TaxonomyMappingCandidate`
```python
class TaxonomyMappingCandidate(BaseModel):
    competency_id: int
    subskill_id: int | None = None
    relevance_score: float = Field(..., ge=0.0, le=1.0)
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: str = ""
```

**Quality Rule**: `relevance_score` and `confidence` must both be $\ge 0.40$ for automated linking. Subskills must belong to the referenced competency.

### 3.4 Assessment Item Generator (`AssessmentGenerator`)

Generates candidate assessment items from mapped chunks.

```python
class AssessmentGenerator(Protocol):
    def generate_candidates(
        self,
        chunk: ChunkCandidate,
        competency_id: int,
        subskill_id: int | None = None,
        count: int = 1,
    ) -> list[AssessmentItemCandidate]:
        ...
```

#### Output Schema: `AssessmentItemCandidate`
```python
class AssessmentItemCandidate(BaseModel):
    question_text: str = Field(..., min_length=10)
    options: list[str] = Field(..., min_length=2, max_length=6)
    correct_option: str
    explanation: str = Field(..., min_length=5)
    cognitive_level: str  # Remembering, Understanding, Applying, Analyzing, Evaluating, Creating
    difficulty: str = "medium"
    competency_id: int
    subskill_id: int | None = None
    quality_score: float = Field(default=0.85, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
```

---

## 4. Practical Learning Evaluator Boundary

Defined in `backend/app/services/practical/deterministic_evaluator.py`.

### 4.1 Interface Specification

```python
class PracticalEvaluator(Protocol):
    def evaluate(
        self,
        task: PracticalTask,
        submission: PracticalSubmission,
    ) -> PracticalEvaluationResult:
        ...
```

### 4.2 Scoring Invariants & Quality Rules
1. **Dimension Scoring**: Each dimension defined in `task.evaluation_rubric["dimensions"]` is scored in $[0.0, 1.0]$.
2. **Tolerance Checking**: Numeric submissions are checked against `expected_value` within `tolerance` percentage:
   $$|\text{submitted} - \text{expected}| \le (\text{expected} \times \text{tolerance})$$
3. **Non-Mastery Rule**: If an attempt fails (`passed == False`), mastery MUST NOT advance to mastered status. Competency state is capped at pre-attempt mastery.
4. **Human Review Gate**: If an attempt raises ambiguity, unexpected format, or `flagged_for_review == True`, the status transitions to `REVIEW_REQUIRED` and does not automatically commit mastery gains until an administrator approves.

---

## 5. Replaceability & Adapter Registration Matrix

| Interface | Default Built-in Baseline | Pluggable Implementation Example | Configuration Key |
|---|---|---|---|
| `ScenarioGenerator` | `DeterministicScenarioGenerator` | `LLMScenarioGenerator` (OpenAI / Claude / Gemini) | `SCENARIO_GENERATOR_PROVIDER` |
| `ScenarioEvaluator` | `DeterministicScenarioEvaluator` | `LLMScenarioEvaluator` | `SCENARIO_EVALUATOR_PROVIDER` |
| `ContentExtractor` | `DeterministicContentExtractor` | `TesseractOCRContentExtractor` / `VisionExtractor` | `CONTENT_EXTRACTOR_PROVIDER` |
| `ContentChunker` | `DeterministicContentChunker` | `LangChainSemanticChunker` | `CONTENT_CHUNKER_PROVIDER` |
| `ContentMapper` | `DeterministicContentMapper` | `EmbeddingCosineMapper` (BGE-large / SBERT) | `CONTENT_MAPPER_PROVIDER` |
| `AssessmentGenerator` | `DeterministicAssessmentGenerator` | `FewShotBloomAssessmentGenerator` | `ASSESSMENT_GENERATOR_PROVIDER` |
| `PracticalEvaluator` | `DeterministicEvaluator` | `DynamicSandboxEvaluator` (Docker/Jupyter) | `PRACTICAL_EVALUATOR_PROVIDER` |
| `CompetencyEstimator` | `DeterministicCompetencyEstimator` | `BKTCompetencyEstimator` / `IRT2PLEstimator` | `COMPETENCY_ESTIMATOR_PROVIDER` |

---

## 6. Verification Checklist for ML Contributors

Before submitting any new ML adapter:
1. Implement the canonical Protocol class without altering method signatures.
2. Ensure all output models match the exact Pydantic DTO definitions.
3. Catch all network, API, and timeout exceptions internally and return a structured fallback result or raise the specific domain exception (`CandidateValidationError`, `ContentExtractionError`).
4. Run `backend/.venv/bin/pytest backend/tests/test_task_5_2b_scenario.py backend/tests/test_task_5_3b_content.py backend/tests/test_task_5_4_practical.py` to confirm zero regression against backend contracts.
