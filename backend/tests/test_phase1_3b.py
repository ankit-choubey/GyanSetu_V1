import json

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.assessment import AssessmentItem
from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.user import User
from app.seed_data.competency_taxonomy import COMPETENCIES, taxonomy_counts
from app.seed_data.question_bank import QUESTION_BANK, QuestionBankRecord
from app.seed_data.question_bank_loader import (
    SOURCE_REFERENCE_PREFIX,
    load_question_bank,
    question_bank_fingerprint,
)


@pytest.fixture
def session_factory(monkeypatch):
    from app.seed import seed_data  # noqa: F401

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("app.seed_data.runner.SessionLocal", factory)
    yield factory
    engine.dispose()


@pytest.fixture
def seeded_db(session_factory):
    from app.seed import seed_data

    seed_data("taxonomy-test-password")
    return session_factory


def _minimal_taxonomy(db):
    role = Role(name="Statistical Officer", description="Test role")
    db.add(role)
    db.flush()
    data_quality = Competency(role_id=role.id, name="Data Quality", description="Test competency")
    sampling = Competency(role_id=role.id, name="Sampling Design", description="Test competency")
    db.add_all([data_quality, sampling])
    db.flush()
    validation = SubSkill(competency_id=data_quality.id, name="Validation rules")
    frames = SubSkill(competency_id=sampling.id, name="Sampling frames")
    db.add_all([validation, frames])
    db.flush()
    db.add(RoleCompetency(role_id=role.id, competency_id=data_quality.id))
    learner = User(
        email="learner@example.com",
        full_name="Sample Learner",
        password_hash="hashed",
        role_id=role.id,
        is_active=True,
    )
    db.add(learner)
    db.flush()
    return learner, data_quality, sampling, validation, frames


def _valid_record(**overrides) -> QuestionBankRecord:
    payload = {
        "competency_name": "Data Quality",
        "subskill_name": "Validation rules",
        "question_text": "Which check belongs in a validation rule set?",
        "options": (
            "Accept every code regardless of range",
            "Reject values outside the documented domain",
            "Overwrite identifiers after collection",
            "Publish before reviewing edit failures",
        ),
        "correct_option": "B",
        "difficulty": "easy",
    }
    payload.update(overrides)
    return QuestionBankRecord(**payload)


