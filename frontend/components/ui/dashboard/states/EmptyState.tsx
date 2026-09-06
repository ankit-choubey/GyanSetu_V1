"use client";

import React from "react";
import { Stethoscope, ArrowRight, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/cn";

interface EmptyStateProps {
  title?: string;
  description?: string;
  onStartDiagnostic?: () => void;
  className?: string;
}

export function EmptyState({
  title = "No Competency Evidence Recorded Yet",
  description = "This officer has been onboarded to the SSS cadre but has not yet completed a diagnostic assessment. The competency engine requires baseline evidence before generating targeted next-best-actions.",
  onStartDiagnostic,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-10 text-center flex flex-col items-center justify-center max-w-2xl mx-auto my-6 shadow-sm",
        className
      )}
    >
      <div className="w-14 h-14 rounded-2xl bg-blue-100 flex items-center justify-center text-blue-600 mb-4 shadow-sm">
        <Stethoscope className="w-7 h-7" />
      </div>

      <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono bg-blue-50 text-blue-700 border border-blue-200 mb-3">
        <ShieldCheck className="w-3.5 h-3.5" />
        <span>First-Class State: Baseline Calibration Required</span>
      </div>

      <h3 className="font-heading text-2xl sm:text-3xl text-slate-900 mb-2">
        {title}
      </h3>

      <p className="text-xs sm:text-sm text-slate-600 font-sans max-w-lg mb-6 leading-relaxed">
        {description}
      </p>

      <button
        type="button"
        onClick={onStartDiagnostic}
        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs sm:text-sm font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
      >
        <span>Initialize Adaptive Diagnostic (20 min)</span>
        <ArrowRight className="w-4 h-4" />
      </button>

      <p className="text-[11px] font-mono text-slate-400 mt-4">
        Hard Rule: Unassessed competencies are displayed as &quot;Unassessed&quot; (never 0% or failing).
      </p>
    </div>
  );
}
