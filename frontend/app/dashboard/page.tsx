"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { motion } from "framer-motion";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import {
  getCompetencyState,
  getCompetencyStateSync,
  deriveKPISummary,
  deriveRadarData,
  deriveActiveGap,
} from "@/lib/api/competency";
import { DashboardResponse, BackendCompetency } from "@/lib/api/types";
import { MetricCard } from "@/components/ui/dashboard/MetricCard";
import { CompetencyRadar } from "@/components/ui/dashboard/CompetencyRadar";
import { ActiveGapCard } from "@/components/ui/dashboard/ActiveGapCard";
import { NextBestActionCard } from "@/components/ui/dashboard/NextBestActionCard";
import { DashboardSkeleton } from "@/components/ui/dashboard/states/CardSkeleton";
import { EmptyState } from "@/components/ui/dashboard/states/EmptyState";
import { ErrorState } from "@/components/ui/dashboard/states/ErrorState";
import {
  HelpCircle,
  CheckCircle2,
  ChevronRight,
  ClipboardCheck,
  X,
} from "lucide-react";
import { cn } from "@/lib/cn";

export default function DashboardPage() {
  const { persona, setUserInfo } = useDashboard();
  const [data, setData] = useState<DashboardResponse>(() =>
    getCompetencyStateSync(persona)
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeDiagnosticModal, setActiveDiagnosticModal] = useState(false);
  const [selectedCompetency, setSelectedCompetency] = useState<BackendCompetency | null>(null);

  const handleOpenDiagnosticModal = useCallback(() => {
    setActiveDiagnosticModal(true);
  }, []);

  const handleCloseDiagnosticModal = useCallback(() => {
    setActiveDiagnosticModal(false);
  }, []);

  const handleSelectCompetency = useCallback((c: BackendCompetency) => {
    setSelectedCompetency(c);
  }, []);

  const handleCloseCompetencyModal = useCallback(() => {
    setSelectedCompetency(null);
  }, []);

  // Synchronize state on persona change
  useEffect(() => {
    let isSubscribed = true;
    const isMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

    if (isMock) {
      const state = getCompetencyStateSync(persona);
      setData(state);
      setUserInfo(state.full_name, state.role_name);
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    getCompetencyState(persona)
      .then((state) => {
        if (isSubscribed) {
          setData(state);
          setUserInfo(state.full_name, state.role_name);
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isSubscribed) {
          setError(err.message || "Failed to load dashboard data.");
          setIsLoading(false);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [persona, setUserInfo]);

  // Derived state (§1.1 Ground Truth)
  const kpiSummary = useMemo(() => deriveKPISummary(data), [data]);
  const radarData = useMemo(() => deriveRadarData(data.competencies), [data.competencies]);
  const activeGap = useMemo(() => deriveActiveGap(data.competencies), [data.competencies]);
  const isAllUnassessed = kpiSummary.mastery_avg === null;

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Could not load dashboard"
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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: "spring", stiffness: 400, damping: 30 },
    },
  };

  return (
    <motion.div 
      className="space-y-8 pb-12 w-full"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Demo Mode Notification Bar */}
      <motion.div variants={itemVariants} className="bg-white border border-slate-200 rounded-xl p-4 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold text-slate-900">
              Demo Mode — {persona === "jso" ? "Sample Learner" : "New Learner"}
            </span>
          </div>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            {isAllUnassessed
              ? "New officer — no assessments taken yet."
              : "Officer with active competency data and diagnosed needs."}
          </p>
        </div>

        <button
          type="button"
          onClick={handleOpenDiagnosticModal}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200 hover:bg-blue-100 transition whitespace-nowrap"
        >
          <ClipboardCheck className="w-3.5 h-3.5" />
          <span>Start Assessment</span>
        </button>
      </motion.div>

      {/* ROW 1: 4 KPI STAT CARDS */}
      <motion.section variants={itemVariants} aria-label="Key Performance Indicators">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Mastery */}
          <MetricCard
            label="Mastery"
            value={kpiSummary.mastery_avg}
            type="mastery"
            sublabel={
              kpiSummary.mastery_avg !== null
                ? "Average across competencies"
                : "Awaiting baseline"
            }
          />

          {/* Confidence */}
          <MetricCard
            label="Confidence"
            value={kpiSummary.confidence_avg > 0 ? kpiSummary.confidence_avg : null}
            displayValue={
              kpiSummary.confidence_avg > 0
                ? `${(kpiSummary.confidence_avg * 100).toFixed(0)}%`
                : undefined
            }
            type="confidence"
            sublabel="Estimation certainty"
          />

          {/* Coverage */}
          <MetricCard
            label="Coverage"
            value={kpiSummary.coverage_avg > 0 ? kpiSummary.coverage_avg : null}
            displayValue={
              kpiSummary.coverage_avg > 0
                ? `${(kpiSummary.coverage_avg * 100).toFixed(0)}%`
                : undefined
            }
            type="coverage"
            sublabel="Subskills tested"
          />

          {/* Assessed Count */}
          <MetricCard
            label="Competencies"
            value={`${kpiSummary.assessed_count} of ${kpiSummary.total_count}`}
            displayValue={`${kpiSummary.assessed_count} of ${kpiSummary.total_count}`}
            sublabel="Assessed to date"
          />
        </div>
      </motion.section>

      {/* If entirely unassessed, render the dedicated EmptyState CTA */}
      {isAllUnassessed ? (
        <motion.div variants={itemVariants}>
          <EmptyState onStartDiagnostic={handleOpenDiagnosticModal} />
        </motion.div>
      ) : null}

      {/* ROW 2: COMPETENCY RADAR (COL 7) + ACTIVE GAP (COL 5) */}
      <motion.section variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <CompetencyRadar
            data={radarData}
            isAllUnassessed={isAllUnassessed}
            className="h-full"
          />
        </div>

        <div className="lg:col-span-5 flex flex-col">
          <ActiveGapCard
            gap={activeGap}
            onTakeAction={handleOpenDiagnosticModal}
            className="h-full"
          />
        </div>
      </motion.section>

      {/* ROW 3: RECOMMENDED ACTION (only if next_best_action exists) */}
      {data.next_best_action && (
        <motion.section variants={itemVariants} aria-labelledby="recommended-action-heading">
          <h2 id="recommended-action-heading" className="sr-only">
            Recommended Action
          </h2>
          <NextBestActionCard
            nba={data.next_best_action}
            onStartAction={handleOpenDiagnosticModal}
          />
        </motion.section>
      )}

      {/* ROW 4: COMPETENCY BREAKDOWN TABLE */}
      <motion.section variants={itemVariants} className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
          <div>
            <h3 className="font-heading text-xl sm:text-2xl tracking-normal text-slate-900">
              Competency Breakdown
            </h3>
            <p className="text-xs text-slate-500 font-sans">
              Measured competency performance and evidence records
            </p>
          </div>
          <span className="text-xs text-slate-400">
            {data.competencies.length} competencies
          </span>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="border-b border-slate-200 text-slate-500 text-[11px] uppercase tracking-wider bg-slate-50/60 font-semibold">
                <th className="py-3 px-4">Competency</th>
                <th className="py-3 px-4">Mastery</th>
                <th className="py-3 px-4">Confidence</th>
                <th className="py-3 px-4">Coverage</th>
                <th className="py-3 px-4">Evidence</th>
                <th className="py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.competencies.map((c) => {
                const isUnassessed = c.mastery === null;
                return (
                  <tr
                    key={c.competency_id}
                    onClick={() => handleSelectCompetency(c)}
                    className="hover:bg-slate-50/80 cursor-pointer transition"
                  >
                    <td className="py-3 px-4">
                      <div className="font-semibold text-slate-900 text-xs">
                        {c.competency_name}
                      </div>
                    </td>
                    <td className="py-3 px-4">
                      {isUnassessed ? (
                        <span className="inline-flex items-center gap-1 text-slate-500 text-[11px]">
                          <HelpCircle className="w-3 h-3 text-slate-400" />
                          Unassessed
                        </span>
                      ) : (
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900 text-xs">
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
                        <span className="text-slate-400 text-[11px]">—</span>
                      ) : (
                        <span
                          className={cn(
                            "px-2 py-0.5 rounded text-[11px] border font-medium",
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
                    <td className="py-3 px-4 text-slate-600">
                      {isUnassessed ? "—" : `${(c.coverage * 100).toFixed(0)}%`}
                    </td>
                    <td className="py-3 px-4 text-slate-600">
                      {c.evidence_count} items
                    </td>
                    <td className="py-3 px-4">
                      <span
                        className={cn(
                          "px-2 py-0.5 rounded text-[10px] uppercase tracking-wider border font-medium",
                          c.status === "ASSESSED"
                            ? "bg-teal-50 text-teal-800 border-teal-200"
                            : c.status === "CONFLICTING_EVIDENCE"
                            ? "bg-amber-50 text-amber-800 border-amber-200"
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
      </motion.section>

      {/* START ASSESSMENT MODAL */}
      {activeDiagnosticModal && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full border border-slate-200 shadow-xl p-6 relative">
            <button
              type="button"
              onClick={handleCloseDiagnosticModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2.5 mb-3">
              <div className="w-9 h-9 rounded-lg bg-blue-100 flex items-center justify-center text-blue-600">
                <ClipboardCheck className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-heading text-xl text-slate-900">
                  Start Assessment
                </h4>
                <p className="text-xs text-slate-500">
                  Target: {activeGap?.competency_name || "Sampling Design"}
                </p>
              </div>
            </div>

            <p className="text-xs text-slate-600 font-sans leading-relaxed mb-4">
              Take an adaptive diagnostic assessment to calibrate your competency state. Questions adapt dynamically based on your response history.
            </p>

            <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-200 text-xs mb-5 space-y-1.5">
              <div className="flex justify-between">
                <span className="text-slate-500">Learner:</span>
                <span className="text-slate-900 font-semibold">{data.full_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Role:</span>
                <span className="text-slate-900">{data.role_name}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-500">Target Competency:</span>
                <span className="text-slate-900 font-medium">
                  {activeGap?.competency_name || "Sampling Design"}
                </span>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3">
              <button
                type="button"
                onClick={handleCloseDiagnosticModal}
                className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
              >
                Cancel
              </button>
              <a
                href="/dashboard/assessments"
                className="px-4 py-2 text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition shadow-xs"
              >
                Proceed to Assessments Page
              </a>
            </div>
          </div>
        </div>
      )}

      {/* SELECTED COMPETENCY DETAIL MODAL */}
      {selectedCompetency && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-md w-full border border-slate-200 shadow-xl p-6 relative">
            <button
              type="button"
              onClick={handleCloseCompetencyModal}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <h4 className="font-heading text-xl text-slate-900 mb-1">
              {selectedCompetency.competency_name}
            </h4>
            <p className="text-xs text-slate-500 mb-4">
              Status: {selectedCompetency.status.replace("_", " ")}
            </p>

            <div className="space-y-3 text-xs">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Mastery:</span>
                <span className="font-semibold text-slate-900">
                  {selectedCompetency.mastery !== null
                    ? `${(selectedCompetency.mastery * 100).toFixed(0)}%`
                    : "Unassessed"}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Confidence:</span>
                <span className="font-semibold text-slate-900">
                  {(selectedCompetency.confidence * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Coverage:</span>
                <span className="font-semibold text-slate-900">
                  {(selectedCompetency.coverage * 100).toFixed(0)}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Evidence Records:</span>
                <span className="font-semibold text-slate-900">
                  {selectedCompetency.evidence_count} items
                </span>
              </div>
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <button
                type="button"
                onClick={handleCloseCompetencyModal}
                className="px-4 py-2 text-xs font-medium bg-slate-100 text-slate-700 rounded-lg hover:bg-slate-200 transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </motion.div>
  );
}
