/**
 * GyanSetu — Competency Intelligence Platform
 * TypeScript Data Models mirroring the Backend API Contract (dashboard_plan.md §1)
 */

export interface BackendCompetency {
  competency_id: number;
  competency_name: string;
  mastery: number | null; // float | null (null = UNASSESSED, never treat as 0)
  confidence: number; // float 0.0–1.0
  coverage: number; // float 0.0–1.0
  evidence_count: number; // int
  status: "UNASSESSED" | "ASSESSED" | "CONFLICTING_EVIDENCE";
}

export interface NextBestActionResponse {
  target_subskill_id: number | null;
  gap_reason: string;
  selected_intervention: {
    id: number;
    title: string;
    type: string; // "PRACTICE" | "TRAINING"
    reason: string;
  };
  explanation: string;
  uncertainty: number | null;
}

export interface DashboardResponse {
  user_id: number;
  full_name: string;
  role_name: string;
  designation?: string;
  department?: string;
  total_competencies: number;
  competencies: BackendCompetency[];
  evaluations_completed?: number;
  total_evidence_records?: number;
  next_best_action?: NextBestActionResponse | null;
}

export interface AdaptiveQuestionResponse {
  status: "QUESTION_PROPOSED" | "SUFFICIENT_EVIDENCE";
  sufficient_evidence: boolean;
  stop_reason?: string | null;
  question_id?: number;
  competency_id?: number;
  subskill_id?: number;
  question_text?: string;
  options?: string[];
  difficulty?: "easy" | "medium" | "hard";
}

export interface QuestionFeedbackItem {
  question_id: number;
  selected: string;
  is_correct: boolean;
  feedback: string;
  identified_gap?: string | null;
}

export interface AssessmentSubmitResponse {
  status: string;
  message: string;
  assessment_id: number;
  score: number;
  feedback: QuestionFeedbackItem[];
  competency_status: string;
  mastery: number;
  confidence: number;
  next_best_action?: NextBestActionResponse | null;
}

export interface CompetencyAnalytics {
  role_id: number;
  role_name: string;
  competency_id: number;
  competency_name: string;
  learner_count: number;
  assessed_count: number;
  average_mastery: number;
  average_confidence: number;
  average_coverage: number;
  total_evidence: number;
  status_distribution: {
    ASSESSED: number;
    UNASSESSED: number;
    CONFLICTING_EVIDENCE?: number;
  };
}

export interface AdminAnalyticsResponse {
  total_competencies: number;
  competencies: CompetencyAnalytics[];
}

export interface TaskItem {
  id: number;
  title: string;
  description: string;
  type: "PRACTICE" | "TRAINING";
  competency_name: string;
  priority: number;
  status: "active" | "completed" | "not_started";
  progress_pct: number;
  due_date: string;
}

export interface TaskSummary {
  active: number;
  completed: number;
  total: number;
}

export interface TasksResponse {
  tasks: TaskItem[];
  summary: TaskSummary;
}

export interface RadarDataPoint {
  axis: string;
  current: number;
  target: number;
  fullMark: number;
  isUnassessed?: boolean;
  evidence_count?: number;
}

export interface ActiveGapDerived {
  competency_id: number;
  competency_name: string;
  mastery: number | null;
  confidence: number;
  coverage: number;
  evidence_count: number;
}

export interface KPISummaryDerived {
  mastery_avg: number | null;
  confidence_avg: number;
  coverage_avg: number;
  assessed_count: number;
  total_count: number;
}

export interface StudyLibraryItem {
  id: number;
  title: string;
  source_type: "pdf" | "pptx" | "youtube" | string;
  source_url?: string | null;
  filename?: string | null;
  file_size: number;
  competency_mapped: string;
  summary?: string | null;
  concepts: string[];
  questions_count: number;
  has_file: boolean;
  created_at: string | null;
}

