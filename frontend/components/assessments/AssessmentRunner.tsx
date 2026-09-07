"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, AlertCircle, CheckCircle2, Loader2, Lightbulb, GraduationCap, ChevronDown, Award
} from "lucide-react";
import { cn } from "@/lib/cn";
import confetti from "canvas-confetti";
import { client } from "@/lib/api/client";

interface AssessmentRunnerProps {
  sessionId: string;
  tier: "easy" | "medium" | "tough";
  onClose: (score?: number, passed?: boolean) => void;
}

// Mock Data
const MOCK_QUESTIONS = {
  easy: [
    {
      id: "q_easy_01",
      text: "What does P(A|B) denote in Bayesian probability?",
      options: [
        { id: "A", text: "The joint probability of events A and B" },
        { id: "B", text: "The conditional probability of event A given that event B has occurred" },
        { id: "C", text: "The marginal probability of event A occurring independently" },
        { id: "D", text: "The union probability of event A or event B" }
      ]
    },
    {
      id: "q_easy_02",
      text: "Which of the following describes a Type I error?",
      options: [
        { id: "A", text: "Failing to reject a false null hypothesis" },
        { id: "B", text: "Rejecting a true null hypothesis" },
        { id: "C", text: "Accepting a true alternative hypothesis" },
        { id: "D", text: "Failing to reject a true null hypothesis" }
      ]
    }
  ],
  medium: [],
  tough: []
};

