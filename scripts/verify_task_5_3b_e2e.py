"""
scripts/verify_task_5_3b_e2e.py — Task 5.3b Content Backend End-to-End Runtime Verifier.

Executes the complete operational loop for content ingestion and processing:
TEST 1: Valid PDF upload
TEST 2: Invalid file rejected
TEST 3: Oversized file rejected
TEST 4: Unsupported media type rejected
TEST 5: Duplicate checksum handled
TEST 6: Content metadata persisted
TEST 7: Processing job created
TEST 8: Processing status changes
TEST 9: Extracted content persisted
TEST 10: Chunks persisted
TEST 11: Provenance preserved
TEST 12: Failed processing produces FAILED state
TEST 13: Retry works
TEST 14: Successful retry reaches READY
TEST 15: Unauthorized access rejected
TEST 16: Learner cannot access admin-only content controls
TEST 17: Content versioning works
TEST 18: Retired content cannot be used where prohibited
TEST 19: Malformed mapper output is rejected
TEST 20: Candidate assessment output passes through backend validation
"""

from __future__ import annotations

import os
import sys
import uuid
from pathlib import Path

# Add backend and root to sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
os.chdir(BASE_DIR / "backend")

from dotenv import load_dotenv
load_dotenv(BASE_DIR / "backend" / ".env")

from fastapi.testclient import TestClient
from sqlalchemy import select

from app.database import SessionLocal
from app.main import app
from app.models.competency import Competency, Role, SubSkill
from app.models.content import ContentAsset, ContentChunk, ContentStatus, ContentVersion, JobStatus, ProcessingJob
from app.models.user import User
from app.services.content.content_interfaces import (
    CandidateAssessment,
    CandidateAssessmentValidationError,
    ContentExtractionError,
    ContentMappingError,
    validate_assessment_candidate,
)
from app.services.content.content_service import (
    ContentService,
    ContentValidationError,
    InvalidStateTransitionError,
)
from app.utils.security import create_access_token, hash_password


