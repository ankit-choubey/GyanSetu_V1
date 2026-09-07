from __future__ import annotations

import copy
import json
import os
from dataclasses import asdict

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel

os.environ.setdefault("JWT_SECRET", "scenario-seed-test-secret")

from app.models.competency import Competency, Role, RoleCompetency, SubSkill
from app.models.scenario import ScenarioItem
from app.seed import seed_data
from app.seed_data.scenario_bank import SCENARIO_BANK, ScenarioBankRecord
from app.seed_data.scenario_bank_loader import (
    load_scenario_bank,
    scenario_bank_fingerprint,
)


@pytest.fixture
def session_factory():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    with factory() as db:
        role = Role(name="Statistical Officer")
        sampling = Competency(name="Sampling Design")
        data_quality = Competency(name="Data Quality")
        db.add_all([role, sampling, data_quality])
        db.flush()
        db.add_all(
            [
                RoleCompetency(role_id=role.id, competency_id=sampling.id),
                RoleCompetency(role_id=role.id, competency_id=data_quality.id),
                SubSkill(competency_id=sampling.id, name="Stratified sampling"),
                SubSkill(competency_id=sampling.id, name="Sampling frames"),
                SubSkill(competency_id=data_quality.id, name="Validation rules"),
            ]
        )
        db.commit()
    yield factory
    engine.dispose()


def _record(**overrides) -> ScenarioBankRecord:
    original = SCENARIO_BANK[0]
    values = {
        "competency_name": original.competency_name,
        "subskill_name": original.subskill_name,
        "scenario_output": copy.deepcopy(original.scenario_output),
        "source_reference": original.source_reference,
    }
    values.update(overrides)
    return ScenarioBankRecord(**values)


def _mapping_record(**overrides) -> dict:
    return asdict(_record(**overrides))


def _output_with(mutator) -> dict:
    output = copy.deepcopy(SCENARIO_BANK[0].scenario_output)
    mutator(output)
    return output


def test_valid_scenario_maps_and_serializes_all_fields(session_factory):
    record = _record()
    with session_factory() as db:
        assert load_scenario_bank(db, [record]) == 1
        db.commit()
        item = db.execute(select(ScenarioItem)).scalar_one()

    assert item.title == record.scenario_output["scenario"]["title"]
    assert item.scenario_text == record.scenario_output["scenario"]["context"]
    assert item.question == record.scenario_output["scenario"]["task"]["question"]
    assert item.response_type == "structured_text"
    assert item.instructions == record.scenario_output["scenario"]["task"]["instructions"]
    assert item.difficulty == "medium"
    assert item.cognitive_level == "application"
    assert item.source_reference == record.source_reference
    assert item.context_data == '{"planning_stage": "before sampling", "population_structure": "homogeneous subgroups"}'
    assert item.expected_reasoning == json.dumps(record.scenario_output["expected_reasoning"], ensure_ascii=False)
    assert item.rubric == json.dumps(record.scenario_output["rubric"], ensure_ascii=False)

    assert item.competency_id == db.execute(
        select(Competency.id).where(Competency.name == "Sampling Design")
    ).scalar_one()
    assert item.subskill_id == db.execute(
        select(SubSkill.id).where(
            SubSkill.name == "Stratified sampling",
            SubSkill.competency_id == item.competency_id,
        )
    ).scalar_one()


def test_mapping_input_is_accepted(session_factory):
    with session_factory() as db:
        assert load_scenario_bank(db, [_mapping_record()]) == 1


@pytest.mark.parametrize(
    "field, value, message",
    [
        ("competency_name", "Unknown competency", "Invalid competency reference"),
        ("subskill_name", "Unknown subskill", "Invalid subskill reference"),
        ("subskill_name", "Validation rules", "does not belong to competency"),
    ],
)
def test_invalid_taxonomy_reference_is_rejected(session_factory, field, value, message):
    with session_factory() as db:
        with pytest.raises(ValueError, match=message):
            load_scenario_bank(db, [_record(**{field: value})])
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == 0


