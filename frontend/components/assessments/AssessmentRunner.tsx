"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, AlertCircle, CheckCircle2, Loader2, Lightbulb, GraduationCap, ChevronDown, Award
} from "lucide-react";
import { cn } from "@/lib/cn";
import confetti from "canvas-confetti";
import { client } from "@/lib/api/client";
import { QUESTION_BANK, AssessmentQuestion } from "./questionBank";

interface AssessmentRunnerProps {
  sessionId: string;
  tier: "easy" | "medium" | "tough";
  onClose: (score?: number, passed?: boolean) => void;
}

export function AssessmentRunner({ sessionId, tier, onClose }: AssessmentRunnerProps) {
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [expandedFeedback, setExpandedFeedback] = useState<string | null>(null);

  useEffect(() => {
    async function loadQuestions() {
      // 1. Check if dynamically generated questions exist (from YouTube or document ingestion)
      const cached = typeof window !== "undefined" ? localStorage.getItem("active_assessment_questions") : null;
      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length >= 5) {
            setQuestions(parsed);
            return;
          }
        } catch (e) {
          console.warn("Failed to parse cached questions:", e);
        }
      }

      // 2. Default to the comprehensive 15-question bank for the active tier
      const defaultSet = QUESTION_BANK[tier] || QUESTION_BANK.easy;
      setQuestions(defaultSet);
    }
    loadQuestions();
  }, [tier]);

  const handleSelect = (qId: string, optId: string) => {
    setAnswers(prev => ({ ...prev, [qId]: optId }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    await new Promise(resolve => setTimeout(resolve, 600));

    let correctCount = 0;
    const evaluatedItems = questions.map((q) => {
      const userSelected = answers[q.id] || "None";
      const correctOpt = q.correct_answer || "A";
      const isCorrect = userSelected.toUpperCase() === correctOpt.toUpperCase();
      if (isCorrect) correctCount++;

      return {
        question_id: q.id,
        is_correct: isCorrect,
        user_selected: userSelected,
        correct_option: correctOpt,
        why_wrong: !isCorrect 
          ? (q.explanation || "Selected answer does not match the official statistical standard.") 
          : undefined,
        why_right: isCorrect 
          ? (q.explanation || "Correct! Excellent precision and understanding.") 
          : undefined,
        misconception_hint: !isCorrect 
          ? (q.misconception || `Key insight: Option ${correctOpt} correctly addresses the problem.`) 
          : undefined,
        remediation_steps: !isCorrect 
          ? (q.remediation || ["Review the corresponding official handbook section.", "Practice active recall on this topic."]) 
          : undefined,
      };
    });

    const total = questions.length > 0 ? questions.length : 15;
    const score = Math.round((correctCount / total) * 100);
    const passed = score >= 70;

    // Persist assessment to real backend database for authenticated user
    try {
      await client.post("/api/assessment/runner-submit", {
        competency_id: tier === "easy" ? 1 : tier === "medium" ? 2 : 3,
        tier,
        score,
        passed,
        total_questions: total,
        correct_count: correctCount,
      });
    } catch (apiErr) {
      console.warn("Persisting assessment attempt failed or offline:", apiErr);
    }

    if (passed) {
      confetti({
        particleCount: 120,
        spread: 80,
        origin: { y: 0.6 },
        colors: ['#047857', '#2563EB', '#7C3AED']
      });
    }

    setResults({
      score,
      passed,
      correctCount,
      totalCount: total,
      next_tier_unlocked: passed ? (tier === "easy" ? "medium" : tier === "medium" ? "tough" : null) : null,
      items: evaluatedItems
    });
    setIsSubmitting(false);
  };

  if (results) {
    return (
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden"
      >
        <div className={cn(
          "p-8 text-center border-b font-sans",
          results.passed ? "bg-emerald-50/50 border-emerald-100" : "bg-rose-50/50 border-rose-100"
        )}>
          {results.passed ? (
            <Award className="w-14 h-14 text-emerald-600 mx-auto mb-3" />
          ) : (
            <AlertCircle className="w-14 h-14 text-rose-600 mx-auto mb-3" />
          )}
          <div className="font-heading font-bold text-5xl tabular-nums text-slate-900 mb-1">
            {results.score}%
          </div>
          <p className="text-sm font-semibold text-slate-700 mb-2">
            {results.correctCount} of {results.totalCount} Questions Correct
          </p>
          <p className="text-xs font-medium text-slate-600 mb-4 max-w-md mx-auto">
            {results.passed 
              ? "Assessment successfully passed (≥ 70% threshold). Your competency mastery has been recorded in the platform." 
              : "Passing score is 70%. Review the coach's tips and remediation below to strengthen key competencies."}
          </p>
          {results.next_tier_unlocked && (
            <div className="inline-flex items-center gap-2 px-4 py-1.5 bg-blue-50 text-blue-800 rounded-full text-xs font-semibold border border-blue-200">
              Next Tier Unlocked: Tier '{results.next_tier_unlocked.toUpperCase()}' is now available
            </div>
          )}
        </div>

        <div className="p-6 sm:p-8 bg-slate-50">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-heading text-slate-900">Detailed Feedback & Misconceptions ({results.totalCount} Questions)</h3>
            <span className="text-xs font-medium text-slate-500">Click each question to view coach tips</span>
          </div>
          <div className="space-y-3">
            {results.items.map((res: any, idx: number) => {
              const q = questions.find(qu => qu.id === res.question_id);
              const isExpanded = expandedFeedback === res.question_id;
              
              return (
                <div key={res.question_id} className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-xs">
                  <div 
                    className="p-4 flex items-start gap-4 cursor-pointer hover:bg-slate-50 transition"
                    onClick={() => setExpandedFeedback(isExpanded ? null : res.question_id)}
                  >
                    {res.is_correct ? (
                      <CheckCircle2 className="w-6 h-6 text-emerald-500 shrink-0 mt-0.5" />
                    ) : (
                      <AlertCircle className="w-6 h-6 text-rose-500 shrink-0 mt-0.5" />
                    )}
                    <div className="flex-1">
                      <p className="text-sm font-medium text-slate-900">{idx + 1}. {q?.text}</p>
                      <p className="text-xs text-slate-500 mt-1">
                        Your answer: <span className="font-semibold text-slate-700">{res.user_selected}</span>
                        {!res.is_correct && (
                          <span className="ml-3 text-emerald-600 font-semibold">
                            Correct: {res.correct_option}
                          </span>
                        )}
                      </p>
                    </div>
                    <ChevronDown className={cn("w-5 h-5 text-slate-400 transition-transform", isExpanded && "rotate-180")} />
                  </div>

                  <AnimatePresence>
                    {isExpanded && (
                      <motion.div 
                        initial={{ height: 0 }}
                        animate={{ height: "auto" }}
                        exit={{ height: 0 }}
                        className="overflow-hidden border-t border-slate-100"
                      >
                        <div className="p-4 bg-slate-50 space-y-3">
                          {res.is_correct ? (
                            <p className="text-sm text-emerald-800 bg-emerald-50 p-3 rounded-md border border-emerald-100">
                              <span className="font-semibold">Why you got it right:</span> {res.why_right}
                            </p>
                          ) : (
                            <div className="space-y-3">
                              <p className="text-sm text-rose-800 bg-rose-50 p-3 rounded-md border border-rose-100">
                                <span className="font-semibold">Explanation:</span> {res.why_wrong}
                              </p>
                              
                              {res.misconception_hint && (
                                <div className="flex gap-3 items-start bg-amber-50 p-3 rounded-md border border-amber-100">
                                  <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                                  <div>
                                    <p className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-0.5">Coach's Insight</p>
                                    <p className="text-sm text-amber-900">{res.misconception_hint}</p>
                                  </div>
                                </div>
                              )}

                              {res.remediation_steps && (
                                <div className="flex gap-3 items-start bg-blue-50 p-3 rounded-md border border-blue-100">
                                  <GraduationCap className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                                  <div>
                                    <p className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-1">Recommended Action Steps</p>
                                    <ul className="list-disc list-inside text-sm text-blue-900 space-y-1">
                                      {res.remediation_steps.map((step: string, i: number) => (
                                        <li key={i}>{step}</li>
                                      ))}
                                    </ul>
                                  </div>
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      </motion.div>
                    )}
                  </AnimatePresence>
                </div>
              );
            })}
          </div>

          <div className="mt-8 flex justify-end">
            <button
              onClick={() => onClose(results.score, results.passed)}
              className="px-6 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition shadow-sm"
            >
              Return to Dashboard
            </button>
          </div>
        </div>
      </motion.div>
    );
  }

  if (questions.length === 0) return null;

  const currentQ = questions[currentIdx];
  const progressPercent = Math.round(((currentIdx + 1) / questions.length) * 100);
  const answeredCount = Object.keys(answers).length;

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden relative"
    >
      <button 
        onClick={() => onClose()}
        className="absolute top-4 right-4 p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 rounded-full transition z-10"
        title="Exit Assessment"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Header bar */}
      <div className="bg-slate-50 p-5 sm:p-6 border-b border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                {tier} Tier
              </span>
              <span className="text-xs text-slate-500 font-medium">
                {questions.length} Questions Total • 70% Pass Standard
              </span>
            </div>
            <h2 className="text-xl font-heading font-bold text-slate-900 mt-1">
              Question {currentIdx + 1} of {questions.length}
            </h2>
          </div>
          <div className="text-right">
            <span className="text-xs font-semibold text-slate-600">
              Answered: {answeredCount} / {questions.length}
            </span>
          </div>
        </div>

        {/* Progress Bar */}
        <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden mb-3">
          <div 
            className="bg-blue-600 h-full transition-all duration-300 rounded-full"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        {/* Numbered Question Navigator (1 to 15) */}
        <div className="flex flex-wrap gap-1.5 pt-1">
          {questions.map((q, i) => {
            const isAnswered = !!answers[q.id];
            const isCurrent = i === currentIdx;
            return (
              <button
                key={q.id || i}
                onClick={() => setCurrentIdx(i)}
                className={cn(
                  "w-7 h-7 rounded text-xs font-semibold transition-all flex items-center justify-center",
                  isCurrent 
                    ? "bg-blue-600 text-white shadow-sm ring-2 ring-blue-400/40" 
                    : isAnswered
                    ? "bg-emerald-100 text-emerald-800 hover:bg-emerald-200"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                )}
                title={`Jump to Question ${i + 1}`}
              >
                {i + 1}
              </button>
            );
          })}
        </div>
      </div>

      {/* Question Content */}
      <div className="p-6 sm:p-8">
        <p className="text-base sm:text-lg font-medium text-slate-900 mb-6 leading-relaxed">
          {currentQ.text}
        </p>

        <div className="space-y-3">
          {currentQ.options.map((opt: any) => {
            const isSelected = answers[currentQ.id] === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => handleSelect(currentQ.id, opt.id)}
                className={cn(
                  "w-full text-left p-4 rounded-lg border transition-all flex items-center gap-4 group",
                  isSelected 
                    ? "border-blue-500 bg-blue-50/50 shadow-xs ring-1 ring-blue-500/30" 
                    : "border-slate-200 hover:border-slate-300 hover:bg-slate-50"
                )}
              >
                <div className={cn(
                  "w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold shrink-0 transition-colors",
                  isSelected ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-600 group-hover:bg-slate-200"
                )}>
                  {opt.id}
                </div>
                <span className={cn("text-sm", isSelected ? "text-slate-900 font-medium" : "text-slate-700")}>
                  {opt.text}
                </span>
              </button>
            );
          })}
        </div>

        {/* Footer Navigation */}
        <div className="mt-8 pt-6 border-t border-slate-100 flex justify-between items-center">
          <button
            onClick={() => setCurrentIdx(p => Math.max(0, p - 1))}
            disabled={currentIdx === 0}
            className="px-4 py-2 text-sm font-medium text-slate-600 disabled:opacity-40 disabled:cursor-not-allowed hover:bg-slate-100 rounded-lg transition"
          >
            Previous
          </button>

          <div className="flex items-center gap-3">
            {currentIdx < questions.length - 1 ? (
              <button
                onClick={() => setCurrentIdx(p => Math.min(questions.length - 1, p + 1))}
                className="px-5 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition"
              >
                Next Question
              </button>
            ) : null}

            <button
              onClick={handleSubmit}
              disabled={answeredCount < questions.length || isSubmitting}
              className={cn(
                "px-6 py-2 rounded-lg text-sm font-semibold shadow-sm transition flex items-center gap-2",
                answeredCount === questions.length
                  ? "bg-emerald-600 text-white hover:bg-emerald-700"
                  : "bg-slate-300 text-slate-600 cursor-not-allowed"
              )}
            >
              {isSubmitting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Scoring...</>
              ) : (
                `Submit Assessment (${answeredCount}/${questions.length})`
              )}
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
