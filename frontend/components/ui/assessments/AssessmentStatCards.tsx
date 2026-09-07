"use client";

import React from "react";
import { ClipboardCheck, CheckCircle2, Award } from "lucide-react";
import { cn } from "@/lib/cn";

interface AssessmentStatCardsProps {
  totalCompetencies: number;
  assessedCount: number;
  avgMastery: number | null;
  className?: string;
}

export function AssessmentStatCards({
  totalCompetencies,
  assessedCount,
  avgMastery,
  className,
}: AssessmentStatCardsProps) {
  return (
    <div className={cn("grid grid-cols-1 sm:grid-cols-3 gap-4", className)}>
      {/* Total Competencies Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Competencies
          </span>
          <ClipboardCheck className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {totalCompetencies}
          </div>
          <p className="text-xs text-slate-500 mt-1">For your role syllabus</p>
        </div>
      </div>

      {/* Assessed Count Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Assessed
          </span>
          <CheckCircle2 className="w-4 h-4 text-teal-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {assessedCount} of {totalCompetencies}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {totalCompetencies - assessedCount > 0
              ? `${totalCompetencies - assessedCount} remaining unassessed`
              : "All competencies evaluated"}
          </p>
        </div>
      </div>

      {/* Average Mastery Card */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Average Mastery
          </span>
          <Award className="w-4 h-4 text-indigo-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {avgMastery !== null ? `${Math.round(avgMastery * 100)}%` : "—"}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {avgMastery !== null
              ? "Across evaluated competencies"
              : "Awaiting first assessment"}
          </p>
        </div>
      </div>
    </div>
  );
}
