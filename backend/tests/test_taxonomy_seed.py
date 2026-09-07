from collections import Counter

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlmodel import SQLModel

from app.models.competency import Competency, CompetencyDomain, Role, RoleCompetency, SubSkill
from app.seed import seed_data
from app.seed_data.competency_taxonomy import ROLES, taxonomy_counts

REQUIRED_ROLES = {role.name for role in ROLES}
REQUIRED_DOMAINS = {domain for domain in CompetencyDomain}


@pytest.fixture
def seeded_db(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    monkeypatch.setattr("app.seed_data.runner.SessionLocal", session_factory)
    seed_data("taxonomy-test-password")
    yield session_factory
    engine.dispose()


def test_seed_all_roles_created(seeded_db):
    with seeded_db() as db:
        role_names = {name for (name,) in db.execute(select(Role.name)).all()}
    assert REQUIRED_ROLES.issubset(role_names)


def test_seed_four_domains_populated(seeded_db):
    with seeded_db() as db:
        domains = {domain for (domain,) in db.execute(select(Competency.domain)).all()}
    assert REQUIRED_DOMAINS == domains


def test_seed_subskill_count_minimum(seeded_db):
    with seeded_db() as db:
        assert db.scalar(select(func.count()).select_from(SubSkill)) >= 140


def test_seed_role_competency_mapping(seeded_db):
    with seeded_db() as db:
        counts = dict(
            db.execute(
                select(Role.name, func.count(RoleCompetency.competency_id))
                .join(RoleCompetency, RoleCompetency.role_id == Role.id)
                .group_by(Role.id)
            ).all()
        )
    assert all(counts.get(role_name, 0) >= 3 for role_name in REQUIRED_ROLES)


def test_seed_competency_subskill_mapping(seeded_db):
    with seeded_db() as db:
        counts = dict(
            db.execute(
                select(Competency.id, func.count(SubSkill.id))
                .join(SubSkill, SubSkill.competency_id == Competency.id)
                .group_by(Competency.id)
            ).all()
        )
    assert len(counts) >= 40
    assert all(count >= 2 for count in counts.values())


def test_seed_no_orphan_subskills(seeded_db):
    with seeded_db() as db:
        orphan_count = db.scalar(
            select(func.count()).select_from(SubSkill).outerjoin(Competency, SubSkill.competency_id == Competency.id).where(Competency.id.is_(None))
        )
    assert orphan_count == 0


def test_seed_idempotent(seeded_db):
    seed_data("taxonomy-test-password")
    with seeded_db() as db:
        first_counts = {
            "roles": db.scalar(select(func.count()).select_from(Role)),
            "competencies": db.scalar(select(func.count()).select_from(Competency)),
            "subskills": db.scalar(select(func.count()).select_from(SubSkill)),
            "links": db.scalar(select(func.count()).select_from(RoleCompetency)),
        }
    seed_data("taxonomy-test-password")
    with seeded_db() as db:
        second_counts = {
            "roles": db.scalar(select(func.count()).select_from(Role)),
            "competencies": db.scalar(select(func.count()).select_from(Competency)),
            "subskills": db.scalar(select(func.count()).select_from(SubSkill)),
            "links": db.scalar(select(func.count()).select_from(RoleCompetency)),
        }
    assert first_counts == second_counts


def test_taxonomy_counts_match_target():
    role_count, domain_count, competency_count, subskill_count = taxonomy_counts()
    assert role_count == 8
    assert domain_count == 4
    assert competency_count == 40
    assert subskill_count >= 140
