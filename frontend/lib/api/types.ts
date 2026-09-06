/**
 * GyanSetu — Competency Intelligence Platform
 * TypeScript Data Models mirroring the Build Guide (§12, §29) and Dashboard Plan (§2)
 */

export type EvidenceType =
  | "ASSESSMENT"
  | "PRACTICAL_TASK"
  | "PROJECT"
  | "PEER_REVIEW"
  | "SELF_REPORT"
  | "CERTIFICATION";

export type CompetencyStatus =
  | "mastered"
  | "proficient"
  | "needs_improvement"
  | "unassessed";

export interface CompetencyMetric {
  id: number | string;
  name: string;
  domain: string;
  /**
   * Mastery range 0.0–1.0 or null.
   * NOTE (Honesty Rule): null = Unassessed / Unknown. NEVER treat null as 0.0 or failing.
   */
  mastery: number | null;
  /** Confidence in the measurement: 0.0–1.0 */
  confidence: number;
  /** Coverage of tested subskills: 0.0–1.0 (percentage) */
  coverage: number;
  /** Last assessed ISO date string or null if unassessed */
  last_assessed: string | null;
  /** Primary identified subskill gap */
  gap: string | null;
  gap_severity?: "low" | "medium" | "high";
  status: CompetencyStatus;
  /** Flagged if different evidence modalities disagree */
  conflicting_evidence?: boolean;
}

/**
 * 12 Explainability Fields for the Next-Best-Action (Build Guide §29)
 */
export interface NextBestAction {
  /** 1. The specific training/lab action proposed */
  selected_action: string;
  /** 2. Defensible causal justification */
  justification: string;
  /** 3. Relevance to official statistical officer duties */
  role_relevance: string;
  /** 4. Target competency mapped to KCM/TPAC */
  competency_alignment: string;
  /** 5. Specific subskills covered */
  subskill_coverage: string;
  /** 6. Prior knowledge or course prerequisites */
  prerequisites: string;
  /** 7. Urgency / severity of the gap */
  gap_severity: "High" | "Medium" | "Low";
  /** 8. Confidence level in the gap estimation */
  evidence_confidence: "High" | "Medium" | "Low";
  /** 9. Cognitive / workload readiness state */
  learner_state: string;
  /** 10. Platform delivery modality */
  modality: "iGOT Karmayogi" | "NSSTA Workshop" | "TPAC Practical" | "Self-Paced Lab";
  /** 11. Availability status */
  availability: "Immediate" | "Scheduled" | "Upcoming";
  /** 12. Measurable expected competency gain */
  expected_outcome: string;
}

export interface AgentActivity {
  id: string;
  agent: "Diagnostic" | "Competency Engine" | "Intervention" | "Monitoring";
  action: string;
  timestamp: string;
  status: "completed" | "in_progress" | "pending";
}

export interface OfficerProfile {
  name: string;
  role: string;
  cadre: string;
  designation: string;
  organization: string;
  posting: string;
}

export interface RadarDataPoint {
  axis: string;
  current: number;
  target: number;
  fullMark: number;
  isUnassessed?: boolean;
}

export interface ActiveGap {
  title: string;
  competency_name: string;
  severity: "high" | "medium" | "low";
  evidence_basis: string;
  impact: string;
  recommendation_action: string;
}

export interface KPISummary {
  mastery_avg: number | null;
  confidence_level: "Low" | "Medium" | "High";
  confidence_score: number;
  coverage_pct: number;
  recency_label: string;
  diversity_count: number;
  diversity_total: number;
}

export interface CompetencyState {
  _meta: {
    source: "SANDBOX DATA" | "LIVE API";
    persona: string;
    version: string;
  };
  officer: OfficerProfile;
  kpi_summary: KPISummary;
  competencies: CompetencyMetric[];
  radar_data: RadarDataPoint[];
  active_gap: ActiveGap;
  next_best_action: NextBestAction;
  agent_activity: AgentActivity[];
}
