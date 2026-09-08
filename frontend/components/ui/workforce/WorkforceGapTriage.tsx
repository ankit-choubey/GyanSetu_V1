"use client";

import React, { useState, useEffect } from "react";
import { AlertCircle, AlertTriangle, HelpCircle, ShieldAlert, Sparkles, BookOpen, CheckCircle2 } from "lucide-react";
import { client } from "@/lib/api/client";
import { cn } from "@/lib/cn";

export interface WorkforceGapItem {
  competency_id: number;
  competency_name: string;
  domain: string;
  affected_learners_count: number;
  mean_mastery: number;
  gap_severity: number;
  confidence: number;
  coverage: number;
  priority_score: number;
  classification: "ACTIONABLE" | "NEEDS_MORE_EVIDENCE" | string;
  urgency: "HIGH" | "MEDIUM" | string;
  intervention_available: boolean;
  intervention_options_count: number;
  why_prioritized: string;
}

export interface WorkforceGapsResponse {
  workforce_gaps: WorkforceGapItem[];
  total_gaps_identified: number;
  actionable_gaps_count: number;
  needs_more_evidence_count: number;
  governance_guardrail?: string;
}

const BASELINE_GAPS: WorkforceGapItem[] = [
  {
    competency_id: 3,
    competency_name: "Python for Official Statistics",
    domain: "STATISTICAL_COMPUTING",
    affected_learners_count: 14,
    mean_mastery: 0.46,
    gap_severity: 0.24,
    confidence: 0.58,
    coverage: 0.40,
    priority_score: 0.785,
    classification: "ACTIONABLE",
    urgency: "HIGH",
    intervention_available: true,
    intervention_options_count: 2,
    why_prioritized: "Observed gap (0.24) confirmed with sufficient evidence confidence (0.58) affecting 14 officers. 2 active NSSTA coding modules available.",
  },
  {
    competency_id: 1,
    competency_name: "Sampling Design & Variance Estimation",
    domain: "SURVEY_METHODOLOGY",
    affected_learners_count: 8,
    mean_mastery: 0.58,
    gap_severity: 0.12,
    confidence: 0.42,
    coverage: 0.35,
    priority_score: 0.620,
    classification: "ACTIONABLE",
    urgency: "MEDIUM",
    intervention_available: true,
    intervention_options_count: 1,
    why_prioritized: "Observed gap (0.12) confirmed with sufficient confidence affecting 8 officers. Targeted Neyman allocation drill ready.",
  },
  {
    competency_id: 4,
    competency_name: "National Accounts & SUTS Compilation",
    domain: "MACROECONOMIC_STATISTICS",
    affected_learners_count: 4,
    mean_mastery: 0.52,
    gap_severity: 0.18,
    confidence: 0.28,
    coverage: 0.20,
    priority_score: 0.490,
    classification: "NEEDS_MORE_EVIDENCE",
    urgency: "MEDIUM",
    intervention_available: false,
    intervention_options_count: 0,
    why_prioritized: "Observed gap (0.18) has preliminary confidence (0.28 < 0.35). Small-cell suppression active (N=4 < 5). Administer diagnostic before intervention.",
  },
];

