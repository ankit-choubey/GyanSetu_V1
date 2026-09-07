import {
  DashboardResponse,
  BackendCompetency,
  RadarDataPoint,
  ActiveGapDerived,
  KPISummaryDerived,
  AdaptiveQuestionResponse,
  AssessmentSubmitResponse,
  AdminAnalyticsResponse,
  TasksResponse,
} from "./types";
import { client } from "./client";
import jsoMockData from "@/lib/mock/officer-jso.json";
import newOfficerMockData from "@/lib/mock/officer-new.json";

// --- Synchronous Mock Readers ---

export function getCompetencyStateSync(
  persona: "jso" | "new" | "admin" = "jso"
): DashboardResponse {
  if (persona === "new") {
    return newOfficerMockData as unknown as DashboardResponse;
  }
  return jsoMockData as unknown as DashboardResponse;
}

export async function getCompetencyState(
  persona: "jso" | "new" | "admin" = "jso"
): Promise<DashboardResponse> {
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

  if (useMock) {
    return getCompetencyStateSync(persona);
  }

  try {
    const res = await client.get<DashboardResponse>("/api/dashboard/learner");
    if (res && res.competencies && res.competencies.length > 0) {
      return res;
    }
    return getCompetencyStateSync(persona);
  } catch (err) {
    console.warn("Backend /api/dashboard/learner error, falling back to persona data:", err);
    return getCompetencyStateSync(persona);
  }
}

// --- Derivation Helpers (§1.1 Ground Truth) ---

export function deriveKPISummary(dashboard: DashboardResponse): KPISummaryDerived {
  const competencies = dashboard.competencies || [];
  const assessed = competencies.filter((c) => c.mastery !== null);

  const mastery_avg =
    assessed.length > 0
      ? assessed.reduce((sum, c) => sum + (c.mastery ?? 0), 0) / assessed.length
      : null;

  const confidence_avg =
    competencies.length > 0
      ? competencies.reduce((sum, c) => sum + (c.confidence || 0), 0) /
        competencies.length
      : 0;

  const coverage_avg =
    competencies.length > 0
      ? competencies.reduce((sum, c) => sum + (c.coverage || 0), 0) /
        competencies.length
      : 0;

  return {
    mastery_avg,
    confidence_avg,
    coverage_avg,
    assessed_count: assessed.length,
    total_count: dashboard.total_competencies || competencies.length,
  };
}

export function deriveRadarData(
  competencies: BackendCompetency[]
): RadarDataPoint[] {
  return (competencies || []).map((c) => ({
    axis: c.competency_name,
    current: c.mastery !== null ? Math.round(c.mastery * 100) : 0,
    target: 80,
    fullMark: 100,
    isUnassessed: c.mastery === null,
    evidence_count: c.evidence_count,
  }));
}

export function deriveActiveGap(
  competencies: BackendCompetency[]
): ActiveGapDerived | null {
  if (!competencies || competencies.length === 0) return null;

  // Find lowest non-null mastery first
  const assessed = competencies.filter((c) => c.mastery !== null);
  if (assessed.length > 0) {
    const lowest = [...assessed].sort(
      (a, b) => (a.mastery ?? 0) - (b.mastery ?? 0)
    )[0];
    return {
      competency_id: lowest.competency_id,
      competency_name: lowest.competency_name,
      mastery: lowest.mastery,
      confidence: lowest.confidence,
      coverage: lowest.coverage,
      evidence_count: lowest.evidence_count,
    };
  }

  // Fallback to first competency if all unassessed
  const first = competencies[0];
  return {
    competency_id: first.competency_id,
    competency_name: first.competency_name,
    mastery: null,
    confidence: first.confidence,
    coverage: first.coverage,
    evidence_count: first.evidence_count,
  };
}

// --- Assessment API Handlers ---

export async function fetchAssessmentNext(params: {
  competency_id?: number;
  subskill_id?: number;
}): Promise<AdaptiveQuestionResponse> {
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
  if (useMock) {
    return {
      status: "QUESTION_PROPOSED",
      sufficient_evidence: false,
      question_id: 101,
      competency_id: params.competency_id || 1,
      subskill_id: params.subskill_id || 2,
      question_text:
        "When conducting stratified sampling under Neyman allocation, which condition necessitates allocating a larger sample size to a given stratum?",
      options: [
        "A. The stratum has a higher variance and lower sampling cost.",
        "B. The stratum has a smaller overall population size.",
        "C. The stratum contains uniform non-response items.",
        "D. The stratum has zero internal variance.",
      ],
      difficulty: "medium",
    };
  }

  return client.post<AdaptiveQuestionResponse>("/api/assessment/next", params);
}

export async function submitAssessment(params: {
  competency_id: number;
  question_id: number;
  selected_option: string;
}): Promise<AssessmentSubmitResponse> {
  const useMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";
  if (useMock) {
    const isCorrect = params.selected_option.startsWith("A");
    return {
      status: "success",
      message: "Assessment submitted successfully",
      assessment_id: 10,
      score: isCorrect ? 1.0 : 0.0,
      feedback: [
        {
          question_id: params.question_id,
          selected: params.selected_option,
          is_correct: isCorrect,
          feedback: isCorrect
            ? "Correct! Neyman allocation allocates sample size proportional to stratum size and stratum standard deviation."
            : "Incorrect. Under Neyman allocation, larger sample sizes are assigned to strata with higher standard deviations.",
          identified_gap: isCorrect ? null : "Neyman Allocation Variance Weighting",
        },
      ],
      competency_status: "ASSESSED",
      mastery: isCorrect ? 0.65 : 0.45,
      confidence: 0.6,
      next_best_action: {
        target_subskill_id: 2,
        gap_reason: isCorrect ? "practice_continuation" : "low_mastery",
        selected_intervention: {
          id: 3,
          title: "Stratified Variance & Neyman Allocation Drill",
          type: "PRACTICE",
          reason: isCorrect
            ? "Reinforce optimal sample allocation across multi-strata survey datasets."
            : "Address conceptual gap in Neyman allocation variance estimation formula.",
        },
        explanation:
          "Targeted practice drill with 3 realistic survey allocation scenarios.",
        uncertainty: 0.2,
      },
    };
  }

  return client.post<AssessmentSubmitResponse>("/api/assessment/submit", params);
}