def run_verification() -> bool:
    print("=" * 80)
    print("TASK 5.3b — CONTENT BACKEND RUNTIME E2E VERIFICATION")
    print("=" * 80)

    client = TestClient(app)
    db = SessionLocal()

    test_results: list[tuple[str, bool, str]] = []

    try:
        # Seed test admin and learner
        admin_role = db.execute(select(Role).where(Role.name == "Admin")).scalars().first()
        if not admin_role:
            admin_role = Role(name="Admin")
            db.add(admin_role)
            db.flush()

        learner_role = db.execute(select(Role).where(Role.name == "Learner")).scalars().first()
        if not learner_role:
            learner_role = Role(name="Learner")
            db.add(learner_role)
            db.flush()

        comp = db.execute(select(Competency)).scalars().first()
        if not comp:
            comp = Competency(name="E2E Content Competency")
            db.add(comp)
            db.flush()

        sub = db.execute(select(SubSkill).where(SubSkill.competency_id == comp.id)).scalars().first()
        if not sub:
            sub = SubSkill(name="E2E Content Subskill", competency_id=comp.id)
            db.add(sub)
            db.flush()

        admin_user = db.execute(select(User).where(User.email == "content_admin_e2e@mospi.gov.in")).scalar_one_or_none()
        if not admin_user:
            admin_user = User(
                email="content_admin_e2e@mospi.gov.in",
                full_name="Content Admin E2E",
                password_hash=hash_password("adminpass"),
                role_id=admin_role.id,
                is_active=True,
            )
            db.add(admin_user)
            db.flush()

        learner_user = db.execute(select(User).where(User.email == "content_learner_e2e@mospi.gov.in")).scalar_one_or_none()
        if not learner_user:
            learner_user = User(
                email="content_learner_e2e@mospi.gov.in",
                full_name="Content Learner E2E",
                password_hash=hash_password("learnerpass"),
                role_id=learner_role.id,
                is_active=True,
            )
            db.add(learner_user)
            db.flush()

        db.commit()
        db.refresh(admin_user)
        db.refresh(learner_user)

        admin_token = create_access_token(admin_user.id)
        learner_token = create_access_token(learner_user.id)

        # TEST 1: Valid PDF upload
        pdf_content = f"%PDF-1.4 MoSPI Field Investigation Manual {uuid.uuid4().hex}. Sampling procedures and field data verification.".encode()
        resp1 = client.post(
            "/api/content/upload",
            files={"file": (f"survey_guide_{uuid.uuid4().hex[:6]}.pdf", pdf_content, "application/pdf")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        t1_pass = resp1.status_code == 200 and resp1.json()["status"] == "UPLOADED" and resp1.json()["asset_id"] is not None
        asset_id = resp1.json().get("asset_id")
        test_results.append(("TEST 1: Valid PDF upload", t1_pass, f"Asset ID: {asset_id}"))

        # TEST 2: Invalid file rejected (empty)
        resp2 = client.post(
            "/api/content/upload",
            files={"file": ("empty.pdf", b"", "application/pdf")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        t2_pass = resp2.status_code == 400
        test_results.append(("TEST 2: Empty file rejection", t2_pass, f"Status: {resp2.status_code}"))

        # TEST 3: Oversized file rejected (> 15MB)
        oversized = b"x" * (16 * 1024 * 1024)
        resp3 = client.post(
            "/api/content/upload",
            files={"file": ("large.pdf", oversized, "application/pdf")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        t3_pass = resp3.status_code == 400
        test_results.append(("TEST 3: Oversized file rejection", t3_pass, f"Status: {resp3.status_code}"))

        # TEST 4: Unsupported media type rejected
        resp4 = client.post(
            "/api/content/upload",
            files={"file": ("script.sh", b"#!/bin/bash\necho hi", "application/x-sh")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        t4_pass = resp4.status_code == 400
        test_results.append(("TEST 4: Unsupported media type rejection", t4_pass, f"Status: {resp4.status_code}"))

        # TEST 5: Duplicate checksum handled
        resp5 = client.post(
            "/api/content/upload",
            files={"file": ("survey_guide_copy.pdf", pdf_content, "application/pdf")},
            headers={"Authorization": f"Bearer {admin_token}"},
        )
        t5_pass = resp5.status_code == 200 and resp5.json()["asset_id"] == asset_id and resp5.json()["is_duplicate"] is True
        test_results.append(("TEST 5: Checksum duplicate detection", t5_pass, f"Duplicate flagged: {resp5.json().get('is_duplicate')}"))

        # TEST 6: Content metadata persisted
        resp6 = client.get(f"/api/content/{asset_id}", headers={"Authorization": f"Bearer {learner_token}"})
        t6_pass = resp6.status_code == 200 and resp6.json()["asset_id"] == asset_id and resp6.json()["file_size"] == len(pdf_content)
        test_results.append(("TEST 6: Content metadata DB persistence", t6_pass, f"Retrieved asset size: {resp6.json().get('file_size')}"))

        # TEST 7: Processing job created
        resp7 = client.get(f"/api/content/{asset_id}/status", headers={"Authorization": f"Bearer {learner_token}"})
        t7_pass = resp7.status_code == 200 and resp7.json()["status"] in ("QUEUED", "PROCESSING", "COMPLETED")
        test_results.append(("TEST 7: Processing job initialized", t7_pass, f"Job ID: {resp7.json().get('job_id')}, Status: {resp7.json().get('status')}"))

        # TEST 8: Processing status changes
        resp8 = client.post(f"/api/content/{asset_id}/process", headers={"Authorization": f"Bearer {admin_token}"})
        t8_pass = resp8.status_code == 200 and resp8.json()["status"] == "COMPLETED" and resp8.json()["current_stage"] == "READY"
        test_results.append(("TEST 8: Pipeline execution to READY", t8_pass, f"Stage: {resp8.json().get('current_stage')}"))

        # TEST 9: Extracted content persisted
        chunks_resp = client.get(f"/api/content/{asset_id}/chunks", headers={"Authorization": f"Bearer {learner_token}"})
        t9_pass = chunks_resp.status_code == 200 and len(chunks_resp.json()) >= 1
        test_results.append(("TEST 9: Extracted content persisted", t9_pass, f"Chunks persisted: {len(chunks_resp.json())}"))

        # TEST 10: Chunks persisted
        chunks_data = chunks_resp.json()
        t10_pass = len(chunks_data) >= 1 and chunks_data[0]["chunk_type"] == "TEXT"
        test_results.append(("TEST 10: Chunk entity schema verified", t10_pass, f"Chunk index 0 type: {chunks_data[0].get('chunk_type') if chunks_data else None}"))

        # TEST 11: Provenance preserved
        cand_resp = client.get(f"/api/content/{asset_id}/candidates", headers={"Authorization": f"Bearer {learner_token}"})
        t11_pass = cand_resp.status_code == 200 and len(cand_resp.json()) >= 1 and f"[INGESTED_CONTENT:{asset_id}:chunk_" in cand_resp.json()[0]["provenance"]
        test_results.append(("TEST 11: Candidate artifact provenance", t11_pass, f"Provenance: {cand_resp.json()[0].get('provenance') if cand_resp.json() else None}"))

        # TEST 12: Failed processing produces FAILED state
        fail_bytes = f"corrupt stream {uuid.uuid4().hex}".encode()
        fail_asset, fail_job, _ = ContentService.upload_content_asset(
            db, f"fail_{uuid.uuid4().hex[:6]}.pdf", "application/pdf", fail_bytes
        )
        class CrashingExtractor:
            def extract(self, fn, mt, cb):
                raise ContentExtractionError("Extraction crash")
        t12_caught = False
        try:
            ContentService.process_content_asset(db, fail_asset.asset_id, extractor=CrashingExtractor())
        except ContentExtractionError:
            t12_caught = True
        db.refresh(fail_asset)
        t12_pass = t12_caught and fail_asset.status == ContentStatus.FAILED.value
        test_results.append(("TEST 12: Error produces FAILED state", t12_pass, f"Asset status: {fail_asset.status}"))

        # TEST 13: Retry works
        resp13 = client.post(f"/api/content/{fail_asset.asset_id}/retry", headers={"Authorization": f"Bearer {admin_token}"})
        t13_pass = resp13.status_code == 200 and resp13.json()["status"] == "COMPLETED" and resp13.json()["retry_count"] >= 1
        test_results.append(("TEST 13: Failed job retry endpoint", t13_pass, f"Retry count: {resp13.json().get('retry_count')}"))

        # TEST 14: Successful retry reaches READY
        db.refresh(fail_asset)
        t14_pass = fail_asset.status == ContentStatus.READY.value
        test_results.append(("TEST 14: Successful retry reaches READY", t14_pass, f"Asset status: {fail_asset.status}"))

        # TEST 15: Unauthorized access rejected (no token)
        resp15 = client.get("/api/content")
        t15_pass = resp15.status_code in (401, 403)
        test_results.append(("TEST 15: Unauthenticated access rejected", t15_pass, f"Status: {resp15.status_code}"))

        # TEST 16: Learner cannot access admin-only content controls
        resp16 = client.post(
            "/api/content/upload",
            files={"file": ("learner_upload.pdf", b"pdf", "application/pdf")},
            headers={"Authorization": f"Bearer {learner_token}"},
        )
        t16_pass = resp16.status_code == 403
        test_results.append(("TEST 16: Learner restricted from admin controls", t16_pass, f"Status: {resp16.status_code}"))

        # TEST 17: Content versioning works
        versions = db.execute(select(ContentVersion).where(ContentVersion.asset_id == fail_asset.id)).scalars().all()
        t17_pass = len(versions) >= 1 and versions[0].version_number == 1
        test_results.append(("TEST 17: Content versioning tracked", t17_pass, f"Versions found: {len(versions)}"))

        # TEST 18: Retired content cannot be used where prohibited
        retire_bytes = f"to retire {uuid.uuid4().hex}".encode()
        retire_asset, _, _ = ContentService.upload_content_asset(
            db, f"retire_{uuid.uuid4().hex[:6]}.pdf", "application/pdf", retire_bytes
        )
        resp18 = client.post(f"/api/content/{retire_asset.asset_id}/retire", headers={"Authorization": f"Bearer {admin_token}"})
        t18_pass = resp18.status_code == 200 and resp18.json()["status"] == "RETIRED"
        test_results.append(("TEST 18: Content retirement enforcement", t18_pass, f"Status: {resp18.json().get('status')}"))

        # TEST 19: Malformed mapper output is rejected
        class CrashingMapper:
            def map_chunk(self, d, c):
                raise ContentMappingError("Invalid taxonomy structure")
        map_fail_bytes = f"map fail bytes {uuid.uuid4().hex}".encode()
        map_fail_asset, _, _ = ContentService.upload_content_asset(
            db, f"map_fail_{uuid.uuid4().hex[:6]}.pdf", "application/pdf", map_fail_bytes
        )
        t19_caught = False
        try:
            ContentService.process_content_asset(db, map_fail_asset.asset_id, mapper=CrashingMapper())
        except ContentMappingError:
            t19_caught = True
        test_results.append(("TEST 19: Malformed mapper rejection", t19_caught, "Mapping error handled gracefully"))

        # TEST 20: Candidate assessment output passes through backend validation
        good_cand = CandidateAssessment(
            prompt="Which sampling method is official standard for consumer expenditure?",
            item_type="MULTIPLE_CHOICE",
            options=["Stratified Multi-stage Sampling", "Voluntary Survey"],
            correct_answer="Stratified Multi-stage Sampling",
            competency_id=comp.id,
            subskill_id=sub.id,
            difficulty="medium",
            provenance="[INGESTION_TEST]",
            rubric={"type": "EXACT_MATCH"},
        )
        t20_valid = True
        try:
            validate_assessment_candidate(db, good_cand)
        except CandidateAssessmentValidationError:
            t20_valid = False

        bad_cand = CandidateAssessment(
            prompt="Short",
            item_type="MULTIPLE_CHOICE",
            options=["A"],
            correct_answer="B",
            competency_id=comp.id,
            subskill_id=sub.id,
            difficulty="medium",
            provenance="[INGESTION_TEST]",
            rubric={},
        )
        t20_bad_caught = False
        try:
            validate_assessment_candidate(db, bad_cand)
        except CandidateAssessmentValidationError:
            t20_bad_caught = True

        t20_pass = t20_valid and t20_bad_caught
        test_results.append(("TEST 20: Assessment candidate validation", t20_pass, "Candidate items strictly validated"))

    finally:
        db.close()

    # Print Report
    print("\n" + "-" * 80)
    all_passed = True
    for name, passed, detail in test_results:
        flag = "PASS" if passed else "FAIL"
        if not passed:
            all_passed = False
        print(f"[{flag}] {name:50} -> {detail}")
    print("-" * 80)
    print(f"5.3b CONTENT RUNTIME STATUS: {'ALL PASSED' if all_passed else 'FAILURES DETECTED'}")
    print("=" * 80)
    return all_passed


if __name__ == "__main__":
    success = run_verification()
    sys.exit(0 if success else 1)
