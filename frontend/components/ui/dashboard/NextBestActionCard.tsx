"use client";

import React from "react";
import Link from "next/link";
import { ArrowRight, BookOpen, CheckCircle2, Target } from "lucide-react";
import { NextBestActionResponse } from "@/lib/api/types";
import { cn } from "@/lib/cn";

interface NextBestActionCardProps {
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
        "bg-white rounded-xl border border-blue-200/80 p-6 shadow-sm hover:shadow-md transition-all relative overflow-hidden",
        className
      )}
    >
      {/* Top Accent Stripe */}
      <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-600 via-indigo-600 to-teal-400" />

      {/* Header Row: Badge & Type */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-blue-50 text-blue-800 border border-blue-200">
            <Target className="w-3.5 h-3.5 text-blue-600" />
            Recommended Action
          </span>
          {nba.gap_reason && (
            <span className="text-xs text-slate-500 capitalize">
              Trigger: {nba.gap_reason.replace("_", " ")}
            </span>
          )}
        </div>

        <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
          <BookOpen className="w-3 h-3" />
          {intervention.type}
        </span>
      </div>

      {/* Primary Recommended Title */}
      <div className="mb-4">
        <h3 className="font-heading text-xl sm:text-2xl text-slate-900 tracking-normal leading-snug">
          {intervention.title}
        </h3>
      </div>

      {/* Reason & Explanation Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5 text-xs">
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
          <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-blue-600" />
            Why this action
          </div>
          <p className="text-slate-700 leading-relaxed font-sans">
            {intervention.reason}
          </p>
        </div>

        {nba.explanation && (
          <div className="bg-teal-50/50 p-4 rounded-lg border border-teal-100">
            <div className="text-[11px] font-semibold text-teal-700 uppercase tracking-wider mb-1">
              Expected Outcome
            </div>
            <p className="text-teal-950 leading-relaxed font-sans">
              {nba.explanation}
            </p>
          </div>
        )}
      </div>

      {/* Action Footer */}
      <div className="flex items-center justify-end pt-2 border-t border-slate-100">
        {onStartAction ? (
          <button
            type="button"
            onClick={onStartAction}
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm"
          >
            <span>Start Task</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        ) : (
          <Link
            href="/dashboard/tasks"
            className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm"
          >
            <span>View Tasks</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </Link>
        )}
      </div>
    </div>
  );
});

NextBestActionCard.displayName = "NextBestActionCard";
