"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import { getCompetencyState, getCompetencyStateSync } from "@/lib/api/competency";
import { CompetencyState, CompetencyMetric } from "@/lib/api/types";
import { MetricCard } from "@/components/ui/dashboard/MetricCard";
import { CompetencyRadar } from "@/components/ui/dashboard/CompetencyRadar";
import { ActiveGapCard } from "@/components/ui/dashboard/ActiveGapCard";
import { NextBestActionCard } from "@/components/ui/dashboard/NextBestActionCard";
import { AgentActivityStrip } from "@/components/ui/dashboard/AgentActivityStrip";
import { DashboardSkeleton } from "@/components/ui/dashboard/states/CardSkeleton";
import { EmptyState } from "@/components/ui/dashboard/states/EmptyState";
import { ErrorState } from "@/components/ui/dashboard/states/ErrorState";
import {
  HelpCircle,
  CheckCircle2,
  AlertTriangle,
  FileSpreadsheet,
  Layers,
  ChevronRight,
  Sparkles,
  RefreshCw,
  X,
} from "lucide-react";
import { cn } from "@/lib/cn";

export default function DashboardPage() {
  const { persona } = useDashboard();
  // Synchronous initialization with sandbox data for instant zero-latency render
  const [data, setData] = useState<CompetencyState>(() => getCompetencyStateSync(persona));
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiagnosticModal, setActiveDiagnosticModal] = useState(false);
  const [selectedCompetency, setSelectedCompetency] = useState<CompetencyMetric | null>(null);

  const handleOpenDiagnosticModal = useCallback(() => {
    setActiveDiagnosticModal(true);
  }, []);

  const handleCloseDiagnosticModal = useCallback(() => {
    setActiveDiagnosticModal(false);
  }, []);

  const handleSelectCompetency = useCallback((c: CompetencyMetric) => {
    setSelectedCompetency(c);
  }, []);

  const handleCloseCompetencyModal = useCallback(() => {
    setSelectedCompetency(null);
  }, []);

  // Synchronize state on persona change
  useEffect(() => {
    let isSubscribed = true;
    const isMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

    // Immediate instant sync in mock mode (no skeleton flash or network wait)
    if (isMock) {
      setData(getCompetencyStateSync(persona));
      setIsLoading(false);
      return;
    }

    // Live backend mode with graceful background update
    setIsLoading(true);
    setError(null);

    getCompetencyState(persona)
      .then((state) => {
        if (isSubscribed) {
          setData(state);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isSubscribed) {
          setError(err.message || "Failed to load competency state.");
          setIsLoading(false);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [persona]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Could not connect to Competency Intelligence Engine"
        message={error || "Unexpected data error"}
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

  const isAllUnassessed = data.kpi_summary.mastery_avg === null;

  return (
    <div className="space-y-8 pb-12">
      {/* Persona Notice Banner (Hackathon Demo Clarity) */}
      <div className="bg-white border border-slate-200/80 rounded-xl p-4 shadow-sm flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-blue-50 border border-blue-200 flex items-center justify-center text-blue-600 shrink-0">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-mono text-xs font-semibold text-slate-900">
                ACTIVE DEMO PERSONA: {data._meta.persona}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-blue-100 text-blue-800">
                MoSPI SSS Cadre
              </span>
            </div>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              {isAllUnassessed
                ? "First-Class Baseline State: Zero evidence is safely rendered as Unassessed, never failing."
                : "Active Closed-Loop State: Demonstrating gap diagnosis → 12-facet explainable intervention."}
            </p>
          </div>
        </div>

        <button
          type="button"
          onClick={handleOpenDiagnosticModal}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition whitespace-nowrap"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span>Simulate Diagnostic Test</span>
        </button>
      </div>

      {/* ROW 1: ABOVE-THE-FOLD KPI STRIP (5 METRICS, §3.1) */}
      <section aria-labelledby="kpi-strip-heading">
        <h2 id="kpi-strip-heading" className="sr-only">
          Competency Key Performance Indicators
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {/* 1. Mastery (Top-Left per F-Pattern) */}
          <MetricCard
            label="1. Cadre Mastery"
            value={data.kpi_summary.mastery_avg}
            confidence={data.kpi_summary.confidence_level}
            confidenceScore={data.kpi_summary.confidence_score}
            type="mastery"
            sublabel={
              data.kpi_summary.mastery_avg !== null
                ? "Weighted cross-domain index"
                : "Awaiting baseline diagnostic"
            }
          />

          {/* 2. Estimation Confidence */}
          <MetricCard
            label="2. Belief Confidence"
            value={
              data.kpi_summary.confidence_score > 0
                ? `${(data.kpi_summary.confidence_score * 100).toFixed(0)}%`
                : null
            }
            displayValue={
              data.kpi_summary.confidence_score > 0
                ? `${(data.kpi_summary.confidence_score * 100).toFixed(0)}%`
                : undefined
            }
            confidence={data.kpi_summary.confidence_level}
            type="confidence"
            sublabel="Uncertainty calibration"
          />

          {/* 3. Tested Subskill Coverage */}
          <MetricCard
            label="3. Subskill Coverage"
            value={
              data.kpi_summary.coverage_pct > 0
                ? data.kpi_summary.coverage_pct
                : null
            }
            type="coverage"
            sublabel="Tested syllabus scope"
          />

          {/* 4. Evidence Recency */}
          <MetricCard
            label="4. Evidence Recency"
            value={data.kpi_summary.recency_label}
            type="recency"
            sublabel="Freshness of latest proof"
          />

          {/* 5. Evidence Diversity */}
          <MetricCard
            label="5. Evidence Diversity"
            value={`${data.kpi_summary.diversity_count} of ${data.kpi_summary.diversity_total}`}
            type="diversity"
            sublabel="Fused data modalities"
          />
        </div>
      </section>

      {/* If entirely unassessed, render the dedicated EmptyState CTA */}
      {isAllUnassessed ? (
        <EmptyState
          onStartDiagnostic={handleOpenDiagnosticModal}
        />
      ) : null}

      {/* ROW 2: 5-AXIS RADAR (COL 7) + ACTIVE GAP CARD (COL 5) (§3.1) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <CompetencyRadar
            data={data.radar_data}
            isAllUnassessed={isAllUnassessed}
            className="h-full"
          />
        </div>

        <div className="lg:col-span-5 flex flex-col">
          <ActiveGapCard
            gap={data.active_gap}
            onTakeAction={handleOpenDiagnosticModal}
            className="h-full"
          />
        </div>
      </section>

      {/* ROW 3: NEXT BEST ACTION CARD (12 EXPLAINABILITY FIELDS) (§3.1) */}
      <section aria-labelledby="nba-heading">
        <h2 id="nba-heading" className="sr-only">
          Recommended Next Best Action
        </h2>
        <NextBestActionCard nba={data.next_best_action} />
      </section>

      {/* ROW 4: AGENT ACTIVITY AUDIT STRIP (§3.1) */}
      <section aria-labelledby="agent-activity-heading">
        <h2 id="agent-activity-heading" className="sr-only">
          Multi-Agent System Activity
        </h2>
        <AgentActivityStrip activities={data.agent_activity} />
      </section>

      {/* SECTION 5: DETAILED COMPETENCY BREAKDOWN TABLE */}
      <section className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="font-heading text-2xl tracking-wide text-slate-900">
              Official Statistics Competency Matrix
            </h3>
            <p className="text-xs text-slate-500 font-sans">
              SSS JSO curriculum competencies mapped to MoSPI Field Operations & National Accounts
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            5 Registered Competencies
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 font-mono text-[11px] uppercase bg-slate-50/50">
                <th className="py-3 px-4">Code / Competency</th>
                <th className="py-3 px-4">Domain</th>
                <th className="py-3 px-4">Mastery</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Coverage</th>
                <th className="py-3 px-4">Actionable Gap</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.competencies.map((c) => {
                const isUnassessed = c.mastery === null;
                return (
                  <tr
                    key={c.id}
                    onClick={() => handleSelectCompetency(c)}
                    className="hover:bg-slate-50/70 cursor-pointer transition"
                  >
                    <td className="py-3 px-4">
                      <div className="font-mono text-[11px] text-blue-600 font-semibold">
                        {c.id}
                      </div>
                      <div className="font-medium text-slate-900 text-xs">
                        {c.name}
                      </div>
                    </td>
                    <td className="py-3 px-4 text-slate-600 font-mono text-[11px]">
                      {c.domain}
                    </td>
                    <td className="py-3 px-4">
                      {isUnassessed ? (
                        <span className="inline-flex items-center gap-1 text-slate-500 font-mono text-[11px]">
                          <HelpCircle className="w-3 h-3 text-slate-400" />
                          Unassessed
                        </span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-semibold text-slate-900 text-xs">
                            {(c.mastery! * 100).toFixed(0)}%
                          </span>
                          <div className="w-16 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                            <div
                              className={cn(
                                "h-full rounded-full",
                                c.mastery! >= 0.7
                                  ? "bg-teal-500"
                                  : c.mastery! >= 0.4
                                  ? "bg-amber-500"
                                  : "bg-rose-500"
                              )}
                              style={{ width: `${c.mastery! * 100}%` }}
                            />
                          </div>
                        </div>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      {isUnassessed ? (
                        <span className="text-slate-400 font-mono text-[11px]">—</span>
                      ) : (
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[11px] font-mono border font-medium",
                            c.confidence >= 0.7
                              ? "bg-teal-50 text-teal-700 border-teal-200"
                              : c.confidence >= 0.4
                              ? "bg-blue-50 text-blue-700 border-blue-200"
                              : "bg-amber-50 text-amber-700 border-amber-200"
                          )}
                        >
                          {(c.confidence * 100).toFixed(0)}%
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4 font-mono text-slate-600">
                      {isUnassessed ? "—" : `${(c.coverage * 100).toFixed(0)}%`}
                    </td>
                    <td className="py-3 px-4">
                      {c.gap ? (
                        <span className="text-rose-700 bg-rose-50 border border-rose-100 px-2 py-0.5 rounded font-mono text-[11px] inline-block max-w-[220px] truncate">
                          {c.gap}
                        </span>
                      ) : isUnassessed ? (
                        <span className="text-slate-400 font-mono text-[11px]">
                          Baseline required
                        </span>
                      ) : (
                        <span className="text-teal-700 font-mono text-[11px] flex items-center gap-1">
                          <CheckCircle2 className="w-3 h-3 text-teal-600" />
                          Meets Threshold
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-[10px] font-mono uppercase tracking-wider border",
                          c.status === "mastered"
                            ? "bg-teal-50 text-teal-800 border-teal-200"
                            : c.status === "proficient"
                            ? "bg-blue-50 text-blue-800 border-blue-200"
                            : c.status === "needs_improvement"
                            ? "bg-rose-50 text-rose-800 border-rose-200"
                            : "bg-slate-100 text-slate-600 border-slate-200"
                        )}
                      >
                        {c.status.replace("_", " ")}
                      </span>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      {/* DIAGNOSTIC SIMULATION MODAL */}
      {activeDiagnosticModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={handleCloseDiagnosticModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-heading text-2xl text-slate-900">
                  Adaptive Diagnostic Simulator
                </h4>
                <p className="text-[11px] font-mono text-slate-500">
                  Target: {data.active_gap.title}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 font-sans leading-relaxed mb-4">
              In Phase 2, this modal launches the live CAT (Computerized Adaptive Testing) session, assessing the officer on finite population correction, stratum weights, and Jackknife variance estimation.
            </p>

            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs mb-5 space-y-1.5 font-mono">
              <div className="flex justify-between">
                <span className="text-slate-500">Officer:</span>
                <span className="text-slate-900 font-semibold">{data.officer.name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Assessment Scope:</span>
                <span className="text-slate-900">12 Adaptive Items (MoSPI NSSTA Item Bank)</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Current Mastery:</span>
                <span className="text-slate-900">
                  {data.kpi_summary.mastery_avg !== null
                    ? `${(data.kpi_summary.mastery_avg * 100).toFixed(0)}% (Confidence: Low)`
                    : "Unassessed"}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleCloseDiagnosticModal}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Close Simulation
              </button>
              <button
                type="button"
                onClick={() => {
                  alert("Phase 2 Diagnostic will update belief state and re-morph the radar chart!");
                  handleCloseDiagnosticModal();
                }}
                className="px-4 py-2 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-sm"
              >
                Simulate Completion & Morph Radar
              </button>
            </div>
          </div>
        </div>
      )}

      {/* SELECTED COMPETENCY DETAIL MODAL */}
      {selectedCompetency && (
        <div className="fixed inset-0 z-50 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full border border-slate-200 shadow-2xl p-6 relative">
            <button
              type="button"
              onClick={handleCloseCompetencyModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <span className="text-[10px] font-mono uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
              {selectedCompetency.id} · {selectedCompetency.domain}
            </span>

            <h4 className="font-heading text-2xl text-slate-900 mt-2 mb-1">
              {selectedCompetency.name}
            </h4>

            <div className="mt-4 space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-mono">Mastery Score:</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {selectedCompetency.mastery !== null
                    ? `${(selectedCompetency.mastery * 100).toFixed(0)}%`
                    : "Unassessed (No Evidence)"}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-mono">Confidence:</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {(selectedCompetency.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-mono">Coverage:</span>
                <span className="font-semibold text-slate-900 font-mono">
                  {(selectedCompetency.coverage * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500 font-mono">Last Assessed:</span>
                <span className="text-slate-700 font-mono">
                  {selectedCompetency.last_assessed
                    ? new Date(selectedCompetency.last_assessed).toLocaleDateString()
                    : "Never"}
                </span>
              </div>
              <div className="py-1.5">
                <span className="text-slate-500 font-mono block mb-1">
                  Identified Primary Gap:
                </span>
                <span className="text-rose-800 bg-rose-50 border border-rose-200 px-2.5 py-1 rounded block font-mono">
                  {selectedCompetency.gap || "None identified / Unassessed"}
                </span>
              </div>
            </div>

            <div className="mt-6 flex justify-end">
              <button
                type="button"
                onClick={handleCloseCompetencyModal}
                className="px-4 py-2 text-xs font-medium bg-slate-900 text-white rounded-lg hover:bg-slate-800 transition"
              >
                Dismiss
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