@pytest.mark.parametrize(
    "mutator, message",
    [
        (lambda output: output["scenario"]["task"].update(response_type="multiple_choice"), "response_type"),
        (lambda output: output.update(difficulty="extreme"), "difficulty"),
        (lambda output: output.update(cognitive_level="recall"), "cognitive_level"),
        (lambda output: output["rubric"].update(max_score=9), "rubric"),
        (lambda output: output["rubric"].update(criteria=[]), "rubric.criteria"),
        (lambda output: output["expected_reasoning"].update(key_points=[]), "key_points"),
        (lambda output: output["scenario"]["task"].pop("instructions"), "task"),
    ],
)
def test_invalid_scenario_output_is_rejected(session_factory, mutator, message):
    record = _record(scenario_output=_output_with(mutator))
    with session_factory() as db:
        with pytest.raises(ValueError, match=message):
            load_scenario_bank(db, [record])
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == 0


def test_required_record_fields_are_rejected(session_factory):
    record = asdict(_record())
    del record["source_reference"]
    with session_factory() as db:
        with pytest.raises(ValueError, match="missing fields.*source_reference"):
            load_scenario_bank(db, [record])


def test_overlong_serialized_field_is_rejected(session_factory):
    record = _record(
        scenario_output=_output_with(
            lambda output: output["scenario"]["context_data"].update(
                {"long_value": "x" * 6000}
            )
        )
    )
    with session_factory() as db:
        with pytest.raises(ValueError, match="context_data.*maximum length"):
            load_scenario_bank(db, [record])


def test_duplicate_records_in_one_batch_insert_once(session_factory):
    record = _record()
    with session_factory() as db:
        assert load_scenario_bank(db, [record, record]) == 1
        db.commit()
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == 1


def test_repeated_loading_preserves_id_and_skips_duplicate(session_factory):
    record = _record()
    with session_factory() as db:
        assert load_scenario_bank(db, [record]) == 1
        db.commit()
        first_id = db.execute(select(ScenarioItem.id)).scalar_one()
        assert load_scenario_bank(db, [record]) == 0
        db.commit()
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == 1
        assert db.execute(select(ScenarioItem.id)).scalar_one() == first_id


def test_fingerprint_is_stable_and_uses_required_format():
    first = scenario_bank_fingerprint(_record())
    second = scenario_bank_fingerprint(_record())
    assert first == second
    assert first.startswith("gyansetu-scenario:")
    assert len(first.rsplit(":", 1)[-1]) == 16


def test_mixed_batch_rolls_back_atomically(session_factory):
    valid = _record()
    invalid = _record(source_reference="gyansetu-scenario:invalid:v1", competency_name="Unknown")
    with session_factory() as db:
        with pytest.raises(ValueError, match="Invalid competency reference"):
            load_scenario_bank(db, [valid, invalid])
        db.rollback()
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == 0


def test_seed_full_taxonomy_provisions_scenario(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("app.seed_data.runner.SessionLocal", factory)
    seed_data("scenario-seed-password")
    with factory() as db:
        scenarios = db.execute(select(ScenarioItem)).scalars().all()
        assert len(scenarios) == len(SCENARIO_BANK)
        first_ids = [scenario.id for scenario in scenarios]
        first_references = [scenario.source_reference for scenario in scenarios]

    seed_data("scenario-seed-password")
    with factory() as db:
        scenarios = db.execute(select(ScenarioItem)).scalars().all()
        assert [scenario.id for scenario in scenarios] == first_ids
        assert [scenario.source_reference for scenario in scenarios] == first_references
    engine.dispose()


def test_seed_does_not_call_generator(monkeypatch):
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("app.seed_data.runner.SessionLocal", factory)

    def fail_generation(*args, **kwargs):
        raise AssertionError("scenario generator must not run during seeding")

    monkeypatch.setattr("ml_pipeline.scenario_generator.generate_scenario", fail_generation)
    seed_data("scenario-seed-password")
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(ScenarioItem)) == len(SCENARIO_BANK)
    engine.dispose()