export function WorkforceGapTriage({ className }: { className?: string }) {
  const [gaps, setGaps] = useState<WorkforceGapItem[]>(BASELINE_GAPS);
  const [isLive, setIsLive] = useState(false);

  useEffect(() => {
    let isSubscribed = true;

    client
      .get<WorkforceGapsResponse>("/api/workforce/gaps")
      .then((res) => {
        if (isSubscribed && res && res.workforce_gaps && res.workforce_gaps.length > 0) {
          setGaps(res.workforce_gaps);
          setIsLive(true);
        }
      })
      .catch(() => {
        // Retain baseline demonstration view seamlessly
      });

    return () => {
      isSubscribed = false;
    };
  }, []);

  const actionableCount = gaps.filter((g) => g.classification === "ACTIONABLE").length;
  const evidenceNeededCount = gaps.filter((g) => g.classification === "NEEDS_MORE_EVIDENCE").length;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 shadow-xs relative overflow-hidden",
        className
      )}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-heading text-xl sm:text-2xl text-slate-900 font-bold">
              Workforce Capability Gap Triage
            </h3>
            {isLive ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                Live MoSPI Engine
              </span>
            ) : (
              <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-medium bg-slate-100 text-slate-600 border border-slate-200">
                Cadre Advisory Baseline
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 font-sans">
            Confidence-aware triage categorizing skill deficits into ACTIONABLE interventions vs diagnostic recommendations
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-rose-50 text-rose-800 border border-rose-200 font-semibold">
            <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
            {actionableCount} Actionable
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-amber-50 text-amber-800 border border-amber-200 font-semibold">
            <HelpCircle className="w-3.5 h-3.5 text-amber-600" />
            {evidenceNeededCount} Needs Evidence
          </span>
        </div>
      </div>

      {/* Gap Cards Grid */}
      <div className="space-y-4">
        {gaps.map((gap) => {
          const isActionable = gap.classification === "ACTIONABLE";
          const isSuppressed = gap.affected_learners_count < 5;

          return (
            <div
              key={gap.competency_id}
              className={cn(
                "p-5 rounded-xl border transition flex flex-col justify-between gap-4",
                isActionable
                  ? "bg-rose-50/20 border-rose-200/80 hover:bg-rose-50/30"
                  : "bg-amber-50/20 border-amber-200/80 hover:bg-amber-50/30"
              )}
            >
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-bold border uppercase tracking-wider",
                        isActionable
                          ? "bg-rose-100 text-rose-800 border-rose-200"
                          : "bg-amber-100 text-amber-800 border-amber-200"
                      )}
                    >
                      {isActionable ? (
                        <AlertCircle className="w-3 h-3 text-rose-700" />
                      ) : (
                        <HelpCircle className="w-3 h-3 text-amber-700" />
                      )}
                      {gap.classification.replace(/_/g, " ")}
                    </span>

                    <span className="text-[11px] font-semibold text-slate-500 bg-white px-2 py-0.5 rounded border border-slate-200">
                      Urgency: {gap.urgency}
                    </span>

                    <span className="text-[11px] font-mono text-slate-400">
                      {gap.domain}
                    </span>
                  </div>

                  <h4 className="font-heading text-lg font-bold text-slate-900 pt-1">
                    {gap.competency_name}
                  </h4>
                </div>

                <div className="text-left sm:text-right shrink-0">
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
                    Priority Score
                  </div>
                  <div className="font-heading text-2xl font-bold text-slate-900 tabular-nums">
                    {gap.priority_score.toFixed(3)}
                  </div>
                </div>
              </div>

              {/* Rationale explanation */}
              <div className="bg-white/80 p-3 rounded-lg border border-slate-200/70 text-xs text-slate-700 leading-relaxed">
                <strong className="font-semibold text-slate-900">Decision Support Rationale: </strong>
                {gap.why_prioritized}
              </div>

              {/* Metrics strip */}
              <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-200/60 text-xs">
                <div className="flex items-center gap-4 text-slate-600">
                  <div>
                    Mean Mastery: <strong className="text-slate-900">{Math.round(gap.mean_mastery * 100)}%</strong> (Benchmark: 70%)
                  </div>
                  <div>
                    Confidence: <strong className="text-blue-700">{Math.round(gap.confidence * 100)}%</strong>
                  </div>
                  <div>
                    Affected Cohort:{" "}
                    {isSuppressed ? (
                      <span className="font-mono text-amber-700 font-semibold">Suppressed (N &lt; 5)</span>
                    ) : (
                      <strong className="text-slate-900">{gap.affected_learners_count} Officers</strong>
                    )}
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  {gap.intervention_available ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-1 rounded-lg">
                      <CheckCircle2 className="w-3 h-3" />
                      <span>{gap.intervention_options_count} NSSTA Modules Available</span>
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-1 rounded-lg">
                      <span>Diagnostic Testing Recommended</span>
                    </span>
                  )}
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
