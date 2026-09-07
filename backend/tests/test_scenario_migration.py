import os
from pathlib import Path

os.environ.setdefault(
    "JWT_SECRET",
    "phase4-2-migration-test-secret-that-is-at-least-32-chars",
)

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, inspect
from sqlmodel import SQLModel

from app.config import settings
from app.models import ScenarioAttempt, ScenarioItem


def test_scenario_models_are_registered_in_sqlmodel_metadata():
    assert ScenarioItem.__tablename__ in SQLModel.metadata.tables
    assert ScenarioAttempt.__tablename__ in SQLModel.metadata.tables


def test_scenario_migration_upgrade_schema_and_downgrade(tmp_path, monkeypatch):
    database_path = tmp_path / "scenario_migration.db"
    monkeypatch.setattr(settings, "database_url", f"sqlite:///{database_path}")

    config = Config(
        str(Path(__file__).parents[1] / "alembic.ini")
    )
    config.set_main_option(
        "script_location",
        str(Path(__file__).parents[1] / "migrations"),
    )

    command.upgrade(config, "head")

    engine = create_engine(f"sqlite:///{database_path}")
    database_inspector = inspect(engine)

    assert "scenario_items" in database_inspector.get_table_names()
    assert "scenario_attempts" in database_inspector.get_table_names()

    scenario_item_foreign_keys = {
        (foreign_key["constrained_columns"][0], foreign_key["referred_table"], foreign_key["referred_columns"][0])
        for foreign_key in database_inspector.get_foreign_keys("scenario_items")
    }
    assert scenario_item_foreign_keys == {
        ("competency_id", "competencies", "id"),
        ("subskill_id", "subskills", "id"),
    }

    scenario_attempt_foreign_keys = {
        (foreign_key["constrained_columns"][0], foreign_key["referred_table"], foreign_key["referred_columns"][0])
        for foreign_key in database_inspector.get_foreign_keys("scenario_attempts")
    }
    assert scenario_attempt_foreign_keys == {
        ("user_id", "users", "id"),
        ("scenario_id", "scenario_items", "id"),
    }

    assert {
        index["name"] for index in database_inspector.get_indexes("scenario_items")
    } == {
        "ix_scenario_items_competency_id",
        "ix_scenario_items_subskill_id",
    }
    assert {
        index["name"] for index in database_inspector.get_indexes("scenario_attempts")
    } == {
        "ix_scenario_attempts_user_id",
        "ix_scenario_attempts_scenario_id",
    }

    constraints = {
        constraint["name"]
        for constraint in database_inspector.get_check_constraints("scenario_attempts")
    }
    assert constraints == {
        "ck_scenario_attempt_score_range",
        "ck_scenario_attempt_percentage_range",
        "ck_scenario_attempt_confidence_range",
    }

    command.downgrade(config, "ac1d2e3f4a5b")
    assert "scenario_items" not in inspect(engine).get_table_names()
    assert "scenario_attempts" not in inspect(engine).get_table_names()
    engine.dispose()