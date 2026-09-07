"use client";

import React from "react";
import { GitFork, CheckCircle2, Layers } from "lucide-react";
import { cn } from "@/lib/cn";

interface MapStatCardsProps {
  totalCount: number;
  assessedCount: number;
  avgCoverage: number;
  className?: string;
}

export function MapStatCards({
  totalCount,
  assessedCount,
  avgCoverage,
  className,
}: MapStatCardsProps) {
  return (
    <div className={cn("grid grid-cols-1 sm:grid-cols-3 gap-5", className)}>
      {/* Total Competencies */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Total Nodes
          </span>
          <GitFork className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {totalCount}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Curriculum syllabus competencies</p>
        </div>
      </div>

      {/* Assessed */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Assessed Nodes
          </span>
          <CheckCircle2 className="w-5 h-5 text-teal-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {assessedCount} of {totalCount}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">
            {Math.round((assessedCount / (totalCount || 1)) * 100)}% mapped and verified
          </p>
        </div>
      </div>

      {/* Average Coverage */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Average Coverage
          </span>
          <Layers className="w-5 h-5 text-amber-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {Math.round(avgCoverage * 100)}%
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Overall tested syllabus breadth</p>
        </div>
      </div>
    </div>
  );
}
