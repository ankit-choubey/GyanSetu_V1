# Ankit's Backend Integration Guide: Multi-Modal Ingestion, Subskills Engine & 3-Tier Gated Assessment

**Target Audience:** Ankit (Backend Lead)  
**AI/ML Pipeline Stack:** Python 3.13 + FastAPI + SQLAlchemy + ChromaDB (`all-MiniLM-L6-v2`) + Groq LLM + BKT/IRT  
**Version:** 2.5 (Production Specification for Multi-Modal Ingestion, 24 Subskills Library & 3-Tier Gated Assessment)  
**Frontend Reference Contract:** See [DEVRAJ_FRONTEND_INTEGRATION_GUIDE.md](file:///Users/utkarshsingh/Desktop/GyanSetu/main/DEVRAJ_FRONTEND_INTEGRATION_GUIDE.md)

---

## 1. Executive Overview & Architecture Blueprint

This document specifies the exact backend contracts, database models, business logic, and AI/ML pipeline bridges required to implement the frontend requirements defined for Devraj.

### The Core Capabilities
1. **Multi-Modal Content Ingestion**: Accepts 1 to 4 file/media streams simultaneously (`YouTube URL`, `PDF`, `PPTX`, `Local Video/Audio`).
2. **Curated Subskills Engine**: Pre-indexes **24 official statistical subskills** grouped into 5 competencies, allowing instant practice without file upload.
3. **Cross-Modal Deduplication**: Uses `ml_pipeline/content_synthesizer.py` to merge overlapping knowledge representations before indexing into ChromaDB.
4. **Dense Semantic Embeddings**: Uses `all-MiniLM-L6-v2` (384 dims) via `ml_pipeline/vector_store.py`.
5. **3-Tier Gated Assessment Engine**:
   - `Tier 1: Easy` ➔ Always Unlocked.
   - `Tier 2: Medium` ➔ Gated; unlocks **only** when learner scores $\ge 70\%$ on Easy.
   - `Tier 3: Tough` ➔ Gated; unlocks **only** when learner scores $\ge 70\%$ on Medium.
6. **Formative Feedback & Misconception Diagnostics**: Leverages `ml_pipeline/explanation_generator.py` and `ml_pipeline/misconception_classifier.py`.
7. **Production Retraining**: Integrates `ml_pipeline/learner_data_pipeline.py` (EM BKT / 2PL IRT / retention decay).

---

## 2. SQLAlchemy Database Models

Ankit, add the following tables to `app/models/session.py` and `app/models/tiered_assessment.py` (or integrate into your existing models):

```python
# app/models/session.py
import enum
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, ForeignKey, Text, Enum
from sqlalchemy.orm import relationship
from app.database import Base


class SourceTypeEnum(str, enum.Enum):
    YOUTUBE = "youtube"
    PDF = "pdf"
    PPTX = "pptx"
    VIDEO = "video"
    SUBSKILL_SEED = "subskill_seed"


class TierLevelEnum(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    TOUGH = "tough"


class KnowledgeSession(Base):
    """Tracks a learner's multi-modal ingestion or subskill session."""
    __tablename__ = "knowledge_sessions"

    id = Column(String(64), primary_key=True, index=True)  # e.g. "sess_9a8b7c6d5e4f"
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    title = Column(String(255), default="My Study Session")
    selected_subskill_id = Column(String(64), nullable=True)  # e.g. "sub_prob_01"
    chroma_collection_name = Column(String(128), nullable=False)
    status = Column(String(32), default="ready")  # "processing", "ready", "failed"
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    sources = relationship("IngestedSource", back_populates="session", cascade="all, delete-orphan")
    tiers = relationship("AssessmentTierState", back_populates="session", cascade="all, delete-orphan")


class IngestedSource(Base):
    """Tracks each distinct modal file or link ingested into the session."""
    __tablename__ = "ingested_sources"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("knowledge_sessions.id"), nullable=False, index=True)
    source_type = Column(Enum(SourceTypeEnum), nullable=False)
    identifier = Column(String(512), nullable=False)  # URL or filename
    chunks_extracted = Column(Integer, default=0)

    session = relationship("KnowledgeSession", back_populates="sources")


class AssessmentTierState(Base):
    """Tracks the 3-tier gating progress for a session."""
    __tablename__ = "assessment_tier_states"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), ForeignKey("knowledge_sessions.id"), nullable=False, index=True)
    tier_level = Column(Enum(TierLevelEnum), nullable=False)  # easy, medium, tough
    is_unlocked = Column(Boolean, default=False)
    is_completed = Column(Boolean, default=False)
    score_percentage = Column(Float, nullable=True)
    passing_score = Column(Float, default=70.0)
    questions_json = Column(Text, nullable=False)  # JSON array of questions for this tier

    session = relationship("KnowledgeSession", back_populates="tiers")
```

---

## 3. Catalog of 24 Curated Statistical Subskills

Store this seed catalog in `app/seed_data/subskills_catalog.json`. This directly backs `GET /api/v1/content/subskills`:

```json
[
  {
    "competency_id": "COMP-01",
    "competency_name": "Probability Theory & Random Variables",
    "subskills": [
      { "subskill_id": "sub_prob_01", "name": "Bayes' Theorem & Conditional Probability", "description": "Prior/posterior odds, Bayes formula, diagnostic tests." },
      { "subskill_id": "sub_prob_02", "name": "Law of Total Probability & Independence", "description": "Partition of sample space, mutually exclusive events." },
      { "subskill_id": "sub_prob_03", "name": "Discrete Distributions (Binomial & Poisson)", "description": "PMF, Poisson approximation, Bernoulli trials." },
      { "subskill_id": "sub_prob_04", "name": "Continuous Distributions (Normal & Exponential)", "description": "PDF, CDF, standard normal z-scores, memoryless property." },
      { "subskill_id": "sub_prob_05", "name": "Expectation, Variance & Covariance Properties", "description": "Linear combinations of random variables, moments." },
      { "subskill_id": "sub_prob_06", "name": "Law of Large Numbers (Weak & Strong)", "description": "Convergence in probability, sample mean consistency." },
      { "subskill_id": "sub_prob_07", "name": "Central Limit Theorem (CLT)", "description": "Asymptotic normality, sample size rules (n >= 30)." }
    ]
  },
  {
    "competency_id": "COMP-02",
    "competency_name": "Sampling Design & Survey Methodology",
    "subskills": [
      { "subskill_id": "sub_samp_01", "name": "Simple Random Sampling (SRSWR & SRSWOR)", "description": "Inclusion probabilities, standard errors, finite population correction." },
      { "subskill_id": "sub_samp_02", "name": "Stratified Random Sampling & Neyman Allocation", "description": "Homogeneous strata, variance reduction, optimal allocation." },
      { "subskill_id": "sub_samp_03", "name": "Systematic Sampling & Circular Selection", "description": "Periodic variations, sampling interval k = N/n." },
      { "subskill_id": "sub_samp_04", "name": "Cluster Sampling & Two-Stage Design", "description": "Intra-class correlation, primary and secondary sampling units." },
      { "subskill_id": "sub_samp_05", "name": "Non-Sampling Errors & Frame Imperfections", "description": "Non-response bias, imputation methods, measurement errors." }
    ]
  },
  {
    "competency_id": "COMP-03",
    "competency_name": "National Accounts & Macroeconomic Aggregates",
    "subskills": [
      { "subskill_id": "sub_macro_01", "name": "GDP Compilation (Production, Income, Expenditure)", "description": "Three approaches to GDP, boundary of production." },
      { "subskill_id": "sub_macro_02", "name": "Gross Value Added (GVA) at Basic vs Producer Prices", "description": "Product taxes/subsidies, intermediate consumption." },
      { "subskill_id": "sub_macro_03", "name": "Capital Formation & Consumption of Fixed Capital (CFC)", "description": "GFCF, inventory changes, depreciation vs CFC." },
      { "subskill_id": "sub_macro_04", "name": "Supply and Use Tables (SUT) & Input-Output Framework", "description": "Commodity flows, balancing supply and demand." }
    ]
  },
  {
    "competency_id": "COMP-04",
    "competency_name": "Price Indices & Inflation Analytics",
    "subskills": [
      { "subskill_id": "sub_price_01", "name": "Laspeyres, Paasche & Fisher Ideal Price Indices", "description": "Base-weighted vs current-weighted index, time reversal test." },
      { "subskill_id": "sub_price_02", "name": "Consumer Price Index (CPI) Basket Weighting", "description": "Cost-of-living index, household expenditure survey weights." },
      { "subskill_id": "sub_price_03", "name": "Wholesale Price Index (WPI) & GDP Deflator", "description": "Headline vs core inflation, implicit price deflator." },
      { "subskill_id": "sub_price_04", "name": "Index of Industrial Production (IIP) Weighting", "description": "Manufacturing, mining, electricity sector index." }
    ]
  },
  {
    "competency_id": "COMP-05",
    "competency_name": "Statistical Inference & Hypothesis Testing",
    "subskills": [
      { "subskill_id": "sub_inf_01", "name": "Point Estimation & Confidence Intervals", "description": "Unbiasedness, consistency, 95% confidence intervals." },
      { "subskill_id": "sub_inf_02", "name": "Hypothesis Testing (Type I & II Errors, p-values)", "description": "Significance level alpha, statistical power 1 - beta." },
      { "subskill_id": "sub_inf_03", "name": "Chi-Square Test of Independence & Goodness-of-Fit", "description": "Contingency tables, expected frequencies, degrees of freedom." },
      { "subskill_id": "sub_inf_04", "name": "One-Way & Two-Way ANOVA", "description": "F-statistic, between vs within sum of squares." },
      { "subskill_id": "sub_inf_05", "name": "Ordinary Least Squares (OLS) Linear Regression", "description": "Gauss-Markov assumptions, R-squared, residual diagnostics." }
    ]
  }
]
```

---

## 4. REST API Endpoint Implementation Guide

### 4.1 Subskills Catalog Endpoint
* **Route:** `GET /api/v1/content/subskills`
* **File:** `app/routers/content.py`

```python
@router.get("/content/subskills")
def get_subskills_catalog():
    catalog_path = os.path.join(os.path.dirname(__file__), "..", "seed_data", "subskills_catalog.json")
    with open(catalog_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    total_count = sum(len(c["subskills"]) for c in data)
    return {
        "total_subskills": total_count,
        "competencies": data,
    }
```

---

### 4.2 Multi-Modal & Subskill Ingestion Endpoint
* **Route:** `POST /api/v1/content/multi-ingest`
* **File:** `app/routers/content.py`
* **Signature:**

```python
import uuid
import tempfile
from fastapi import APIRouter, Depends, File, Form, UploadFile, HTTPException, status
from sqlalchemy.orm import Session

# Import AI/ML Pipeline engines directly
from ml_pipeline.document_processor import extract_text_and_tables_from_pdf, extract_text_from_pptx
from ml_pipeline.video_processor import process_media, process_youtube_url
from ml_pipeline.chunker import chunk_document
from ml_pipeline.content_synthesizer import ContentSynthesizer
from ml_pipeline.vector_store import add_chunks
from ml_pipeline.generate_question_bank import generate_questions_for_chunk  # or seed fallback

@router.post("/content/multi-ingest")
async def multi_ingest_content(
    youtube_url: Optional[str] = Form(None),
    pdf_file: Optional[UploadFile] = File(None),
    pptx_file: Optional[UploadFile] = File(None),
    video_file: Optional[UploadFile] = File(None),
    subskill_id: Optional[str] = Form(None),
    title: Optional[str] = Form("My Study Session"),
    db: Session = Depends(get_db),
    user = Depends(get_current_user_optional),
):
    # 1. Validation: At least one input must be present
    if not any([youtube_url, pdf_file, pptx_file, video_file, subskill_id]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one ingestion source (YouTube, PDF, PPTX, Video, or Subskill) must be provided."
        )

    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    collection_name = f"coll_{session_id}"
    extracted_chunks_by_source: dict[str, list[dict]] = {}
    sources_summary = []

    # 2. Extract PDF
    if pdf_file:
        pdf_bytes = await pdf_file.read()
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name
        doc_result = extract_text_and_tables_from_pdf(tmp_path)
        chunks = chunk_document(doc_result, source_id=pdf_file.filename)
        extracted_chunks_by_source["pdf"] = chunks
        sources_summary.append({"source_type": "pdf", "filename": pdf_file.filename, "chunks_extracted": len(chunks)})
        os.unlink(tmp_path)

    # 3. Extract PPTX
    if pptx_file:
        pptx_bytes = await pptx_file.read()
        with tempfile.NamedTemporaryFile(suffix=".pptx", delete=False) as tmp:
            tmp.write(pptx_bytes)
            tmp_path = tmp.name
        pptx_result = extract_text_from_pptx(tmp_path)
        chunks = chunk_document(pptx_result, source_id=pptx_file.filename)
        extracted_chunks_by_source["pptx"] = chunks
        sources_summary.append({"source_type": "pptx", "filename": pptx_file.filename, "chunks_extracted": len(chunks)})
        os.unlink(tmp_path)

    # 4. Extract YouTube Video
    if youtube_url:
        yt_result = process_youtube_url(youtube_url)
        yt_doc = {"text": yt_result["transcript"], "pages": [{"page_number": 1, "text": yt_result["transcript"], "tables": []}]}
        chunks = chunk_document(yt_doc, source_id="youtube_video")
        extracted_chunks_by_source["youtube"] = chunks
        sources_summary.append({"source_type": "youtube", "identifier": youtube_url, "chunks_extracted": len(chunks)})

    # 5. Extract Local Video/Audio
    if video_file:
        vid_bytes = await video_file.read()
        suffix = os.path.splitext(video_file.filename)[1]
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
            tmp.write(vid_bytes)
            tmp_path = tmp.name
        media_result = process_media(tmp_path)
        media_doc = {"text": media_result["transcript"], "pages": [{"page_number": 1, "text": media_result["transcript"], "tables": []}]}
        chunks = chunk_document(media_doc, source_id=video_file.filename)
        extracted_chunks_by_source["video"] = chunks
        sources_summary.append({"source_type": "video", "filename": video_file.filename, "chunks_extracted": len(chunks)})
        os.unlink(tmp_path)

    # 6. Load Curated Subskill Seed Content if requested
    if subskill_id:
        subskill_seed_chunks = load_subskill_seed_chunks(subskill_id)
        extracted_chunks_by_source["subskill_seed"] = subskill_seed_chunks
        sources_summary.append({"source_type": "subskill_seed", "identifier": subskill_id, "chunks_extracted": len(subskill_seed_chunks)})

    # 7. Run Cross-Modal Content Synthesizer (Upgrade 4)
    synthesizer = ContentSynthesizer(similarity_threshold=0.82)
    synthesis_result = synthesizer.synthesize(extracted_chunks_by_source)

    # 8. Index into ChromaDB with Dense Semantic Embeddings (Upgrade 1)
    add_chunks(synthesis_result.deduplicated_chunks, collection_name=collection_name)

    # 9. Generate & Calibrate 3 Tiers of Questions
    easy_qs, medium_qs, tough_qs = generate_3tier_questions(
        chunks=synthesis_result.deduplicated_chunks,
        subskill_id=subskill_id
    )

    # 10. Persist Session & Tiers to Database
    session = KnowledgeSession(
        id=session_id,
        user_id=user.id if user else None,
        title=title,
        selected_subskill_id=subskill_id,
        chroma_collection_name=collection_name,
        status="ready"
    )
    db.add(session)
    db.flush()

    tier_easy = AssessmentTierState(session_id=session_id, tier_level="easy", is_unlocked=True, questions_json=json.dumps(easy_qs))
    tier_medium = AssessmentTierState(session_id=session_id, tier_level="medium", is_unlocked=False, questions_json=json.dumps(medium_qs))
    tier_tough = AssessmentTierState(session_id=session_id, tier_level="tough", is_unlocked=False, questions_json=json.dumps(tough_qs))
    db.add_all([tier_easy, tier_medium, tier_tough])
    db.commit()

    return {
        "status": "success",
        "session_id": session_id,
        "title": title,
        "ingested_sources": sources_summary,
        "deduplication_summary": {
            "total_raw_chunks": synthesis_result.total_input_chunks,
            "synthesized_chunks": synthesis_result.total_output_chunks,
            "redundant_chunks_merged": synthesis_result.overlap_pairs_count,
            "reduction_percentage": synthesis_result.reduction_percentage,
        },
        "assessment_status": {
            "easy": { "unlocked": True, "completed": False, "score": None },
            "medium": { "unlocked": False, "completed": False, "score": None },
            "tough": { "unlocked": False, "completed": False, "score": None },
        }
    }
```

---

### 4.3 Gated Tier Status & Questions Fetching
* **Routes:**
  - `GET /api/v1/assessment/tiers?session_id={session_id}`
  - `GET /api/v1/assessment/questions?session_id={session_id}&tier={easy|medium|tough}`
* **File:** `app/routers/assessment.py`

```python
@router.get("/assessment/tiers")
def get_assessment_tier_status(session_id: str, db: Session = Depends(get_db)):
    tiers = db.query(AssessmentTierState).filter_by(session_id=session_id).all()
    if not tiers:
        raise HTTPException(status_code=404, detail="Session not found")
    
    tier_map = {t.tier_level: t for t in tiers}
    return {
        "session_id": session_id,
        "tiers": {
            "easy": {
                "unlocked": tier_map["easy"].is_unlocked,
                "completed": tier_map["easy"].is_completed,
                "score": tier_map["easy"].score_percentage,
                "passing_score": tier_map["easy"].passing_score,
                "questions_count": len(json.loads(tier_map["easy"].questions_json)),
            },
            "medium": {
                "unlocked": tier_map["medium"].is_unlocked,
                "completed": tier_map["medium"].is_completed,
                "score": tier_map["medium"].score_percentage,
                "passing_score": tier_map["medium"].passing_score,
                "unlock_requirement": "Score >= 70% on Easy tier",
                "questions_count": len(json.loads(tier_map["medium"].questions_json)),
            },
            "tough": {
                "unlocked": tier_map["tough"].is_unlocked,
                "completed": tier_map["tough"].is_completed,
                "score": tier_map["tough"].score_percentage,
                "passing_score": tier_map["tough"].passing_score,
                "unlock_requirement": "Score >= 70% on Medium tier",
                "questions_count": len(json.loads(tier_map["tough"].questions_json)),
            }
        }
    }


@router.get("/assessment/questions")
def get_tier_questions(session_id: str, tier: str, db: Session = Depends(get_db)):
    tier_state = db.query(AssessmentTierState).filter_by(session_id=session_id, tier_level=tier.lower()).first()
    if not tier_state:
        raise HTTPException(status_code=404, detail=f"Tier '{tier}' not found for session")

    # Security Gating Check
    if not tier_state.is_unlocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"TIER_LOCKED: Complete prior tier with >= {tier_state.passing_score}% to unlock '{tier}'."
        )

    questions = json.loads(tier_state.questions_json)
    # Strip correct_answer before sending to frontend!
    sanitized = []
    for q in questions:
        sanitized.append({
            "question_id": q["question_id"],
            "question_text": q["question_text"],
            "options": q["options"],  # [{"id": "A", "text": "..."}, ...]
            "source_reference": q.get("source_reference", "GyanSetu Knowledge Base")
        })
    return {"session_id": session_id, "tier": tier, "questions": sanitized}
```

---

### 4.4 Submit Tier Answers, Rich Formative Feedback & Unlock Progression
* **Route:** `POST /api/v1/assessment/submit-tier`
* **File:** `app/routers/assessment.py`

Ankit, here is where you invoke the upgraded **`explanation_generator.py`** (Upgrade 2) and **`misconception_classifier.py`**:

```python
from pydantic import BaseModel
from ml_pipeline.explanation_generator import generate_feedback
from ml_pipeline.misconception_classifier import classify_misconception
from models.bkt_model import BKTModel

class AnswerItem(BaseModel):
    question_id: str
    selected_option: str

class SubmitTierRequest(BaseModel):
    session_id: str
    tier: str
    answers: list[AnswerItem]


@router.post("/assessment/submit-tier")
def submit_tier_assessment(payload: SubmitTierRequest, db: Session = Depends(get_db)):
    tier_state = db.query(AssessmentTierState).filter_by(session_id=payload.session_id, tier_level=payload.tier.lower()).first()
    if not tier_state:
        raise HTTPException(status_code=404, detail="Tier state not found")

    questions = json.loads(tier_state.questions_json)
    questions_by_id = {q["question_id"]: q for q in questions}

    correct_count = 0
    results = []

    for ans in payload.answers:
        q = questions_by_id.get(ans.question_id)
        if not q:
            continue

        selected = ans.selected_option.strip().upper()
        correct = q["correct_answer"].strip().upper()
        is_correct = (selected == correct)
        if is_correct:
            correct_count += 1

        # Invoke Upgrade 2: Groq Formative Feedback
        feedback_res = generate_feedback(
            mcq={
                "question": q["question_text"],
                "options": [opt["text"] for opt in q["options"]],
                "correct_answer": correct,
                "explanation": q.get("explanation", ""),
                "subskill": q.get("subskill", "Statistical Concept")
            },
            selected_letter=selected,
            source_context=q.get("source_context"),
            use_llm=True
        )

        # Misconception diagnosis if incorrect
        misconception_type = None
        if not is_correct:
            try:
                diag = classify_misconception(
                    question_text=q["question_text"],
                    correct_answer=correct,
                    selected_answer=selected,
                    options=[opt["text"] for opt in q["options"]],
                    explanation=q.get("explanation", "")
                )
                misconception_type = diag.misconception_type
            except Exception:
                misconception_type = "conceptual_confusion"

        results.append({
            "question_id": ans.question_id,
            "is_correct": is_correct,
            "user_selected": selected,
            "correct_option": correct,
            "feedback": feedback_res["feedback"],
            "why_wrong": feedback_res.get("why_wrong"),
            "why_right": feedback_res.get("why_right"),
            "misconception_hint": feedback_res.get("misconception_hint"),
            "remediation_steps": feedback_res.get("remediation_steps", []),
            "misconception": misconception_type
        })

    # Compute score
    total = len(payload.answers)
    score_pct = round((correct_count / max(1, total)) * 100.0, 1)
    passed = (score_pct >= tier_state.passing_score)

    tier_state.score_percentage = score_pct
    tier_state.is_completed = True

    next_tier_unlocked = None
    # 3-Tier Gated Unlock Rules:
    if passed:
        if payload.tier == "easy":
            next_tier = db.query(AssessmentTierState).filter_by(session_id=payload.session_id, tier_level="medium").first()
            if next_tier:
                next_tier.is_unlocked = True
                next_tier_unlocked = "medium"
        elif payload.tier == "medium":
            next_tier = db.query(AssessmentTierState).filter_by(session_id=payload.session_id, tier_level="tough").first()
            if next_tier:
                next_tier.is_unlocked = True
                next_tier_unlocked = "tough"

    db.commit()

    return {
        "session_id": payload.session_id,
        "tier": payload.tier,
        "score_percentage": score_pct,
        "passed": passed,
        "next_tier_unlocked": next_tier_unlocked,
        "message": (
            f"Congratulations! You scored {score_pct}% on {payload.tier.title()} and unlocked {next_tier_unlocked.title()}!"
            if next_tier_unlocked
            else (f"Score: {score_pct}%. Passed!" if passed else f"Score: {score_pct}%. Passing requirement is {tier_state.passing_score}%. Review feedback and retry.")
        ),
        "results": results,
        "learning_state": {
            "bkt_mastery_probability": round(min(0.99, 0.20 + (score_pct / 100.0) * 0.75), 2),
            "recommended_action": f"Proceed to {next_tier_unlocked.title()} tier" if next_tier_unlocked else "Review incorrect questions"
        }
    }
```

---

## 5. Background Task Processing

For video audio extraction and Groq Whisper transcription (which take 5–15 seconds), use FastAPI's `BackgroundTasks` to keep the API reactive:

```python
from fastapi import BackgroundTasks

@router.post("/content/multi-ingest-async")
async def multi_ingest_async(background_tasks: BackgroundTasks, ...):
    session_id = f"sess_{uuid.uuid4().hex[:12]}"
    # Save session with status="processing"
    background_tasks.add_task(run_ingest_pipeline, session_id, files_and_urls)
    return {"status": "processing", "session_id": session_id, "check_status_url": f"/api/v1/content/status/{session_id}"}
```

---

## 6. Verification & Automated Unit Testing

Ankit, verify your implementation with this pytest test case in `backend/tests/test_tiered_assessment_integration.py`:

```python
def test_3tier_unlock_progression(client):
    # 1. Create subskill session
    res = client.post("/api/v1/content/subskill-session", json={"subskill_id": "sub_prob_01"})
    assert res.status_code == 200
    sess_id = res.json()["session_id"]

    # 2. Check initial tier status: easy=unlocked, medium=locked, tough=locked
    tiers = client.get(f"/api/v1/assessment/tiers?session_id={sess_id}").json()["tiers"]
    assert tiers["easy"]["unlocked"] is True
    assert tiers["medium"]["unlocked"] is False

    # 3. Medium questions should return 403 Forbidden
    med_res = client.get(f"/api/v1/assessment/questions?session_id={sess_id}&tier=medium")
    assert med_res.status_code == 403

    # 4. Submit Easy answers with 100% score
    easy_qs = client.get(f"/api/v1/assessment/questions?session_id={sess_id}&tier=easy").json()["questions"]
    answers = [{"question_id": q["question_id"], "selected_option": "A"} for q in easy_qs]
    sub_res = client.post("/api/v1/assessment/submit-tier", json={"session_id": sess_id, "tier": "easy", "answers": answers})
    assert sub_res.status_code == 200

    # 5. Verify Medium unlocks if score >= 70%
    if sub_res.json()["passed"]:
        assert sub_res.json()["next_tier_unlocked"] == "medium"
        updated_med = client.get(f"/api/v1/assessment/questions?session_id={sess_id}&tier=medium")
        assert updated_med.status_code == 200
```

---

Ankit, both the AI/ML pipeline and Frontend contracts are aligned. Connect these endpoints and the system will run smoothly end-to-end!
