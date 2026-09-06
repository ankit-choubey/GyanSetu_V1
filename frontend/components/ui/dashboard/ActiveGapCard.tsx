"use client";

import React from "react";
import { AlertTriangle, ArrowRight, CheckCircle2, Info } from "lucide-react";
import { ActiveGap } from "@/lib/api/types";
import { cn } from "@/lib/cn";

interface ActiveGapCardProps {
  gap: ActiveGap;
  className?: string;
  onTakeAction?: () => void;
}

export function ActiveGapCard({
  gap,
  className,
  onTakeAction,
}: ActiveGapCardProps) {
  const isHighSeverity = gap.severity === "high";

  return (
    <div
      className={cn(
        "bg-white rounded-xl border p-6 shadow-sm flex flex-col justify-between relative overflow-hidden",
        isHighSeverity ? "border-rose-200" : "border-slate-200",
        className
      )}
    >
      {/* Top accent strip */}
      <div
        className={cn(
          "absolute top-0 left-0 right-0 h-1",
          isHighSeverity ? "bg-rose-500" : "bg-amber-500"
        )}
      />

      <div>
        {/* Header with Severity Badge */}
        <div className="flex items-center justify-between gap-2 mb-3">
          <div className="flex items-center gap-1.5 text-xs font-mono text-slate-500 uppercase tracking-wider">
            <AlertTriangle
              className={cn(
                "w-4 h-4",
                isHighSeverity ? "text-rose-600" : "text-amber-600"
              )}
            />
            <span>Priority Competency Deficit</span>
          </div>
          <span
            className={cn(
              "px-2.5 py-0.5 rounded text-xs font-mono font-semibold uppercase tracking-wide border",
              isHighSeverity
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            )}
          >
            {gap.severity} Severity
          </span>
        </div>

        {/* Defensible Phrasing (§3.2 / Build Guide §1) */}
        <h3 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-tight leading-snug mb-2">
          Highest-Confidence Actionable Gap:
          <span className="block text-rose-600 font-semibold mt-0.5">
            {gap.title}
          </span>
        </h3>

        {/* Competency mapping */}
        <div className="inline-flex items-center gap-1.5 text-xs font-mono text-slate-600 bg-slate-100 px-2.5 py-1 rounded mb-4">
          <span>Target Domain:</span>
          <span className="font-semibold text-slate-800">{gap.competency_name}</span>
        </div>

        {/* Evidence basis description */}
        <div className="space-y-2 text-xs text-slate-600">
          <div className="flex items-start gap-2 bg-slate-50 p-3 rounded-lg border border-slate-100">
            <Info className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-slate-700">Evidence Basis: </span>
              {gap.evidence_basis}
            </div>
          </div>

          <div className="flex items-start gap-2 bg-rose-50/50 p-3 rounded-lg border border-rose-100/60">
            <AlertTriangle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold text-rose-900">Operational Impact: </span>
              {gap.impact}
            </div>
          </div>
        </div>
      </div>

      {/* Call to action */}
      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-[11px] font-mono text-slate-400">
          Identified by GyanSetu Diagnostic Engine
        </span>
        <button
          type="button"
          onClick={onTakeAction}
          className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-medium bg-rose-600 hover:bg-rose-700 text-white transition shadow-sm hover:shadow"
        >
          <span>Targeted Action</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
