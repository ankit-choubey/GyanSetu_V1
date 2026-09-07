"use client";

import React, { useState } from "react";
import { AdaptiveQuestionResponse } from "@/lib/api/types";
import { HelpCircle, CheckCircle2, Loader2, ArrowRight } from "lucide-react";
import { cn } from "@/lib/cn";

interface QuestionPanelProps {
  competencyName: string;
  question: AdaptiveQuestionResponse;
  isSubmitting: boolean;
  onSubmit: (selectedOption: string) => void;
  onCancel: () => void;
}

export function QuestionPanel({
  competencyName,
  question,
  isSubmitting,
  onSubmit,
  onCancel,
}: QuestionPanelProps) {
  const [selected, setSelected] = useState<string | null>(null);

  const options = question.options || [];

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selected || isSubmitting) return;
    onSubmit(selected);
  };

  return (
    <div className="bg-white rounded-2xl border border-slate-200 shadow-xl p-6 sm:p-8 max-w-2xl w-full">
      {/* Header */}
      <div className="flex items-center justify-between gap-3 pb-4 border-b border-slate-100 mb-6">
        <div>
          <span className="text-xs font-semibold text-blue-600 uppercase tracking-wider block">
            {competencyName}
          </span>
          <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mt-1">
            Adaptive Diagnostic Item
          </h3>
        </div>

        {question.difficulty && (
          <span
            className={cn(
              "px-2.5 py-1 rounded text-xs font-medium uppercase tracking-wider border",
              question.difficulty === "hard"
                ? "bg-rose-50 text-rose-700 border-rose-200"
                : question.difficulty === "medium"
                ? "bg-amber-50 text-amber-700 border-amber-200"
                : "bg-teal-50 text-teal-700 border-teal-200"
            )}
          >
            {question.difficulty}
          </span>
        )}
      </div>

      {/* Question Text */}
      <div className="mb-6">
        <p className="text-slate-800 text-sm sm:text-base leading-relaxed font-sans font-medium">
          {question.question_text || "Consider the following statistical scenario and select the most appropriate method:"}
        </p>
      </div>

      {/* Options */}
      <form onSubmit={handleSubmit}>
        <div className="space-y-3 mb-6">
          {options.map((opt, idx) => {
            const isChecked = selected === opt;
            const optionKey = opt.slice(0, 2);

            return (
              <button
                key={idx}
                type="button"
                onClick={() => setSelected(opt)}
                className={cn(
                  "w-full text-left p-4 rounded-xl border transition-all flex items-start gap-3",
                  isChecked
                    ? "bg-blue-50/70 border-blue-600 ring-2 ring-blue-600/20 shadow-xs"
                    : "bg-white border-slate-200 hover:border-blue-300 hover:bg-slate-50/50"
                )}
              >
                <div
                  className={cn(
                    "w-5 h-5 rounded-full border flex items-center justify-center text-xs font-bold shrink-0 mt-0.5 transition",
                    isChecked
                      ? "bg-blue-600 border-blue-600 text-white"
                      : "border-slate-300 bg-white text-slate-500"
                  )}
                >
                  {isChecked ? (
                    <CheckCircle2 className="w-3.5 h-3.5" />
                  ) : (
                    optionKey.replace(".", "")
                  )}
                </div>
                <span className="text-xs sm:text-sm text-slate-800 leading-normal font-sans">
                  {opt}
                </span>
              </button>
            );
          })}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <button
            type="button"
            onClick={onCancel}
            disabled={isSubmitting}
            className="px-4 py-2 text-xs font-medium text-slate-600 hover:bg-slate-100 rounded-lg transition"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={!selected || isSubmitting}
            className={cn(
              "inline-flex items-center gap-2 px-5 py-2.5 rounded-lg text-xs font-medium text-white transition shadow-xs",
              !selected || isSubmitting
                ? "bg-blue-300 cursor-not-allowed"
                : "bg-blue-600 hover:bg-blue-700 active:scale-[0.98]"
            )}
          >
            {isSubmitting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Evaluating response...</span>
              </>
            ) : (
              <>
                <span>Submit Answer</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
