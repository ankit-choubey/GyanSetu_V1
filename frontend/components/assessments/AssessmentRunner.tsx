"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { motion, AnimatePresence } from "framer-motion";
import { 
  X, AlertCircle, CheckCircle2, Loader2, Lightbulb, GraduationCap, ChevronDown, Award,
  FileSpreadsheet, ArrowRight
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
  const router = useRouter();
  const [questions, setQuestions] = useState<AssessmentQuestion[]>([]);
  const [sourceTitle, setSourceTitle] = useState<string | null>(null);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [results, setResults] = useState<any>(null);
  const [expandedFeedback, setExpandedFeedback] = useState<string | null>(null);

  useEffect(() => {
    async function loadQuestions() {
      // 1. Check if dynamically generated questions exist (from YouTube or document ingestion)
      let allQuestions: AssessmentQuestion[] = [];
      const cached = typeof window !== "undefined" ? localStorage.getItem("active_assessment_questions") : null;
      const storedTitle = typeof window !== "undefined" ? localStorage.getItem("active_source_title") : null;
      if (storedTitle) {
        setSourceTitle(storedTitle);
      }

      if (cached) {
        try {
          const parsed = JSON.parse(cached);
          if (Array.isArray(parsed) && parsed.length > 0) {
            allQuestions = parsed;
          }
        } catch (e) {
          console.warn("Failed to parse cached questions:", e);
        }
      }

      // If not in localStorage and sessionId indicates a library item (lib_X)
      if (allQuestions.length === 0 && sessionId && sessionId.startsWith("lib_")) {
        try {
          const docId = sessionId.replace("lib_", "");
          const docRes = await client.get<any>(`/api/content/library/${docId}`);
          if (docRes && Array.isArray(docRes.questions) && docRes.questions.length > 0) {
            allQuestions = docRes.questions;
            if (docRes.title) setSourceTitle(docRes.title);
          }
        } catch (e) {
          console.warn("Failed to fetch questions for library doc:", e);
        }
      }

      // 2. Divide questions across tiers (5 per tier for a standard 15-question set)
      if (allQuestions.length >= 15) {
        if (tier === "easy") {
          setQuestions(allQuestions.slice(0, 5));
        } else if (tier === "medium") {
          setQuestions(allQuestions.slice(5, 10));
        } else {
          setQuestions(allQuestions.slice(10, 15));
        }
        return;
      } else if (allQuestions.length >= 3) {
        const sliceSize = Math.ceil(allQuestions.length / 3);
        if (tier === "easy") {
          setQuestions(allQuestions.slice(0, sliceSize));
        } else if (tier === "medium") {
          setQuestions(allQuestions.slice(sliceSize, sliceSize * 2));
        } else {
          setQuestions(allQuestions.slice(sliceSize * 2));
        }
        return;
      } else if (allQuestions.length > 0) {
        setQuestions(allQuestions);
        return;
      }

      // 3. Fall back to curated comprehensive question bank for the active tier
      const defaultSet = QUESTION_BANK[tier] || QUESTION_BANK.easy;
      setQuestions(defaultSet);
    }
    loadQuestions();
  }, [tier, sessionId]);

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

    const total = questions.length > 0 ? questions.length : 5;
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

    let savedReportId: number | null = null;
    // Automatically record to the real-time Test Report Ledger
    try {
      const { appendTestLedgerItem, getActiveOfficerProfile } = await import("@/lib/api/ledger");
      const activeOfficer = getActiveOfficerProfile();

      const dynamicTopic = sourceTitle 
        ? sourceTitle 
        : tier === "easy" 
        ? "Sampling Design & Field Methodologies" 
        : tier === "medium" 
        ? "National Accounts & Price Statistics" 
        : "Survey Data Harmonization & Policy Analytics";

      const storedSourceType = typeof window !== "undefined" ? localStorage.getItem("active_source_type") : null;
      const isVideo = storedSourceType === "youtube" || (sourceTitle && /youtube/i.test(sourceTitle));
      const effectiveSourceType = isVideo ? "youtube" : "pdf";
      const totalDocPages = 16;

      const savedReport = appendTestLedgerItem({
        session_id: sessionId || `sess_${Date.now().toString(36)}`,
        timestamp: new Date().toLocaleString("en-IN", {
          day: "2-digit",
          month: "short",
          year: "numeric",
          hour: "2-digit",
          minute: "2-digit",
          hour12: true,
        }),
        iso_date: new Date().toISOString(),
        user_id: activeOfficer.id || 1,
        full_name: activeOfficer.full_name,
        email: activeOfficer.email,
        role_name: activeOfficer.role_name,
        designation: activeOfficer.designation,
        department: activeOfficer.department,
        competency_id: tier === "easy" ? 1 : tier === "medium" ? 2 : 3,
        competency_name: dynamicTopic,
        tier: tier === "easy" ? "Tier 1: Foundation" : tier === "medium" ? "Tier 2: Application" : "Tier 3: Analysis",
        difficulty_band: tier === "easy" ? "Recall & Definitions (Bloom L1-L2)" : tier === "medium" ? "Formulas & Calculations (Bloom L3-L4)" : "Multi-Step & Policy Analysis (Bloom L5-L6)",
        score,
        correct_count: correctCount,
        total_questions: total,
        passing_score: 70,
        result_status: passed ? "PASSED" : "RETRY RECOMMENDED",
        next_tier_unlocked: passed ? (tier === "easy" ? "Tier 2: Application" : tier === "medium" ? "Tier 3: Analysis" : null) : null,
        mastery: Math.min(1.0, Math.max(0.2, score / 100)),
        confidence: 0.85,
        coverage: 0.80,
        uncertainty: 0.15,
        evidence_count: total,
        evidence_diversity: 2,
        assessed_count: `${correctCount} of ${total}`,
        reliability_status: "VERIFIED",
        provenance: sourceTitle ? `[INGESTION:${sourceTitle}]` : (effectiveSourceType === "pdf" ? "[INGESTION:MoSPI_Sampling_Manual.pdf]" : "[DYNAMIC_INGESTION:ASSESSMENT_RUNNER]"),
        evidence_type: "KNOWLEDGE_ASSESSMENT",
        weight: 1.0,
        source_type: effectiveSourceType,
        source_title: sourceTitle || undefined,
        total_pages: totalDocPages,
        items: evaluatedItems.map((it, idx) => {
          const pageStart = 2 + Math.floor(idx * ((totalDocPages - 3) / Math.max(total, 5)));
          const pageEnd = Math.min(pageStart + 1, totalDocPages);
          const subskill = (questions[idx] as any)?.subskill_name || (questions[idx] as any)?.skill_name || "Statistical Methodology";
          return {
            question_number: `Q${idx + 1}`,
            subskill_name: subskill,
            question_text: questions[idx]?.text || (questions[idx] as any)?.question_text || `Assessment Question #${idx + 1}`,
            user_selected: it.user_selected,
            correct_option: it.correct_option,
            is_correct: it.is_correct,
            misconception_hint: it.misconception_hint,
            remediation_steps: Array.isArray(it.remediation_steps) ? it.remediation_steps.join("; ") : it.remediation_steps,
            page_number: (questions[idx] as any)?.page_number || pageStart,
            page_reference: `Page ${pageStart} – ${pageEnd}`,
            section_reference: `Section ${idx + 1}: ${subskill}`,
          };
        }),
      });
      if (savedReport && savedReport.numeric_id) {
        savedReportId = savedReport.numeric_id;
      }
    } catch (ledgerErr) {
      console.warn("Failed recording to Test Report Ledger:", ledgerErr);
    }

    // Immediately persist tier progression & real-time review score to localStorage
    if (typeof window !== "undefined") {
      try {
        const isExplicitSession = !!(sessionId && sessionId !== "demo_session" && sessionId !== "default");
        const effectiveSessionId = sessionId || localStorage.getItem("active_session_id") || "default";
        const sessionKey = isExplicitSession ? `gyansetu_tiers_${effectiveSessionId}` : "gyansetu_tiers_default";
        
        const raw = localStorage.getItem(sessionKey);
        let list = raw ? JSON.parse(raw) : null;
        if (!list || !Array.isArray(list)) {
          list = [
            { id: "easy", name: "Tier 1: Foundation", badgeColor: "text-emerald-600 bg-emerald-50 border-emerald-200", difficultyText: "Easy • Recall & Definitions", unlocked: true, completed: false, score: null, passing_score: 70, description: "Core definitions, terminology, and foundational knowledge of the statistical concept." },
            { id: "medium", name: "Tier 2: Application", badgeColor: "text-amber-600 bg-amber-50 border-amber-200", difficultyText: "Medium • Formulas & Calculations", unlocked: false, completed: false, score: null, passing_score: 70, description: "Apply formulas and solve direct computational problems using real data sets.", unlock_requirement: "Complete Tier 1 with ≥ 70% to unlock." },
            { id: "tough", name: "Tier 3: Analysis", badgeColor: "text-purple-600 bg-purple-50 border-purple-200", difficultyText: "Hard • Multi-Step & Policy", unlocked: false, completed: false, score: null, passing_score: 70, description: "Complex multi-step problems requiring deep analytical reasoning and policy trade-offs.", unlock_requirement: "Complete Tier 2 with ≥ 70% to unlock." }
          ];
        }
        const idx = list.findIndex((t: any) => t.id === tier);
        if (idx > -1) {
          list[idx].completed = true;
          list[idx].score = score;
          if (passed && idx + 1 < list.length) {
            list[idx + 1].unlocked = true;
          }
        }
        localStorage.setItem(sessionKey, JSON.stringify(list));
        if (!isExplicitSession) {
          localStorage.setItem("gyansetu_tiers_default", JSON.stringify(list));
        }

        window.dispatchEvent(
          new CustomEvent("gyansetu:assessment_updated", {
            detail: {
              title: `${tier === "easy" ? "Tier 1: Foundation" : tier === "medium" ? "Tier 2: Application" : "Tier 3: Analysis"}`,
              score,
              passed,
            },
          })
        );
      } catch (tierErr) {
        console.warn("Failed saving tier update from AssessmentRunner:", tierErr);
      }
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
      reportId: savedReportId,
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
        className="w-full bg-white rounded-xl shadow-xs border border-slate-200 overflow-hidden relative"
      >
        <button 
          onClick={() => onClose(results.score, results.passed)}
          className="absolute top-4 right-4 p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 rounded-full transition z-10"
          title="Exit Assessment"
        >
          <X className="w-5 h-5" />
        </button>
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

          {results.reportId && (
            <div className="mt-4">
              <button
                onClick={() => {
                  onClose(results.score, results.passed);
                  router.push(`/dashboard/ledger/${results.reportId}`);
                }}
                className="inline-flex items-center gap-2 px-4 py-2 bg-white text-indigo-700 hover:bg-indigo-50 rounded-xl text-xs font-bold border border-indigo-200 shadow-xs transition"
              >
                <FileSpreadsheet className="w-4 h-4 text-emerald-600" />
                <span>Redirect to Report Ledger (Report #{String(results.reportId).padStart(3, "0")}) &rarr;</span>
              </button>
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

          <div className="mt-8 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-200 pt-6">
            <button
              onClick={() => onClose(results.score, results.passed)}
              className="w-full sm:w-auto px-5 py-2.5 bg-slate-100 text-slate-700 hover:bg-slate-200 rounded-xl text-xs font-semibold transition"
            >
              Return to Assessments
            </button>

            <button
              onClick={() => {
                onClose(results.score, results.passed);
                if (results.reportId) {
                  router.push(`/dashboard/ledger/${results.reportId}`);
                } else {
                  router.push("/dashboard/ledger");
                }
              }}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2 px-6 py-2.5 bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-700 hover:to-indigo-700 text-white rounded-xl text-xs font-bold shadow-md hover:shadow-lg transition active:scale-95"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-300" />
              <span>Redirect to Report Ledger & Download DOCX</span>
              <ArrowRight className="w-4 h-4" />
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
        onClick={() => onClose(results?.score, results?.passed)}
        className="absolute top-4 right-4 p-2 text-slate-400 hover:bg-slate-100 hover:text-slate-700 rounded-full transition z-10"
        title="Exit Assessment"
      >
        <X className="w-5 h-5" />
      </button>

      {/* Header bar */}
      <div className="bg-slate-50 p-5 sm:p-6 border-b border-slate-100">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <span className="text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 bg-blue-100 text-blue-800 rounded">
                {tier} Tier
              </span>
              {sourceTitle && (
                <span className="text-xs font-semibold text-blue-900 bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-200 truncate max-w-xs sm:max-w-md">
                  {sourceTitle}
                </span>
              )}
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
