"use client";

import React from "react";
import { AlertCircle, ArrowRight } from "lucide-react";
import { ActiveGapDerived } from "@/lib/api/types";
import { cn } from "@/lib/cn";

export interface ActiveGapCardProps {
  gap?: ActiveGapDerived | null;
  competencyName?: string;
  mastery?: number | null;
  confidence?: number;
  coverage?: number;
  evidenceCount?: number;
  className?: string;
  onTakeAction?: () => void;
  onStartAssessment?: () => void;
}

export const ActiveGapCard = React.memo(function ActiveGapCard({
  gap,
  competencyName,
  mastery,
  confidence,
  coverage,
  evidenceCount = 0,
  className,
  onTakeAction,
  onStartAssessment,
}: ActiveGapCardProps) {
  const name = gap ? gap.competency_name : competencyName || "Sampling Design";
  const m = gap !== undefined ? gap?.mastery ?? null : mastery ?? null;
  const conf = gap ? gap.confidence : confidence ?? 0;
  const cov = gap ? gap.coverage : coverage ?? 0;
  const evCount = gap ? gap.evidence_count : evidenceCount;
  const onAction = onTakeAction || onStartAssessment;

  const isUnassessed = m === null;
  const isLowMastery = !isUnassessed && m < 0.5;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border p-6 shadow-xs flex flex-col justify-between relative overflow-hidden min-h-[360px]",
        isLowMastery ? "border-rose-200" : "border-slate-200",
        className
      )}
    >
      {/* Top accent strip */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-1",
          isLowMastery ? "bg-rose-500" : "bg-blue-500"
        )}
      />

      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Needs Attention
          </span>
          {isLowMastery && (
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-rose-50 text-rose-700 border border-rose-200 font-medium">
              <AlertCircle className="w-3 h-3" />
              Priority Gap
            </span>
          )}
          {isUnassessed && (
            <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-600 border border-slate-200 font-medium">
              Unassessed
            </span>
          )}
        </div>

        <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mb-1">
          {name}
        </h3>
        <p className="text-xs text-slate-500 mb-5">
          {isUnassessed
            ? "No baseline evidence has been recorded for this competency."
            : isLowMastery
            ? "Current score is below the 80% role benchmark."
            : "Competency is progressing towards the target benchmark."}
        </p>

        {/* Stats grid */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Current Mastery</span>
            <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
              {isUnassessed ? "—" : `${Math.round(m * 100)}%`}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Confidence</span>
            <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
              {isUnassessed ? "—" : `${Math.round(conf * 100)}%`}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Coverage</span>
            <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
              {isUnassessed ? "—" : `${Math.round(cov * 100)}%`}
            </span>
          </div>

          <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
            <span className="text-[11px] text-slate-500 block">Evidence Records</span>
            <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
              {evCount}
            </span>
          </div>
        </div>
      </div>

      {/* Action footer */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-500">
          {isUnassessed ? "Take first assessment" : "Target: 80% benchmark"}
        </span>
        {onAction ? (
          <button
            type="button"
            onClick={onAction}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <a
            href="/dashboard/assessments"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
});

ActiveGapCard.displayName = "ActiveGapCard";
