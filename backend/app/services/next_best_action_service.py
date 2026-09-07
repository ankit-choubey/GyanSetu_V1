from __future__ import annotations

import json
import uuid
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.competency import Competency, RoleCompetency, SubSkill
from app.models.competency_state import CompetencyState
from app.models.intervention import Intervention
from app.models.misconception import Misconception
from app.models.recommendation import RecommendationRecord
from app.models.user import User
from app.services.eligibility_engine import EligibilityEngine
from app.services.recommendation_ranker import RecommendationRanker


class NextBestActionService:
    """Orchestrates gap identification, candidate generation, eligibility filtering, and next best action."""

    def __init__(
        self,
        eligibility_engine: EligibilityEngine | None = None,
        ranker: RecommendationRanker | None = None,
    ) -> None:
        self.eligibility_engine = eligibility_engine or EligibilityEngine()
        self.ranker = ranker or RecommendationRanker()

    def get_next_best_action(
        self,
        db: Session,
        learner: User,
        competency_id: int | None = None,
    ) -> RecommendationRecord:
        # 1. Identify Target Competency
        target_comp: Competency | None = None
        if competency_id is not None:
            target_comp = db.get(Competency, competency_id)

        if target_comp is None and learner.role_id is not None:
            # Query role required competencies and find highest gap
            role_comps = db.execute(
                select(RoleCompetency).where(RoleCompetency.role_id == learner.role_id)
            ).scalars().all()

            best_gap_comp_id = None
            max_gap = -1.0

            for rc in role_comps:
                st = db.execute(
                    select(CompetencyState).where(
                        CompetencyState.user_id == learner.id,
                        CompetencyState.competency_id == rc.competency_id,
                    )
                ).scalar_one_or_none()

                if st is None or st.mastery is None:
                    # Unassessed has top priority for diagnostic baseline
                    best_gap_comp_id = rc.competency_id
                    break
                else:
                    gap = rc.required_level - st.mastery
                    if gap > max_gap:
                        max_gap = gap
                        best_gap_comp_id = rc.competency_id

            if best_gap_comp_id is not None:
                target_comp = db.get(Competency, best_gap_comp_id)

        # If still no competency found, fallback to first available competency
        if target_comp is None:
            target_comp = db.execute(select(Competency)).scalars().first()

        cid = target_comp.id if target_comp else 1

        # 2. Inspect Learner Competency State for target competency
        state = db.execute(
            select(CompetencyState).where(
                CompetencyState.user_id == learner.id,
                CompetencyState.competency_id == cid,
            )
        ).scalar_one_or_none()

        # 3. COLD START HANDLING
        # CRITICAL PRINCIPLE: Missing evidence != low competency
        if state is None or state.mastery is None or state.status == "UNASSESSED":
            rec_id = f"rec_{uuid.uuid4().hex[:12]}"
            explanation = {
                "why": "Learner competency state is currently UNASSESSED with zero verified evidence.",
                "positive_factors": ["+ Foundational baseline evidence required"],
                "negative_factors": ["- Missing evidence must NOT be equated with low competency"],
                "caution_notes": ["Baseline diagnostic recommended before prescribing learning interventions."],
            }

            rec = RecommendationRecord(
                recommendation_id=rec_id,
                user_id=learner.id,
                competency_id=cid,
                action_type="DIAGNOSTIC",
                status="RECOMMENDED",
                objective=f"Complete diagnostic assessment on '{target_comp.name if target_comp else 'Competency'}' to establish baseline mastery.",
                confidence=0.0,
                policy_version=self.ranker.POLICY_VERSION,
                explanation_json=json.dumps(explanation),
                rejected_candidates_json=json.dumps([]),
                alternatives_json=json.dumps([]),
            )
            db.add(rec)
            db.commit()
            db.refresh(rec)
            return rec

        # 4. Check for active misconceptions
        active_misconceptions = db.execute(
            select(Misconception).where(
                Misconception.learner_id == learner.id,
                Misconception.resolved.is_(False),
            )
        ).scalars().all()

        target_subskill: SubSkill | None = None
        target_misconception: Misconception | None = None

        # If an active misconception belongs to subskills of this competency, prioritize it!
        for misc in active_misconceptions:
            sub = db.get(SubSkill, misc.subskill_id) if misc.subskill_id else None
            if sub and sub.competency_id == cid:
                target_subskill = sub
                target_misconception = misc
                break

        # If no misconception, pick first subskill of this competency
        if target_subskill is None:
            target_subskill = db.execute(
                select(SubSkill).where(SubSkill.competency_id == cid)
            ).scalars().first()

        sid = target_subskill.id if target_subskill else None
        sname = target_subskill.name if target_subskill else None

        # 5. Candidate Generation
        # Retrieve all candidate interventions from database catalogue
        candidates = db.execute(
            select(Intervention).where(
                or_(
                    Intervention.competency_id == cid,
                    Intervention.competency_id.is_(None),
                )
            )
        ).scalars().all()

        # If an active misconception exists, also retrieve specific remediation interventions matching the pattern
        if target_misconception and target_misconception.pattern_key:
            pattern_candidates = db.execute(
                select(Intervention).where(
                    Intervention.target_misconception_pattern == target_misconception.pattern_key
                )
            ).scalars().all()
            # Combine without duplicates
            cand_map = {c.id: c for c in candidates}
            for pc in pattern_candidates:
                cand_map[pc.id] = pc
            candidates = list(cand_map.values())

        # 6. Eligibility Filtering
        eligible_candidates, ineligible_decisions = self.eligibility_engine.filter_candidates(
            db, learner, candidates
        )

        # 7. Ranking & Explanation Generation
        ranking_result = self.ranker.rank(
            eligible_candidates=eligible_candidates,
            ineligible_decisions=ineligible_decisions,
            target_competency_id=cid,
            target_subskill_id=sid,
            target_subskill_name=sname,
            active_misconceptions=active_misconceptions,
            competency_state=state,
            gap_severity="HIGH" if (state.mastery or 0.0) < 0.40 else "MEDIUM",
        )

        rec_id = f"rec_{uuid.uuid4().hex[:12]}"

        # 8. Formulate Recommendation Record
        if ranking_result.selected is None:
            # NO_SUITABLE_INTERVENTION
            explanation = {
                "why": "No active intervention in the catalogue currently satisfies all eligibility criteria.",
                "positive_factors": [],
                "negative_factors": ["All candidate interventions were disqualified by eligibility filtering."],
                "caution_notes": ["An intervention catalogue entry must be curated or updated."],
            }
            rec = RecommendationRecord(
                recommendation_id=rec_id,
                user_id=learner.id,
                competency_id=cid,
                target_subskill_id=sid,
                selected_intervention_id=None,
                action_type="NO_SUITABLE_INTERVENTION",
                status="RECOMMENDED",
                objective="No suitable intervention available.",
                confidence=0.0,
                policy_version=self.ranker.POLICY_VERSION,
                explanation_json=json.dumps(explanation),
                rejected_candidates_json=json.dumps(ranking_result.rejected_candidates),
                alternatives_json=json.dumps([]),
            )
        else:
            sel = ranking_result.selected
            explanation = {
                "why": sel.primary_reason,
                "positive_factors": sel.positive_factors,
                "negative_factors": sel.negative_factors,
                "caution_notes": sel.caution_notes,
                "score": sel.total_score,
                "relevance": sel.relevance,
            }

            alternatives = [
                {
                    "intervention_id": alt.intervention.id,
                    "title": alt.intervention.title,
                    "provider": alt.intervention.provider,
                    "intervention_type": alt.intervention.intervention_type,
                    "score": alt.total_score,
                    "reason": alt.primary_reason,
                }
                for alt in ranking_result.ranked_options[1:4]
            ]

            rec = RecommendationRecord(
                recommendation_id=rec_id,
                user_id=learner.id,
                competency_id=cid,
                target_subskill_id=sid,
                selected_intervention_id=sel.intervention.id,
                action_type="INTERVENTION",
                status="RECOMMENDED",
                objective=f"Develop capability in '{target_comp.name}' focusing on '{sname}'.",
                confidence=sel.relevance,
                policy_version=self.ranker.POLICY_VERSION,
                explanation_json=json.dumps(explanation),
                rejected_candidates_json=json.dumps(ranking_result.rejected_candidates),
                alternatives_json=json.dumps(alternatives),
            )

        db.add(rec)
        db.commit()
        db.refresh(rec)
        return rec
