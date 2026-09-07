"use client";

import React from "react";
import Link from "next/link";
import { cn } from "@/lib/cn";
import { ArrowRight, AlertCircle } from "lucide-react";
import { BackendCompetency, ActiveGapDerived } from "@/lib/api/types";
import { StatCell, StatusChip } from "@/components/ui/dashboard/primitives";

export interface ActiveGapCardProps {
  gap?: ActiveGapDerived | BackendCompetency | null;
  competency?: BackendCompetency | ActiveGapDerived | null;
  competencyName?: string;
  mastery?: number | null;
  confidence?: number;
  coverage?: number;
  evidenceCount?: number;
  className?: string;
  onAction?: () => void;
  onTakeAction?: () => void;
  onStartAssessment?: () => void;
}

export const ActiveGapCard = React.memo(function ActiveGapCard({
  gap,
  competency,
  competencyName,
  mastery,
  confidence,
  coverage,
  evidenceCount = 0,
  className,
  onAction,
  onTakeAction,
  onStartAssessment,
}: ActiveGapCardProps) {
  const comp = competency || gap;
  const name = comp?.competency_name || competencyName || "Sampling Design";
  const m = comp !== undefined ? comp?.mastery ?? null : mastery ?? null;
  const conf = comp?.confidence ?? confidence ?? 0;
  const cov = comp?.coverage ?? coverage ?? 0;
  const evCount = comp?.evidence_count ?? evidenceCount;
  const handleAction = onAction || onTakeAction || onStartAssessment;

  if (!comp && mastery === undefined) {
    return (
      <div
        className={cn(
          "bg-white rounded-xl border border-slate-200 p-6 flex flex-col justify-between min-h-[360px] shadow-sm",
          className
        )}
      >
        <div>
          <div className="flex items-center justify-between mb-3">
            <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
              Active Focus Area
            </span>
            <StatusChip status="high">Target met</StatusChip>
          </div>
          <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mb-2">
            No Critical Gaps Identified
          </h3>
          <p className="text-xs text-slate-500 leading-relaxed">
            All assessed competencies meet or exceed role requirements. Continue regular assessments to maintain currency.
          </p>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs text-slate-500">All competencies calibrated</span>
          <Link
            href="/dashboard/assessments"
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-slate-100 hover:bg-slate-200 text-slate-700 transition"
          >
            <span>Review Assessments</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        </div>
      </div>
    );
  }

  const isUnassessed = m === null || m === undefined;
  const isLowMastery = !isUnassessed && m < 0.7;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 flex flex-col justify-between min-h-[360px] shadow-sm relative overflow-hidden",
        className
      )}
    >
      <div>
        <div className="flex items-center justify-between mb-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-500 font-sans">
            Priority Attention
          </span>
          {isLowMastery && (
            <StatusChip status="low">
              <AlertCircle className="w-3.5 h-3.5" />
              Priority gap
            </StatusChip>
          )}
          {isUnassessed && (
            <StatusChip status="unassessed">
              Unassessed
            </StatusChip>
          )}
        </div>

        <h3 className="font-heading text-2xl sm:text-3xl text-slate-900 mb-2 tracking-wide">
          {name}
        </h3>
        <p className="text-sm text-slate-600 mb-5 leading-relaxed font-sans">
          {isUnassessed
            ? "No baseline evidence has been recorded for this competency."
            : isLowMastery
            ? "Current score is below the 80% role benchmark."
            : "Competency is progressing towards the target benchmark."}
        </p>

        {/* Flattened Stats Grid (No nested bordered sub-boxes) */}
        <div className="grid grid-cols-2 gap-y-5 gap-x-6 py-5 my-2 border-y border-slate-100">
          <StatCell
            label="Current Mastery"
            value={isUnassessed ? "—" : `${Math.round(m * 100)}%`}
            status={isUnassessed ? "unassessed" : isLowMastery ? "low" : "high"}
          />
          <StatCell
            label="Confidence"
            value={isUnassessed ? "—" : `${Math.round(conf * 100)}%`}
          />
          <StatCell
            label="Coverage"
            value={isUnassessed ? "—" : `${Math.round(cov * 100)}%`}
          />
          <StatCell
            label="Evidence Records"
            value={evCount}
          />
        </div>
      </div>

      {/* Action footer */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-sm text-slate-600 font-sans">
          {isUnassessed ? "Take first assessment" : "Role target: 80% benchmark"}
        </span>
        {handleAction ? (
          <button
            type="button"
            onClick={handleAction}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <Link
            href="/dashboard/assessments"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
          >
            <span>Start Assessment</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>
    </div>
  );
});
