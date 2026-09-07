"use client";

import React from "react";
import Link from "next/link";
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
        "bg-white rounded-2xl border border-slate-200 border-l-4 border-l-blue-600 p-6 sm:p-7 shadow-sm hover:shadow-md transition-all relative overflow-hidden",
        className
      )}
    >
      {/* Header Row: Badge & Type */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3.5">
        <div className="flex items-center gap-2.5">
          <StatusChip status="info">
            <Target className="w-4 h-4" />
            Recommended Action
          </StatusChip>
          {nba.gap_reason && (
            <span className="text-sm text-slate-600 capitalize font-sans">
              Trigger: {nba.gap_reason.replace("_", " ")}
            </span>
          )}
        </div>

        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
          <BookOpen className="w-3.5 h-3.5 text-slate-500" />
          {intervention.type}
        </span>
      </div>

      {/* Primary Recommended Title */}
      <div className="mb-4">
        <h3 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-wide leading-snug">
          {intervention.title}
        </h3>
      </div>

      {/* Reason & Explanation Grid (Neutral single-tone boxes) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-50/80 p-4 sm:p-5 rounded-xl border border-slate-100">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 text-blue-600" />
            <span>Why this action</span>
          </div>
          <p className="text-sm text-slate-700 font-sans leading-relaxed">
            {intervention.reason}
          </p>
        </div>

        <div className="bg-slate-50/80 p-4 sm:p-5 rounded-xl border border-slate-100">
          <div className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1.5 flex items-center gap-2">
            <ChevronRight className="w-4 h-4 text-slate-400" />
            <span>Target outcome</span>
          </div>
          <p className="text-sm text-slate-700 font-sans leading-relaxed">
            {nba.explanation || "Targeted remediation to address baseline skill gap."}
          </p>
        </div>
      </div>

      {/* Footer / CTA Action */}
      <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
        <span className="text-sm text-slate-600 font-sans">
          Intervention modality: {intervention.type.toLowerCase()}
        </span>

        {onStartAction ? (
          <button
            type="button"
            onClick={onStartAction}
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
          >
            <span>Begin Action</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        ) : (
          <Link
            href="/dashboard/tasks"
            className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm hover:shadow"
          >
            <span>Begin Action</span>
            <ArrowRight className="w-4 h-4" />
          </Link>
        )}
      </div>
    </div>
  );
});
