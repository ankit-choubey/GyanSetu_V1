"use client";

import React from "react";
import { Users2, Award, ClipboardCheck, FileText } from "lucide-react";
import { cn } from "@/lib/cn";

interface WorkforceStatCardsProps {
  totalLearners: number;
  avgMastery: number;
  assessedCount: number;
  totalEvaluations: number;
  totalEvidence: number;
  className?: string;
}

export function WorkforceStatCards({
  totalLearners,
  avgMastery,
  assessedCount,
  totalEvaluations,
  totalEvidence,
  className,
}: WorkforceStatCardsProps) {
  return (
    <div
      className={cn(
        "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5",
        className
      )}
    >
      {/* Total Learners */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Total Learners
          </span>
          <Users2 className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {totalLearners}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Active cadre officers</p>
        </div>
      </div>

      {/* Average Cadre Mastery */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Average Mastery
          </span>
          <Award className="w-5 h-5 text-teal-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {Math.round(avgMastery * 100)}%
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Across all competencies</p>
        </div>
      </div>

      {/* Assessed vs Total */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Assessments Taken
          </span>
          <ClipboardCheck className="w-5 h-5 text-slate-500" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {assessedCount} of {totalEvaluations}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">
            {Math.round((assessedCount / (totalEvaluations || 1)) * 100)}% coverage rate
          </p>
        </div>
      </div>

      {/* Total Evidence */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Evidence Items
          </span>
          <FileText className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {totalEvidence}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Verified observation records</p>
        </div>
      </div>
    </div>
  );
}
