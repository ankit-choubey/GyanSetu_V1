from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.competency import Competency, SubSkill
from app.models.intervention import Intervention
from app.services.adapters import (
    AvailabilityStatus,
    HealthStatus,
    IGOTAdapter,
    InternalAdapter,
    NSSTAAdapter,
    TPACAdapter,
    VirtualLabAdapter,
    get_adapter_for_provider,
    list_all_adapters,
)
from app.services.ecosystem import (
    CompetencyMappingService,
    EcosystemSyncService,
)


@pytest.fixture(scope="module", autouse=True)
def setup_module_data():
    from sqlmodel import SQLModel
    from app.database import engine, SessionLocal
    from app.models.competency import Role
    from app.seed_data.runner import seed_full_taxonomy
    from app.seed_data.intervention_catalog_loader import seed_intervention_catalog
    SQLModel.metadata.create_all(engine)
    db = SessionLocal()
    try:
        if not db.execute(select(Role)).scalars().first():
            seed_full_taxonomy("test-pass")
        seed_intervention_catalog(db)

    finally:
        db.close()


@pytest.fixture
def test_db_session():
    from fastapi.testclient import TestClient
    from app.database import SessionLocal
    from app.main import app

    with TestClient(app):
        db = SessionLocal()
        try:
            yield db
        finally:

            db.close()


def test_all_adapters_satisfy_contract():
    """Verify that every provider adapter satisfies the comprehensive InterventionProvider contract."""
    adapters = list_all_adapters()
    assert len(adapters) >= 5

    for adapter in adapters:
        name = adapter.get_provider_name()
        mode = adapter.get_integration_mode()
        assert isinstance(name, str) and len(name) > 0
        assert mode.value in ("LIVE", "SANDBOX", "REPLAY", "NOT_CONFIGURED")

        # Health Check contract
        health = adapter.health_check()
        assert health.provider == name
        assert health.status in (HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNAVAILABLE)
        assert health.latency_ms >= 0.0

        # General Availability Check
        avail = adapter.check_availability()
        assert avail.status == AvailabilityStatus.AVAILABLE
        assert avail.is_available is True

        # Sync Contract
        resources = adapter.sync_resources()
        assert isinstance(resources, list)
        if len(resources) > 0:
            sample = resources[0]
            assert sample.provider == name
            assert sample.provider_resource_id
            assert sample.title
            assert sample.intervention_type

            # Launch Contract on sample resource
            launch = adapter.launch_resource(sample.provider_resource_id, learner_id=42)
            assert launch.provider == name
            assert launch.provider_resource_id == sample.provider_resource_id
            assert launch.provider_activity_id
            assert launch.learner_id == 42
            assert launch.status in ("ACTIVE", "INITIALIZED")


def test_provider_mode_reporting_and_fallback_reason():
    """Verify explicit mode reporting and fallback explanation for unconfigured live services."""
    igot = IGOTAdapter()
    assert igot.get_integration_mode().value == "REPLAY"
    assert igot.get_requested_mode().value == "LIVE"
    assert "iGOT Karmayogi API unconfigured" in igot.get_fallback_reason()

    nssta = NSSTAAdapter()
    assert nssta.get_integration_mode().value == "REPLAY"
    assert nssta.get_requested_mode().value == "LIVE"
    assert "NSSTA" in nssta.get_fallback_reason()

    vlab = VirtualLabAdapter()
    assert vlab.get_integration_mode().value == "SANDBOX"

    internal = InternalAdapter()
    assert internal.get_integration_mode().value == "LIVE"


def test_adapter_fault_simulations():
    """Verify that all adapters correctly catch simulated outages, timeouts, and auth failures."""
    for adapter in [IGOTAdapter(), NSSTAAdapter(), VirtualLabAdapter(), InternalAdapter()]:
        # Outage simulation
        adapter.set_simulated_availability(False)
        res_outage = adapter.check_availability()
        assert res_outage.is_available is False
        assert res_outage.status == AvailabilityStatus.UNAVAILABLE
        h_outage = adapter.health_check()
        assert h_outage.status == HealthStatus.UNAVAILABLE

        # Reset availability
        adapter.set_simulated_availability(True)
        assert adapter.check_availability().is_available is True

        # Timeout simulation
        adapter.simulate_timeout(True)
        res_timeout = adapter.check_availability()
        assert res_timeout.is_available is False
        assert res_timeout.status == AvailabilityStatus.PROVIDER_ERROR
        adapter.simulate_timeout(False)

        # Auth failure simulation
        adapter.simulate_auth_failure(True)
        res_auth = adapter.check_availability()
        assert res_auth.is_available is False
        assert res_auth.status == AvailabilityStatus.NOT_AUTHORIZED
        adapter.simulate_auth_failure(False)


def test_competency_mapping_taxonomy_resolution(test_db_session: Session):
    """Test explicit competency mapping boundary, statuses, and safe isolation of unverified concepts."""
    mapper = CompetencyMappingService(test_db_session)

    # 1. Exact canonical match
    res_exact = mapper.resolve_mapping("Sampling Design", "Stratified sampling")
    assert res_exact.status == "VERIFIED"
    assert res_exact.confidence == 1.0
    assert res_exact.competency_id is not None

    # 2. Curated synonym match
    res_curated = mapper.resolve_mapping("consumer price index", "cpi compilation")
    assert res_curated.status == "CURATED"
    assert res_curated.confidence == 0.95
    assert res_curated.competency_name == "Index Numbers"

    # 3. Fuzzy partial match
    res_fuzzy = mapper.resolve_mapping("Advanced Sampling Methods")
    assert res_fuzzy.status == "PROVISIONAL"
    assert res_fuzzy.confidence >= 0.70

    # 4. Unknown / Malformed concept -> quarantined as UNDER_REVIEW
    res_unknown = mapper.resolve_mapping("Astrology and Palmistry for Statistics")
    assert res_unknown.status == "UNDER_REVIEW"
    assert res_unknown.competency_id is None
    assert res_unknown.confidence <= 0.20


def test_ecosystem_sync_idempotency_and_deduplication(test_db_session: Session):
    """Verify that repeated synchronization runs are strictly idempotent and prevent duplicates."""
    sync_service = EcosystemSyncService(test_db_session)

    # First sync run
    summary1 = sync_service.sync_provider("iGOT")
    assert summary1.total_processed >= 5

    # Second sync run on the same provider
    summary2 = sync_service.sync_provider("iGOT")
    assert summary2.added_count == 0  # No duplicates created
    assert summary2.updated_count == summary1.total_processed

    # Verify database count has no duplicate source_ids
    items = test_db_session.execute(
        select(Intervention).where(Intervention.provider == "iGOT")
    ).scalars().all()
    source_ids = [item.source_id for item in items]
    assert len(source_ids) == len(set(source_ids)), "Duplicate provider source_ids detected in database!"
