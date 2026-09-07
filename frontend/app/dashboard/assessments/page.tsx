"use client";

import React, { useEffect, useState, useMemo, useCallback } from "react";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import {
  getCompetencyState,
  getCompetencyStateSync,
  deriveKPISummary,
  fetchAssessmentNext,
  submitAssessment,
} from "@/lib/api/competency";
import {
  DashboardResponse,
  BackendCompetency,
  AdaptiveQuestionResponse,
  AssessmentSubmitResponse,
} from "@/lib/api/types";
import { AssessmentStatCards } from "@/components/ui/assessments/AssessmentStatCards";
import { CompetencyAssessmentCard } from "@/components/ui/assessments/CompetencyAssessmentCard";
import { QuestionPanel } from "@/components/ui/assessments/QuestionPanel";
import { ResultsPanel } from "@/components/ui/assessments/ResultsPanel";
import { DashboardSkeleton } from "@/components/ui/dashboard/states/CardSkeleton";
import { ErrorState } from "@/components/ui/dashboard/states/ErrorState";

export default function AssessmentsPage() {
  const { persona } = useDashboard();
  const [data, setData] = useState<DashboardResponse>(() =>
    getCompetencyStateSync(persona)
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Assessment flow modal state
  const [activeCompetency, setActiveCompetency] = useState<BackendCompetency | null>(null);
  const [activeQuestion, setActiveQuestion] = useState<AdaptiveQuestionResponse | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [assessmentResult, setAssessmentResult] = useState<AssessmentSubmitResponse | null>(null);

  // Sync state on persona change
  useEffect(() => {
    let isSubscribed = true;
    const isMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

    if (isMock) {
      setData(getCompetencyStateSync(persona));
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    getCompetencyState(persona)
      .then((res) => {
        if (isSubscribed) {
          setData(res);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isSubscribed) {
          setError(err.message || "Failed to load competencies.");
          setIsLoading(false);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [persona]);

  const kpiSummary = useMemo(() => deriveKPISummary(data), [data]);

  // Handle starting assessment
  const handleStartAssessment = useCallback(async (comp: BackendCompetency) => {
    setActiveCompetency(comp);
    setAssessmentResult(null);
    try {
      const q = await fetchAssessmentNext({ competency_id: comp.competency_id });
      setActiveQuestion(q);
    } catch (e) {
      console.error("Failed to fetch adaptive question:", e);
    }
  }, []);

  // Handle answering question
  const handleSubmitAnswer = useCallback(
    async (selectedOption: string) => {
      if (!activeCompetency || !activeQuestion) return;
      setIsSubmitting(true);

      try {
        const result = await submitAssessment({
          competency_id: activeCompetency.competency_id,
          question_id: activeQuestion.question_id || 101,
          selected_option: selectedOption,
        });

        setAssessmentResult(result);

        // Optimistically update competency list in local state
        setData((prev) => ({
          ...prev,
          competencies: prev.competencies.map((c) =>
            c.competency_id === activeCompetency.competency_id
              ? {
                  ...c,
                  mastery: result.mastery,
                  confidence: result.confidence,
                  status: "ASSESSED",
                  evidence_count: c.evidence_count + 1,
                }
              : c
          ),
          next_best_action: result.next_best_action || prev.next_best_action,
        }));
      } catch (err) {
        console.error("Assessment submit error:", err);
      } finally {
        setIsSubmitting(false);
      }
    },
    [activeCompetency, activeQuestion]
  );

  const handleCloseFlow = useCallback(() => {
    setActiveCompetency(null);
    setActiveQuestion(null);
    setAssessmentResult(null);
  }, []);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Could not load assessments"
        message={error || "Unexpected error"}
        onRetry={() => {
          setIsLoading(true);
          getCompetencyState(persona)
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setIsLoading(false));
        }}
      />
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
          Assessments
        </h2>
        <p className="text-sm text-slate-500 font-sans mt-1">
          Take adaptive assessments to evaluate your competencies and calibrate your profile
        </p>
      </div>

      {/* ROW 1: STAT CARDS */}
      <AssessmentStatCards
        totalCompetencies={kpiSummary.total_count}
        assessedCount={kpiSummary.assessed_count}
        avgMastery={kpiSummary.mastery_avg}
      />

      {/* ROW 2: ASSESSMENT CARDS */}
      <section aria-labelledby="available-assessments-heading">
        <div className="flex items-center justify-between mb-4">
          <h3
            id="available-assessments-heading"
            className="font-heading text-lg sm:text-xl text-slate-900"
          >
            Available Competency Modules
          </h3>
          <span className="text-xs text-slate-500">
            {data.competencies.length} modules available
          </span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {data.competencies.map((c, index) => (
            <CompetencyAssessmentCard
              key={c.competency_id}
              competency={c}
              index={index}
              onStart={handleStartAssessment}
            />
          ))}
        </div>
      </section>

      {/* ACTIVE ASSESSMENT MODAL OVERLAY */}
      {activeCompetency && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          {assessmentResult ? (
            <ResultsPanel
              competencyName={activeCompetency.competency_name}
              result={assessmentResult}
              onFinish={handleCloseFlow}
            />
          ) : activeQuestion ? (
            <QuestionPanel
              competencyName={activeCompetency.competency_name}
              question={activeQuestion}
              isSubmitting={isSubmitting}
              onSubmit={handleSubmitAnswer}
              onCancel={handleCloseFlow}
            />
          ) : (
            <div className="bg-white rounded-xl p-8 max-w-sm w-full text-center">
              <div className="text-sm text-slate-600">Loading diagnostic question...</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
