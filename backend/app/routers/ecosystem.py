from __future__ import annotations

from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_admin, get_current_user
from app.models.intervention import Intervention
from app.models.user import User
from app.schemas.ecosystem import (
    EcosystemOutcomeRequest,
    EcosystemOutcomeResponse,
    EcosystemResourceResponse,
    LaunchInterventionResponse,
    ProviderHealthResponse,
    ProviderSyncResponse,
)
from app.services.adapters import (
    InterventionAdapter,
    get_adapter_for_provider,
    list_all_adapters,
)
from app.services.ecosystem.outcome_service import EcosystemOutcomeService
from app.services.ecosystem.sync_service import EcosystemSyncService

router = APIRouter(prefix="/ecosystem", tags=["ecosystem"])


@router.get("/providers", response_model=List[ProviderHealthResponse])
def get_providers_overview(
    current_user: User = Depends(get_current_user),
) -> List[ProviderHealthResponse]:
    """Retrieve runtime health and integration status across all ecosystem provider adapters."""
    results: list[ProviderHealthResponse] = []
    for adapter in list_all_adapters():
        h = adapter.health_check()
        results.append(
            ProviderHealthResponse(
                provider=h.provider,
                status=h.status.value,
                mode=h.mode.value,
                latency_ms=h.latency_ms,
                resource_count=h.resource_count,
                details=h.details,
                checked_at=h.checked_at.isoformat(),
            )
        )
    return results


@router.get("/providers/{provider}/health", response_model=ProviderHealthResponse)
def get_provider_health(
    provider: str,
    current_user: User = Depends(get_current_user),
) -> ProviderHealthResponse:
    """Inspect the live health, responsiveness, and mode of a specific provider adapter."""
    adapter = get_adapter_for_provider(provider)
    if adapter.get_provider_name().upper() != provider.upper():
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found in registry")
    h = adapter.health_check()
    return ProviderHealthResponse(
        provider=h.provider,
        status=h.status.value,
        mode=h.mode.value,
        latency_ms=h.latency_ms,
        resource_count=h.resource_count,
        details=h.details,
        checked_at=h.checked_at.isoformat(),
    )


@router.post("/providers/{provider}/sync", response_model=ProviderSyncResponse)
def sync_provider_catalog(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProviderSyncResponse:
    """Trigger idempotent catalog synchronization and deduplication for a provider."""
    adapter = get_adapter_for_provider(provider)
    if adapter.get_provider_name().upper() != provider.upper():
        raise HTTPException(status_code=404, detail=f"Provider '{provider}' not found in registry")

    sync_service = EcosystemSyncService(db)
    summary = sync_service.sync_provider(provider_name=provider, adapter=adapter)

    return ProviderSyncResponse(
        provider=summary.provider,
        mode=summary.mode,
        added_count=summary.added_count,
        updated_count=summary.updated_count,
        skipped_count=summary.skipped_count,
        rejected_count=summary.rejected_count,
        total_processed=summary.total_processed,
        synced_at=summary.synced_at.isoformat(),
    )


@router.get("/resources", response_model=List[EcosystemResourceResponse])
def list_ecosystem_resources(
    provider: Optional[str] = None,
    mode: Optional[str] = None,
    status: Optional[str] = Query(default="ACTIVE"),
    competency_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[EcosystemResourceResponse]:
    """List normalized canonical resources across providers with filtering."""
    query = select(Intervention)
    if provider:
        query = query.where(Intervention.provider == provider.upper())
    if mode:
        query = query.where(Intervention.integration_mode == mode.upper())
    if status:
        query = query.where(Intervention.status == status)
    if competency_id:
        query = query.where(Intervention.competency_id == competency_id)

    items = db.execute(query).scalars().all()
    results: list[EcosystemResourceResponse] = []
    for item in items:
        results.append(
            EcosystemResourceResponse(
                id=item.id,
                provider=item.provider,
                source_id=item.source_id,
                title=item.title,
                description=item.description,
                intervention_type=item.intervention_type,
                modality=item.modality,
                duration_minutes=item.duration_minutes,
                difficulty=item.difficulty,
                competency_id=item.competency_id,
                subskill_id=item.subskill_id,
                status=item.status,
                availability=item.availability,
                integration_mode=item.integration_mode,
                mapping_status=item.mapping_status,
                mapping_confidence=item.mapping_confidence,
                provenance=item.provenance,
                source_url=item.source_url,
                last_verified_at=item.last_verified_at,
                last_synced_at=item.last_synced_at,
            )
        )
    return results


@router.get("/resources/{id}", response_model=EcosystemResourceResponse)
def get_ecosystem_resource(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcosystemResourceResponse:
    """Retrieve detailed metadata and mapping status for a canonical intervention resource."""
    item = db.get(Intervention, id)
    if not item:
        raise HTTPException(status_code=404, detail="Resource not found")
    return EcosystemResourceResponse(
        id=item.id,
        provider=item.provider,
        source_id=item.source_id,
        title=item.title,
        description=item.description,
        intervention_type=item.intervention_type,
        modality=item.modality,
        duration_minutes=item.duration_minutes,
        difficulty=item.difficulty,
        competency_id=item.competency_id,
        subskill_id=item.subskill_id,
        status=item.status,
        availability=item.availability,
        integration_mode=item.integration_mode,
        mapping_status=item.mapping_status,
        mapping_confidence=item.mapping_confidence,
        provenance=item.provenance,
        source_url=item.source_url,
        last_verified_at=item.last_verified_at,
        last_synced_at=item.last_synced_at,
    )


@router.post("/resources/{id}/launch", response_model=LaunchInterventionResponse)
def launch_ecosystem_resource(
    id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> LaunchInterventionResponse:
    """Launch or reference external intervention resource and record external activity ID."""
    outcome_service = EcosystemOutcomeService(db)
    result = outcome_service.launch_intervention(intervention_id=id, current_user=current_user)
    return LaunchInterventionResponse(
        provider=result.provider,
        provider_resource_id=result.provider_resource_id,
        provider_activity_id=result.provider_activity_id,
        learner_id=result.learner_id,
        integration_mode=result.integration_mode,
        launch_url=result.launch_url,
        status=result.status,
        launched_at=result.launched_at.isoformat(),
    )


@router.post("/resources/{id}/outcome", response_model=EcosystemOutcomeResponse)
def record_ecosystem_outcome(
    id: int,
    payload: EcosystemOutcomeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> EcosystemOutcomeResponse:
    """Record an external intervention completion outcome with idempotency and non-mastery enforcement."""
    outcome_service = EcosystemOutcomeService(db)
    result = outcome_service.record_external_outcome(
        intervention_id=id,
        current_user=current_user,
        status=payload.status,
        completion_score=payload.completion_score,
        has_post_assessment_evidence=payload.has_post_assessment_evidence,
        provider_activity_id=payload.provider_activity_id,
        idempotency_key=payload.idempotency_key,
        notes=payload.notes,
    )
    return EcosystemOutcomeResponse(**result)