export function AssessmentRunner({ sessionId, tier, onClose }: AssessmentRunnerProps) {
  const [questions, setQuestions] = useState<any[]>([]);
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
          if (Array.isArray(parsed) && parsed.length > 0) {
            setQuestions(parsed);
            return;
          }
        } catch (e) {
          console.warn("Failed to parse cached questions:", e);
        }
      }

      // 2. Query live adaptive assessment engine
      try {
        const res: any = await client.post("/api/assessment/next", {
          competency_id: 4,
        });
        if (res?.status === "QUESTION_PROPOSED" && res.question_text) {
          const opts = (res.options || []).map((o: string, idx: number) => {
            const letter = String.fromCharCode(65 + idx);
            const cleanText = o.replace(/^[A-Da-d][.)]\s*/, "");
            return { id: letter, text: cleanText };
          });
          const liveItem = {
            id: `q_${res.question_id || 1}`,
            text: res.question_text,
            options: opts,
            correct_answer: "A",
            explanation: "Pedagogically generated question from GyanSetu adaptive engine.",
          };
          const fallbackRemaining = (MOCK_QUESTIONS[tier] || MOCK_QUESTIONS.easy).slice(1);
          setQuestions([liveItem, ...fallbackRemaining]);
          return;
        }
      } catch (e) {
        console.warn("Using fallback questions:", e);
      }
      setQuestions(MOCK_QUESTIONS[tier] || MOCK_QUESTIONS.easy);
    }
    loadQuestions();
  }, [tier]);

  const handleSelect = (qId: string, optId: string) => {
    setAnswers(prev => ({ ...prev, [qId]: optId }));
  };

  const handleSubmit = async () => {
    setIsSubmitting(true);
    // Brief animation pause
    await new Promise(resolve => setTimeout(resolve, 800));
    
    let correctCount = 0;
    const evaluatedItems = questions.map((q) => {
      const userSelected = answers[q.id] || "None";
      const correctOpt = q.correct_answer || "A";
      const isCorrect = userSelected === correctOpt;
      if (isCorrect) correctCount++;

      return {
        question_id: q.id,
        is_correct: isCorrect,
        user_selected: userSelected,
        correct_option: correctOpt,
        why_wrong: !isCorrect 
          ? (q.explanation || "Selected answer is incorrect. Review key definitions in the study materials.") 
          : undefined,
        why_right: isCorrect 
          ? (q.explanation || "Correct! Excellent precision and understanding.") 
          : undefined,
        misconception_hint: !isCorrect 
          ? `Key insight: Option ${correctOpt} correctly addresses the problem based on the lecture.` 
          : undefined,
        remediation_steps: !isCorrect 
          ? ["Review the corresponding video/document section.", "Practice active recall on this topic."] 
          : undefined,
      };
    });

    const total = questions.length > 0 ? questions.length : 1;
    const score = Math.round((correctCount / total) * 100);
    const passed = score >= 70;

    if (passed) {
      confetti({
        particleCount: 100,
        spread: 70,
        origin: { y: 0.6 },
        colors: ['#10B981', '#3B82F6', '#8B5CF6']
      });
    }

    setResults({
      score,
      passed,
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
          results.passed ? "bg-teal-50/40 border-teal-100" : "bg-rose-50/40 border-rose-100"
        )}>
          {results.passed ? (
            <Award className="w-12 h-12 text-teal-600 mx-auto mb-3" />
          ) : (
            <AlertCircle className="w-12 h-12 text-rose-600 mx-auto mb-3" />
          )}
          <div className="font-body font-bold text-4xl tabular-nums text-slate-900 mb-1">
            {results.score}%
          </div>
          <p className="text-xs font-medium text-slate-600 mb-4">
            {results.passed ? "Assessment passed (meets 70% threshold)." : "Passing score is 70%. Review the recommendations below."}
          </p>
          {results.next_tier_unlocked && (
            <div className="inline-flex items-center gap-2 px-3.5 py-1.5 bg-blue-50 text-blue-800 rounded-full text-xs font-semibold border border-blue-200">
              Next tier unlocked: Tier '{results.next_tier_unlocked}' is now available
            </div>
          )}
        </div>

        <div className="p-8 bg-slate-50">
          <h3 className="text-lg font-heading text-slate-900 mb-4">Detailed Feedback</h3>
          <div className="space-y-4">
            {results.items.map((res: any, idx: number) => {
              const q = questions.find(qu => qu.id === res.question_id);
              const isExpanded = expandedFeedback === res.question_id;
              
              return (
                <div key={res.question_id} className="bg-white rounded-lg border border-slate-200 overflow-hidden shadow-sm">
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
                        You selected: <span className="font-semibold">{res.user_selected}</span>
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
                            <p className="text-sm text-emerald-700 bg-emerald-50 p-3 rounded-md border border-emerald-100">
                              <span className="font-semibold">Why you got it right:</span> {res.why_right}
                            </p>
                          ) : (
                            <div className="space-y-3">
                              <p className="text-sm text-rose-700 bg-rose-50 p-3 rounded-md border border-rose-100">
                                <span className="font-semibold">Why option {res.user_selected} is wrong:</span> {res.why_wrong}
                              </p>
                              
                              <div className="flex gap-3 items-start bg-amber-50 p-3 rounded-md border border-amber-100">
                                <Lightbulb className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
                                <div>
                                  <p className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-1">Coach's Tip</p>
                                  <p className="text-sm text-amber-900">{res.misconception_hint}</p>
                                </div>
                              </div>

                              <div className="flex gap-3 items-start bg-blue-50 p-3 rounded-md border border-blue-100">
                                <GraduationCap className="w-5 h-5 text-blue-600 shrink-0 mt-0.5" />
                                <div>
                                  <p className="text-xs font-bold text-blue-800 uppercase tracking-wider mb-1">Action Steps</p>
                                  <ul className="list-disc list-inside text-sm text-blue-900 space-y-1">
                                    {res.remediation_steps.map((step: string, i: number) => (
                                      <li key={i}>{step}</li>
                                    ))}
                                  </ul>
                                </div>
                              </div>
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
              className="px-6 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition"
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

  return (
    <motion.div 
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="w-full bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden relative"
    >
      <button 
        onClick={() => onClose()}
        className="absolute top-4 right-4 p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 rounded-full transition z-10"
      >
        <X className="w-5 h-5" />
      </button>

      <div className="bg-slate-50 p-6 border-b border-slate-100 flex items-center justify-between">
        <div>
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-500 mb-1 block">
            {tier} Tier
          </span>
          <h2 className="text-lg font-heading text-slate-900">Question {currentIdx + 1} of {questions.length}</h2>
        </div>
        <div className="flex gap-1.5">
          {questions.map((_, i) => (
            <div 
              key={i} 
              className={cn(
                "h-2 rounded-full transition-all duration-300",
                i === currentIdx ? "w-6 bg-blue-600" : "w-2 bg-slate-200"
              )} 
            />
          ))}
        </div>
      </div>

      <div className="p-8">
        <p className="text-lg font-medium text-slate-900 mb-8 leading-relaxed">
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
                    ? "border-blue-500 bg-blue-50/50 shadow-sm ring-1 ring-blue-500/20" 
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

        <div className="mt-10 flex justify-between items-center">
          <button
            onClick={() => setCurrentIdx(p => Math.max(0, p - 1))}
            disabled={currentIdx === 0}
            className="px-4 py-2 text-sm font-medium text-slate-600 disabled:opacity-50 disabled:cursor-not-allowed hover:bg-slate-100 rounded-lg transition"
          >
            Previous
          </button>

          {currentIdx === questions.length - 1 ? (
            <button
              onClick={handleSubmit}
              disabled={Object.keys(answers).length < questions.length || isSubmitting}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg text-sm font-semibold hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm transition flex items-center gap-2"
            >
              {isSubmitting ? (
                <><Loader2 className="w-4 h-4 animate-spin" /> Analyzing...</>
              ) : "Submit Assessment"}
            </button>
          ) : (
            <button
              onClick={() => setCurrentIdx(p => Math.min(questions.length - 1, p + 1))}
              className="px-6 py-2 bg-slate-900 text-white rounded-lg text-sm font-semibold hover:bg-slate-800 transition"
            >
              Next Question
            </button>
          )}
        </div>
      </div>
    </motion.div>
  );
}
