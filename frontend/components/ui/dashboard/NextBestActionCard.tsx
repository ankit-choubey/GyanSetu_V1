"use client";

import React from "react";
import { cn } from "@/lib/cn";
import { ArrowRight, BookOpen, CheckCircle2, ChevronRight, Target } from "lucide-react";
import { NextBestActionResponse } from "@/lib/api/types";
import { StatusChip } from "@/components/ui/dashboard/primitives";

export interface NextBestActionCardProps {
  nba: NextBestActionResponse;
  className?: string;
  onStartAction?: () => void;
}

export const NextBestActionCard = React.memo(function NextBestActionCard({
  nba,
  className,
  onStartAction,
}: NextBestActionCardProps) {
  const intervention = nba.selected_intervention;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 border-l-4 border-l-blue-600 p-6 shadow-sm hover:shadow-md transition-all relative overflow-hidden",
        className
      )}
    >
      {/* Header Row: Badge & Type */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <StatusChip status="info">
            <Target className="w-3.5 h-3.5" />
            Recommended Action
          </StatusChip>
          {nba.gap_reason && (
            <span className="text-xs text-slate-500 capitalize font-sans">
              Trigger: {nba.gap_reason.replace("_", " ")}
            </span>
          )}
        </div>

        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600 border border-slate-200">
          <BookOpen className="w-3 h-3 text-slate-400" />
          {intervention.type}
        </span>
      </div>

      {/* Primary Recommended Title */}
      <div className="mb-4">
        <h3 className="font-heading text-xl sm:text-2xl text-slate-900 tracking-normal leading-snug">
          {intervention.title}
        </h3>
      </div>

      {/* Reason & Explanation Grid (Neutral single-tone boxes) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5 text-xs">
        <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-100">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            <span>Why this action</span>
          </div>
          <p className="text-slate-600 font-sans leading-relaxed">
            {intervention.reason}
          </p>
        </div>

        <div className="bg-slate-50/70 p-4 rounded-lg border border-slate-100">
          <div className="text-[11px] font-medium text-slate-400 uppercase tracking-wider mb-1 flex items-center gap-1.5">
            <ChevronRight className="w-3.5 h-3.5 text-slate-400" />
            <span>Target outcome</span>
          </div>
          <p className="text-slate-600 font-sans leading-relaxed">
            {nba.explanation || "Targeted remediation to address baseline skill gap."}
          </p>
        </div>
      </div>

      {/* Footer / CTA Action */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-xs text-slate-500 font-sans">
          Intervention modality: {intervention.type.toLowerCase()}
        </span>

        {onStartAction ? (
          <button
            type="button"
            onClick={onStartAction}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
          >
            <span>Begin Action</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <a
            href="/dashboard/tasks"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
          >
            <span>Begin Action</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </a>
        )}
      </div>
    </div>
  );
});
