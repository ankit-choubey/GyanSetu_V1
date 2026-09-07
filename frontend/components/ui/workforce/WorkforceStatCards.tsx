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
        "grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4",
        className
      )}
    >
      {/* Total Learners */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Learners
          </span>
          <Users2 className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {totalLearners}
          </div>
          <p className="text-xs text-slate-500 mt-1">Active cadre officers</p>
        </div>
      </div>

      {/* Average Cadre Mastery */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Average Mastery
          </span>
          <Award className="w-4 h-4 text-teal-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {Math.round(avgMastery * 100)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">Across all competencies</p>
        </div>
      </div>

      {/* Assessed vs Total */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Assessments Taken
          </span>
          <ClipboardCheck className="w-4 h-4 text-indigo-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {assessedCount} of {totalEvaluations}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {Math.round((assessedCount / (totalEvaluations || 1)) * 100)}% coverage rate
          </p>
        </div>
      </div>

      {/* Total Evidence */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Evidence Items
          </span>
          <FileText className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {totalEvidence}
          </div>
          <p className="text-xs text-slate-500 mt-1">Verified observation records</p>
        </div>
      </div>
    </div>
  );
}
