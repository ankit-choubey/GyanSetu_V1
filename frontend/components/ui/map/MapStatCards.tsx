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
    <div className={cn("grid grid-cols-1 sm:grid-cols-3 gap-4", className)}>
      {/* Total Competencies */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Nodes
          </span>
          <GitFork className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {totalCount}
          </div>
          <p className="text-xs text-slate-500 mt-1">Curriculum syllabus competencies</p>
        </div>
      </div>

      {/* Assessed */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Assessed Nodes
          </span>
          <CheckCircle2 className="w-4 h-4 text-teal-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {assessedCount} of {totalCount}
          </div>
          <p className="text-xs text-slate-500 mt-1">
            {Math.round((assessedCount / (totalCount || 1)) * 100)}% mapped and verified
          </p>
        </div>
      </div>

      {/* Average Coverage */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Average Coverage
          </span>
          <Layers className="w-4 h-4 text-amber-600" />
        </div>
        <div>
          <div className="font-heading text-3xl sm:text-4xl text-slate-900 mt-1">
            {Math.round(avgCoverage * 100)}%
          </div>
          <p className="text-xs text-slate-500 mt-1">Overall tested syllabus breadth</p>
        </div>
      </div>
    </div>
  );
}