def test_valid_question_is_inserted_correctly(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        inserted = load_question_bank(db, [_valid_record()])
        db.commit()

        assert inserted == 1
        item = db.execute(select(AssessmentItem).where(AssessmentItem.user_id.is_(None))).scalar_one()
        competency = db.execute(select(Competency).where(Competency.name == "Data Quality")).scalar_one()
        subskill = db.execute(select(SubSkill).where(SubSkill.name == "Validation rules")).scalar_one()
        options = json.loads(item.options_json)

        assert item.user_id is None
        assert item.competency_id == competency.id
        assert item.subskill_id == subskill.id
        assert item.question_text == "Which check belongs in a validation rule set?"
        assert options == [
            "A. Accept every code regardless of range",
            "B. Reject values outside the documented domain",
            "C. Overwrite identifiers after collection",
            "D. Publish before reviewing edit failures",
        ]
        assert item.correct_option == "B"
        assert item.difficulty == "easy"
        expected_ref = question_bank_fingerprint(
            "Data Quality",
            "Validation rules",
            "Which check belongs in a validation rule set?",
        )
        assert item.source_reference == expected_ref
        assert item.source_reference.startswith(SOURCE_REFERENCE_PREFIX)
        assert len(item.source_reference) == len(SOURCE_REFERENCE_PREFIX) + 16


def test_multiple_valid_questions_are_inserted(session_factory):
    second = QuestionBankRecord(
        competency_name="Sampling Design",
        subskill_name="Sampling frames",
        question_text="What must a sampling frame provide before selection?",
        options=(
            "A list of ineligible units only",
            "Coverage of the target population with usable identifiers",
            "The final published estimate",
            "Interviewer opinions about access",
        ),
        correct_option="B",
        difficulty="medium",
    )
    with session_factory() as db:
        _minimal_taxonomy(db)
        inserted = load_question_bank(db, [_valid_record(), second])
        db.commit()
        count = db.scalar(select(func.count()).select_from(AssessmentItem).where(AssessmentItem.user_id.is_(None)))
    assert inserted == 2
    assert count == 2


def test_invalid_competency_reference_is_rejected(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        with pytest.raises(ValueError, match="Invalid competency reference"):
            load_question_bank(db, [_valid_record(competency_name="Not A Taxonomy Competency")])
        assert db.scalar(select(func.count()).select_from(AssessmentItem)) == 0


def test_invalid_subskill_reference_is_rejected(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        with pytest.raises(ValueError, match="Invalid subskill reference"):
            load_question_bank(db, [_valid_record(subskill_name="No Such Subskill")])
        assert db.scalar(select(func.count()).select_from(AssessmentItem)) == 0


def test_subskill_from_another_competency_is_rejected(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        with pytest.raises(ValueError, match="does not belong to competency"):
            load_question_bank(db, [_valid_record(subskill_name="Sampling frames")])
        assert db.scalar(select(func.count()).select_from(AssessmentItem)) == 0


def test_malformed_question_data_is_rejected(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        with pytest.raises(ValueError, match="Incomplete question-bank record"):
            load_question_bank(db, [{"competency_name": "Data Quality", "subskill_name": "Validation rules"}])
        with pytest.raises(ValueError, match="exactly four option texts"):
            load_question_bank(
                db,
                [{
                    "competency_name": "Data Quality",
                    "subskill_name": "Validation rules",
                    "question_text": "Incomplete options?",
                    "options": ["A only", "B only"],
                    "correct_option": "A",
                    "difficulty": "easy",
                }],
            )
        with pytest.raises(ValueError, match="bare option label"):
            load_question_bank(db, [_valid_record(correct_option="E")])
        assert db.scalar(select(func.count()).select_from(AssessmentItem)) == 0


def test_invalid_difficulty_is_rejected(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        with pytest.raises(ValueError, match="Invalid difficulty"):
            load_question_bank(db, [_valid_record(difficulty="extreme")])
        assert db.scalar(select(func.count()).select_from(AssessmentItem)) == 0


def test_repeated_import_does_not_create_duplicates(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        first = load_question_bank(db, [_valid_record(), _valid_record()])
        db.commit()
        item_id = db.execute(select(AssessmentItem.id)).scalar_one()
        second = load_question_bank(db, [_valid_record()])
        db.commit()
        count = db.scalar(select(func.count()).select_from(AssessmentItem))
        remaining_id = db.execute(select(AssessmentItem.id)).scalar_one()
    assert first == 1
    assert second == 0
    assert count == 1
    assert remaining_id == item_id


def test_mixed_batch_rolls_back_without_persisting_any_items(session_factory):
    with session_factory() as db:
        _minimal_taxonomy(db)
        valid = _valid_record()
        invalid = _valid_record(competency_name="Not A Taxonomy Competency")

        with pytest.raises(ValueError, match="Invalid competency reference"):
            load_question_bank(db, [valid, invalid])

        db.rollback()
        count = db.scalar(select(func.count()).select_from(AssessmentItem))

    assert count == 0


def test_existing_assessment_api_remains_compatible(seeded_db):
    from fastapi import Depends, FastAPI
    from fastapi.testclient import TestClient

    from app.dependencies import get_current_user, get_db
    from app.routers.assessment import router as assessment_router

    app = FastAPI()
    app.include_router(assessment_router, prefix="/api")

    def override_db():
        db = seeded_db()
        try:
            yield db
        finally:
            db.close()

    def load_learner(db=Depends(get_db)) -> User:
        return db.execute(select(User).where(User.email == "learner@example.com")).scalar_one()

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_current_user] = load_learner

    bank_prefix = f"{SOURCE_REFERENCE_PREFIX}%"
    with seeded_db() as db:
        learner = db.execute(select(User).where(User.email == "learner@example.com")).scalar_one()
        allowed_ids = {
            competency_id
            for (competency_id,) in db.execute(
                select(RoleCompetency.competency_id).where(RoleCompetency.role_id == learner.role_id)
            ).all()
        }
        sample = db.execute(
            select(AssessmentItem).where(
                AssessmentItem.source_reference == "sample-data-quality",
                AssessmentItem.user_id.is_(None),
            )
        ).scalar_one()
        bank_item = db.execute(
            select(AssessmentItem).where(
                AssessmentItem.source_reference.like(bank_prefix),
                AssessmentItem.user_id.is_(None),
                AssessmentItem.competency_id.in_(allowed_ids),
            )
        ).scalars().first()
        sample_payload = {
            "competency_id": sample.competency_id,
            "answers": [{"question_id": sample.id, "selected": "B"}],
        }
        bank_payload = {
            "competency_id": bank_item.competency_id,
            "answers": [{"question_id": bank_item.id, "selected": bank_item.correct_option}],
        }

    client = TestClient(app)
    sample_response = client.post("/api/assessment/submit", json=sample_payload)
    bank_response = client.post("/api/assessment/submit", json=bank_payload)
    assert sample_response.status_code == 200
    assert sample_response.json()["score"] == 1.0
    assert bank_response.status_code == 200
    assert bank_response.json()["score"] == 1.0


def test_phase1_1_taxonomy_unchanged_by_question_bank_loading(seeded_db):
    expected_names = {item.name for item in COMPETENCIES}
    expected_subskills = {competency.name: set(competency.subskills) for competency in COMPETENCIES}
    role_count, domain_count, competency_count, subskill_count = taxonomy_counts()

    def taxonomy_mapping(db):
        rows = db.execute(
            select(Competency.name, SubSkill.name).join(SubSkill, SubSkill.competency_id == Competency.id)
        ).all()
        mapping: dict[str, set[str]] = {name: set() for name in expected_names}
        for competency_name, subskill_name in rows:
            mapping.setdefault(competency_name, set()).add(subskill_name)
        return mapping

    with seeded_db() as db:
        before = {
            "roles": db.scalar(select(func.count()).select_from(Role)),
            "competencies": db.scalar(select(func.count()).select_from(Competency)),
            "subskills": db.scalar(select(func.count()).select_from(SubSkill)),
            "names": {name for (name,) in db.execute(select(Competency.name)).all()},
        }
        mapping = taxonomy_mapping(db)
        inserted = load_question_bank(db)
        db.commit()
        after_names = {name for (name,) in db.execute(select(Competency.name)).all()}
        after_mapping = taxonomy_mapping(db)
        after_counts = {
            "roles": db.scalar(select(func.count()).select_from(Role)),
            "competencies": db.scalar(select(func.count()).select_from(Competency)),
            "subskills": db.scalar(select(func.count()).select_from(SubSkill)),
        }

    assert inserted == 0
    assert before["names"] == expected_names == after_names
    assert mapping == expected_subskills == after_mapping
    assert before["competencies"] == competency_count == after_counts["competencies"]
    assert before["subskills"] == subskill_count == after_counts["subskills"]
    assert after_counts["roles"] >= role_count
    assert domain_count == 4


def test_seed_loads_question_bank_idempotently_and_keeps_sample_item(seeded_db):
    from app.seed import seed_data

    with seeded_db() as db:
        sample = db.execute(
            select(AssessmentItem).where(AssessmentItem.source_reference == "sample-data-quality")
        ).scalar_one()
        bank_count = db.scalar(
            select(func.count()).select_from(AssessmentItem).where(
                AssessmentItem.source_reference.like(f"{SOURCE_REFERENCE_PREFIX}%"),
                AssessmentItem.user_id.is_(None),
            )
        )
        sample_id = sample.id
        sample_text = sample.question_text
    assert bank_count == len(QUESTION_BANK)

    seed_data("taxonomy-test-password")
    with seeded_db() as db:
        sample = db.execute(
            select(AssessmentItem).where(AssessmentItem.source_reference == "sample-data-quality")
        ).scalar_one()
        bank_count_again = db.scalar(
            select(func.count()).select_from(AssessmentItem).where(
                AssessmentItem.source_reference.like(f"{SOURCE_REFERENCE_PREFIX}%"),
                AssessmentItem.user_id.is_(None),
            )
        )
        unrelated_changed = db.scalar(
            select(func.count()).select_from(AssessmentItem).where(
                AssessmentItem.id == sample_id,
                AssessmentItem.question_text == sample_text,
                AssessmentItem.source_reference == "sample-data-quality",
            )
        )
    assert bank_count_again == len(QUESTION_BANK)
    assert unrelated_changed == 1
