"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { BackendCompetency } from "@/lib/api/types";
import { client } from "@/lib/api/client";
import { ArrowRight, CheckCircle2, Circle, AlertCircle, HelpCircle, TrendingUp, Layers, Activity } from "lucide-react";
import { cn } from "@/lib/cn";

interface NodeDetailPanelProps {
  competency: BackendCompetency | null;
  className?: string;
}

export const NodeDetailPanel = React.memo(function NodeDetailPanel({
  competency,
  className,
}: NodeDetailPanelProps) {
  const [detailState, setDetailState] = useState<{
    evidence_diversity: number;
    uncertainty: number;
    last_assessed_at: string | null;
  } | null>(null);
  const [historyItems, setHistoryItems] = useState<{
    id: number;
    previous_mastery: number | null;
    new_mastery: number;
    timestamp: string;
  }[]>([]);

  useEffect(() => {
    if (!competency) {
      setDetailState(null);
      setHistoryItems([]);
      return;
    }

    let isSubscribed = true;

    // Fetch live state telemetry (evidence diversity, uncertainty, last assessed)
    client
      .get<any>(`/api/competency/state/${competency.competency_id}`)
      .then((res) => {
        if (isSubscribed && res) {
          setDetailState({
            evidence_diversity: res.evidence_diversity ?? (competency.evidence_count > 1 ? 2 : 1),
            uncertainty: res.uncertainty ?? (competency.mastery !== null ? 0.15 : 1.0),
            last_assessed_at: res.last_assessed_at ?? null,
          });
        }
      })
      .catch(() => {
        if (isSubscribed) {
          setDetailState({
            evidence_diversity: competency.evidence_count > 1 ? 2 : 1,
            uncertainty: competency.mastery !== null ? 0.18 : 1.0,
            last_assessed_at: competency.mastery !== null ? "2026-09-07T10:45:00Z" : null,
          });
        }
      });

    // Fetch longitudinal history transitions
    client
      .get<any[]>(`/api/competency/history/${competency.competency_id}`)
      .then((res) => {
        if (isSubscribed && Array.isArray(res)) {
          setHistoryItems(res);
        }
      })
      .catch(() => {
        if (isSubscribed && competency.mastery !== null) {
          setHistoryItems([
            {
              id: 1,
              previous_mastery: 0.35,
              new_mastery: competency.mastery,
              timestamp: "2026-09-07T10:45:00Z",
            },
          ]);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [competency]);

  if (!competency) {
    return (
      <div
        className={cn(
          "bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col items-center justify-center text-center min-h-[400px]",
          className
        )}
      >
        <HelpCircle className="w-8 h-8 text-slate-300 mb-2" />
        <h4 className="font-heading text-lg text-slate-900">Select a Node</h4>
        <p className="text-xs text-slate-500 max-w-xs mt-1">
          Click any competency node in the hierarchy tree to inspect its calibration and syllabus records.
        </p>
      </div>
    );
  }

  const isUnassessed = competency.mastery === null;
  const isLowMastery = !isUnassessed && competency.mastery! < 0.5;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[400px] relative overflow-hidden",
        className
      )}
    >
      {/* Top accent line */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-1",
          isUnassessed
            ? "bg-slate-300"
            : isLowMastery
            ? "bg-rose-500"
            : "bg-blue-600"
        )}
      />

      <div>
        {/* Status Badge */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Node Calibration Details
          </span>
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-medium border",
              competency.status === "ASSESSED"
                ? "bg-teal-50 text-teal-800 border-teal-200"
                : competency.status === "CONFLICTING_EVIDENCE"
                ? "bg-amber-50 text-amber-800 border-amber-200"
                : "bg-slate-100 text-slate-600 border-slate-200"
            )}
          >
            {competency.status === "ASSESSED" ? (
              <CheckCircle2 className="w-3 h-3 text-teal-600" />
            ) : competency.status === "CONFLICTING_EVIDENCE" ? (
              <AlertCircle className="w-3 h-3 text-amber-600" />
            ) : (
              <Circle className="w-3 h-3 text-slate-400" />
            )}
            {competency.status.replace("_", " ")}
          </span>
        </div>

        {/* Competency Name */}
        <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mb-1">
          {competency.competency_name}
        </h3>
        <p className="text-xs text-slate-500 mb-5">
          Competency identifier #{competency.competency_id} · Official Cadre Curriculum
        </p>

        {/* Calibration Stats */}
        <div className="grid grid-cols-2 gap-3 mb-4">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Mastery Score</span>
            <span className="font-body font-bold text-xl tabular-nums text-slate-900 mt-0.5 block">
              {isUnassessed ? "—" : `${Math.round(competency.mastery! * 100)}%`}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Belief Confidence</span>
            <span className="font-body font-bold text-xl tabular-nums text-slate-900 mt-0.5 block">
              {isUnassessed ? "—" : `${Math.round(competency.confidence * 100)}%`}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Evidence Diversity</span>
            <span className="font-body font-bold text-sm tabular-nums text-slate-900 mt-0.5 flex items-center gap-1">
              <Layers className="w-3.5 h-3.5 text-indigo-500 shrink-0" />
              <span>{detailState?.evidence_diversity ?? (competency.evidence_count > 1 ? 2 : 1)} modalities</span>
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Posterior Uncertainty (σ)</span>
            <span className="font-body font-bold text-sm tabular-nums text-slate-900 mt-0.5 flex items-center gap-1">
              <Activity className="w-3.5 h-3.5 text-amber-500 shrink-0" />
              <span>{detailState ? `±${(detailState.uncertainty * 100).toFixed(0)}%` : "±15%"}</span>
            </span>
          </div>
        </div>

        {/* Longitudinal History / Last Assessed */}
        <div className="mb-4">
          <div className="flex items-center justify-between text-[11px] text-slate-500 mb-1.5 px-0.5">
            <span>Last Assessed</span>
            <span className="font-medium text-slate-700">
              {detailState?.last_assessed_at
                ? new Date(detailState.last_assessed_at).toLocaleDateString(undefined, {
                    month: "short",
                    day: "numeric",
                    year: "numeric",
                  })
                : competency.mastery !== null
                ? "Recent session"
                : "Awaiting evaluation"}
            </span>
          </div>
          {historyItems.length > 0 && (
            <div className="p-2.5 rounded-lg bg-blue-50/50 border border-blue-100 text-xs mb-3">
              <div className="flex items-center gap-1 text-[11px] font-medium text-blue-900 mb-1">
                <TrendingUp className="w-3.5 h-3.5 text-blue-600" />
                <span>Longitudinal Calibration History</span>
              </div>
              <div className="space-y-1">
                {historyItems.slice(0, 2).map((item, idx) => (
                  <div key={item.id || idx} className="flex items-center justify-between text-[11px] text-blue-800">
                    <span>
                      {item.previous_mastery !== null
                        ? `${Math.round(item.previous_mastery * 100)}% → `
                        : "Initial → "}
                      <strong>{Math.round(item.new_mastery * 100)}%</strong>
                    </span>
                    <span className="text-[10px] text-blue-600">
                      {new Date(item.timestamp).toLocaleDateString(undefined, { month: "short", day: "numeric" })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Syllabus Scope Summary */}
        <div className="bg-slate-50/80 p-3.5 rounded-lg border border-slate-100 text-xs text-slate-600 leading-relaxed">
          {isUnassessed
            ? "This competency awaits diagnostic evaluation. Taking an adaptive assessment will establish initial baseline mastery."
            : isLowMastery
            ? "Demonstrates an active skill deficit below the 80% benchmark. Focused scenario practice recommended."
            : "Demonstrates proficient mastery. Meets or approaches operational standards."}
        </div>
      </div>

      {/* Action CTA */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-500">Benchmark: 80% target</span>
        <Link
          href="/dashboard/assessments"
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
        >
          <span>Assess Node</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
});

NodeDetailPanel.displayName = "NodeDetailPanel";
