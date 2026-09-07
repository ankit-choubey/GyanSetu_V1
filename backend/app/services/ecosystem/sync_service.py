from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.intervention import Intervention
from app.services.adapters import (
    CanonicalInterventionPayload,
    InterventionAdapter,
    get_adapter_for_provider,
    list_all_adapters,
)
from .competency_mapper import CompetencyMappingService


@dataclass
class SyncSummary:
    provider: str
    mode: str
    added_count: int = 0
    updated_count: int = 0
    skipped_count: int = 0
    rejected_count: int = 0
    total_processed: int = 0
    synced_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "mode": self.mode,
            "added_count": self.added_count,
            "updated_count": self.updated_count,
            "skipped_count": self.skipped_count,
            "rejected_count": self.rejected_count,
            "total_processed": self.total_processed,
            "synced_at": self.synced_at.isoformat(),
        }


class EcosystemSyncService:
    """Service to synchronize external ecosystem provider resources into GyanSetu system-of-record."""

    STALE_THRESHOLD_DAYS = 180

    def __init__(self, db: Session) -> None:
        self.db = db
        self.mapper = CompetencyMappingService(db)

    def sync_provider(
        self,
        provider_name: str,
        adapter: InterventionAdapter | None = None,
        force_refresh: bool = False,
    ) -> SyncSummary:
        if adapter is None:
            adapter = get_adapter_for_provider(provider_name)

        summary = SyncSummary(
            provider=adapter.get_provider_name(),
            mode=adapter.get_integration_mode().value,
        )

        resources: list[CanonicalInterventionPayload] = adapter.sync_resources()
        now = datetime.now(timezone.utc)
        stale_cutoff = now - timedelta(days=self.STALE_THRESHOLD_DAYS)

        for payload in resources:
            summary.total_processed += 1

            # 1. Resolve Competency Mapping
            mapping = self.mapper.resolve_mapping(
                competency_hint=payload.competency_hint,
                subskill_hint=payload.subskill_hint,
                provider=payload.provider,
            )

            # Determine intervention status
            item_status = payload.status
            if mapping.status == "UNDER_REVIEW":
                item_status = "UNDER_REVIEW"
                summary.rejected_count += 1
            elif payload.last_verified_at and payload.last_verified_at < stale_cutoff:
                item_status = "STALE"

            # 2. Check Deduplication by (provider, source_id)
            existing = self.db.execute(
                select(Intervention).where(
                    Intervention.provider == payload.provider,
                    Intervention.source_id == payload.provider_resource_id,
                )
            ).scalar_one_or_none()

            metadata_str = (
                json.dumps(payload.external_metadata) if payload.external_metadata else None
            )

            if existing:
                # Update existing record idempotently
                existing.title = payload.title
                existing.description = payload.description
                existing.intervention_type = payload.intervention_type
                existing.modality = payload.modality
                existing.duration_minutes = payload.duration_minutes
                existing.difficulty = payload.difficulty
                existing.competency_id = mapping.competency_id
                existing.subskill_id = mapping.subskill_id
                existing.prerequisites_json = payload.prerequisites_json
                existing.source_url = payload.external_url
                existing.provenance = payload.provenance
                existing.version = payload.version
                existing.status = item_status
                existing.integration_mode = payload.integration_mode
                existing.external_metadata_json = metadata_str
                existing.mapping_status = mapping.status
                existing.mapping_confidence = mapping.confidence
                existing.last_synced_at = now
                summary.updated_count += 1
            else:
                # Insert new canonical record
                new_item = Intervention(
                    provider=payload.provider,
                    source_id=payload.provider_resource_id,
                    title=payload.title,
                    description=payload.description,
                    intervention_type=payload.intervention_type,
                    modality=payload.modality,
                    duration_minutes=payload.duration_minutes,
                    difficulty=payload.difficulty,
                    competency_id=mapping.competency_id,
                    subskill_id=mapping.subskill_id,
                    prerequisites_json=payload.prerequisites_json,
                    source="ECOSYSTEM_SYNC",
                    source_url=payload.external_url,
                    provenance=payload.provenance,
                    version=payload.version,
                    status=item_status,
                    integration_mode=payload.integration_mode,
                    external_metadata_json=metadata_str,
                    mapping_status=mapping.status,
                    mapping_confidence=mapping.confidence,
                    last_synced_at=now,
                    last_verified_at=payload.last_verified_at,
                    target_misconception_pattern=payload.target_misconception_pattern,
                    priority=payload.priority,
                )
                self.db.add(new_item)
                summary.added_count += 1

        self.db.commit()
        return summary

    def sync_all_providers(self) -> dict[str, SyncSummary]:
        results: dict[str, SyncSummary] = {}
        for adapter in list_all_adapters():
            name = adapter.get_provider_name()
            results[name] = self.sync_provider(name, adapter=adapter)
        return results
