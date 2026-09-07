"use client";

import React from "react";
import { BackendCompetency } from "@/lib/api/types";
import { ArrowRight, CheckCircle2, Circle, AlertCircle, HelpCircle } from "lucide-react";
import { cn } from "@/lib/cn";

interface CompetencyAssessmentCardProps {
  competency: BackendCompetency;
  index: number;
  onStart: (competency: BackendCompetency) => void;
}

const ACCENT_COLORS = [
  "bg-blue-500",
  "bg-teal-500",
  "bg-amber-500",
  "bg-indigo-500",
  "bg-rose-500",
];

export const CompetencyAssessmentCard = React.memo(
  function CompetencyAssessmentCard({
    competency,
    index,
    onStart,
  }: CompetencyAssessmentCardProps) {
    const isUnassessed = competency.mastery === null;
    const accentColor = ACCENT_COLORS[index % ACCENT_COLORS.length];

    const getConfidenceLabel = (conf: number) => {
      if (conf >= 0.7) return "High";
      if (conf >= 0.4) return "Medium";
      return "Low";
    };

    return (
      <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-xs hover:shadow-md transition-all relative overflow-hidden flex flex-col justify-between min-h-[260px] group">
        {/* Top 4px colored accent strip */}
        <div className={cn("absolute top-0 left-0 right-0 h-1", accentColor)} />

        <div>
          {/* Status & ID Row */}
          <div className="flex items-center justify-between gap-2 mb-3">
            <span className="text-xs font-semibold text-slate-400">
              Competency #{competency.competency_id}
            </span>
            <span
              className={cn(
                "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border",
                competency.status === "ASSESSED"
                  ? "bg-teal-50 text-teal-800 border-teal-200"
                  : competency.status === "CONFLICTING_EVIDENCE"
                  ? "bg-amber-50 text-amber-800 border-amber-200"
                  : "bg-slate-100 text-slate-600 border-slate-200"
              )}
            >
              {competency.status === "ASSESSED" ? (
                <CheckCircle2 className="w-3 h-3 text-teal-600" />
              ) : competency.status === "CONFLICTING_EVIDENCE" ? (
                <AlertCircle className="w-3 h-3 text-amber-600" />
              ) : (
                <Circle className="w-3 h-3 text-slate-400" />
              )}
              {competency.status.replace("_", " ")}
            </span>
          </div>

          {/* Competency Title */}
          <h3 className="font-heading text-xl text-slate-900 mb-4 group-hover:text-blue-600 transition-colors">
            {competency.competency_name}
          </h3>

          {/* Stats Row */}
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Mastery</span>
              <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
                {isUnassessed ? "—" : `${Math.round(competency.mastery! * 100)}%`}
              </span>
            </div>

            <div className="bg-slate-50 p-3 rounded-lg border border-slate-100">
              <span className="text-[11px] text-slate-500 block">Confidence</span>
              <span className="font-heading text-2xl text-slate-900 mt-0.5 block">
                {isUnassessed ? "—" : getConfidenceLabel(competency.confidence)}
              </span>
            </div>
          </div>

          <div className="text-xs text-slate-500 mb-2">
            Evidence: {competency.evidence_count} recorded item{competency.evidence_count === 1 ? "" : "s"}
          </div>
        </div>

        {/* CTA Button */}
        <div className="pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={() => onStart(competency)}
            className="w-full inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition active:scale-[0.98] shadow-xs"
          >
            <span>{isUnassessed ? "Start Assessment" : "Retake Assessment"}</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    );
  }
);

CompetencyAssessmentCard.displayName = "CompetencyAssessmentCard";
