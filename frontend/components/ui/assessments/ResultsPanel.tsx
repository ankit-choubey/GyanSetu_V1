"use client";

import React from "react";
import { AssessmentSubmitResponse } from "@/lib/api/types";
import { CheckCircle2, XCircle, Award, Target, ArrowRight } from "lucide-react";
import { cn } from "@/lib/cn";

interface ResultsPanelProps {
  competencyName: string;
  result: AssessmentSubmitResponse;
  onFinish: () => void;
}

export function ResultsPanel({
  competencyName,
  result,
  onFinish,
}: ResultsPanelProps) {
  const isPassed = result.score >= 0.6;
  const nba = result.next_best_action;

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-6 sm:p-8 max-w-2xl w-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-4 border-b border-slate-100 mb-6">
        <div>
          <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider block">
            Assessment Results
          </span>
          <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mt-1">
            {competencyName}
          </h3>
        </div>

        <div className="flex items-center gap-2">
          <div
            className={cn(
              "w-12 h-12 rounded-full flex items-center justify-center font-body text-base font-bold tabular-nums border",
              isPassed
                ? "bg-teal-50 text-teal-700 border-teal-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            )}
          >
            {Math.round(result.score * 100)}%
          </div>
        </div>
      </div>

      {/* Stats Summary */}
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="text-xs text-slate-500 block">Updated Mastery</span>
          <span className="font-body font-bold text-2xl tabular-nums text-slate-900 mt-1 block">
            {Math.round(result.mastery * 100)}%
          </span>
        </div>
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-100">
          <span className="text-xs text-slate-500 block">Belief Confidence</span>
          <span className="font-body font-bold text-2xl tabular-nums text-slate-900 mt-1 block">
            {Math.round(result.confidence * 100)}%
          </span>
        </div>
      </div>

      {/* Per-question feedback */}
      <div className="mb-6">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">
          Diagnostic Feedback
        </h4>
        <div className="space-y-3">
          {result.feedback.map((item, index) => (
            <div
              key={index}
              className={cn(
                "p-4 rounded-xl border",
                item.is_correct
                  ? "bg-teal-50/50 border-teal-200"
                  : "bg-rose-50/50 border-rose-200"
              )}
            >
              <div className="flex items-center gap-2 mb-1.5">
                {item.is_correct ? (
                  <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0" />
                ) : (
                  <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                )}
                <span
                  className={cn(
                    "text-xs font-semibold uppercase tracking-wider",
                    item.is_correct ? "text-teal-800" : "text-rose-800"
                  )}
                >
                  {item.is_correct ? "Correct Response" : "Incorrect Response"}
                </span>
              </div>
              <p className="text-xs text-slate-700 leading-relaxed font-sans">
                {item.feedback}
              </p>
              {item.identified_gap && (
                <div className="mt-2 text-xs font-medium text-rose-700 bg-rose-100/60 px-2.5 py-1 rounded">
                  Identified Concept Gap: {item.identified_gap}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Next Best Action Card if available */}
      {nba && (
        <div className="mb-6 bg-blue-50/60 border border-blue-200 rounded-xl p-4">
          <div className="flex items-center gap-1.5 text-xs font-semibold text-blue-800 uppercase tracking-wider mb-1">
            <Target className="w-4 h-4 text-blue-600" />
            Recommended Practice
          </div>
          <div className="font-heading text-base text-slate-900 mb-1">
            {nba.selected_intervention.title}
          </div>
          <p className="text-xs text-slate-600 font-sans mb-2">
            {nba.selected_intervention.reason}
          </p>
          <span className="text-[11px] font-medium bg-blue-100 text-blue-800 px-2 py-0.5 rounded">
            {nba.selected_intervention.type}
          </span>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-end pt-4 border-t border-slate-100">
        <button
          type="button"
          onClick={onFinish}
          className="inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition active:scale-[0.98] shadow-xs"
        >
          <span>Return to Assessments</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
