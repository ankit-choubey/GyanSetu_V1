"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  ArrowLeft,
  Download,
  CheckCircle2,
  AlertCircle,
  Clock,
  HelpCircle,
  Lightbulb,
  Sparkles,
  Bot,
  MessageSquare,
} from "lucide-react";
import Script from "next/script";
import { TestLedgerItem } from "@/lib/api/types";
import { getLocalLedgerItems } from "@/lib/api/ledger";
import { generateTestReportDocx } from "@/lib/docx/reportGenerator";
import { cn } from "@/lib/cn";

export default function ReportDetailPage() {
  const params = useParams();
  const rawId = params?.id as string;
  const [item, setItem] = useState<TestLedgerItem | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  useEffect(() => {
    const all = getLocalLedgerItems();
    const found = all.find(
      (it) => String(it.numeric_id) === rawId || it.report_id.includes(rawId)
    );
    if (found) {
      setItem(found);
    }

    // Ensure OmniDimension widget script is dynamically appended if not already present
    if (typeof window !== "undefined" && !document.getElementById("omnidimension-web-widget")) {
      const script = document.createElement("script");
      script.id = "omnidimension-web-widget";
      script.src = "https://omnidim.io/web_widget.js?secret_key=2d39775642b445f9974532e7e04acd6e";
      script.async = true;
      document.body.appendChild(script);
    }
  }, [rawId]);

  const handleDownload = async () => {
    if (!item) return;
    setIsExporting(true);
    try {
      await generateTestReportDocx(item);
    } catch (e) {
      console.error("DOCX generation error:", e);
    } finally {
      setIsExporting(false);
    }
  };

  if (!item) {
    return (
      <div className="p-12 text-center text-slate-500">
        <p className="font-semibold text-slate-800">Test Report not found</p>
        <Link
          href="/dashboard/ledger"
          className="inline-flex items-center gap-1.5 mt-3 text-xs font-semibold text-blue-600 hover:text-blue-700"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Report Ledger</span>
        </Link>
      </div>
    );
  }

  const passed = item.result_status === "PASSED";

  return (
    <div className="space-y-6 pb-16 max-w-5xl mx-auto w-full">
      {/* TOP NAVIGATION & ACTIONS */}
      <div className="flex items-center justify-between gap-4">
        <Link
          href="/dashboard/ledger"
          className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-white border border-slate-200 px-3 py-1.5 rounded-lg shadow-xs transition"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Report Ledger</span>
        </Link>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => {
              const btn = document.getElementById("omni-open-widget-btn");
              if (btn) btn.click();
            }}
            className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition shadow-xs"
            title="Ask AI Remediation Coach"
          >
            <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
            <span>Ask AI Coach</span>
          </button>

          <button
            onClick={handleDownload}
            disabled={isExporting}
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition shadow-sm disabled:opacity-50"
          >
            <Download className="w-4 h-4" />
            <span>{isExporting ? "Generating DOCX..." : "Download Official DOCX"}</span>
          </button>
        </div>
      </div>

      {/* EXECUTIVE BANNER */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-6 mb-6">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded border border-slate-200">
                {item.report_id}
              </span>
              <span className="text-xs text-slate-400">•</span>
              <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                <Clock className="w-3 h-3 text-slate-400" />
                {item.timestamp}
              </span>
            </div>
            <h1 className="font-heading text-2xl sm:text-3xl text-slate-900 font-bold tracking-tight">
              {item.competency_name}
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1">
              {item.tier} • {item.difficulty_band}
            </p>
          </div>

          <div className="text-right sm:text-right shrink-0">
            <div className={cn(
              "font-heading text-4xl sm:text-5xl font-extrabold tabular-nums",
              passed ? "text-emerald-600" : "text-rose-600"
            )}>
              {item.score}%
            </div>
            <div className="text-xs font-semibold uppercase tracking-wider mt-0.5">
              {passed ? (
                <span className="text-emerald-700">Passed ({item.correct_count}/{item.total_questions} Correct)</span>
              ) : (
                <span className="text-rose-700">Retry Recommended ({item.correct_count}/{item.total_questions} Correct)</span>
              )}
            </div>
          </div>
        </div>

        {/* SECTION I: OFFICER PROFILE */}
        <div className="mb-8">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Section I: Officer Profile & Administrative Details
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 bg-slate-50/80 p-4 rounded-xl border border-slate-200 text-xs">
            <div>
              <span className="text-slate-400 block mb-0.5">Officer Name:</span>
              <span className="font-semibold text-slate-800">{item.full_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Official Email:</span>
              <span className="font-medium text-slate-800">{item.email}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Cadre / Role:</span>
              <span className="font-medium text-slate-800">{item.role_name}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Designation:</span>
              <span className="font-medium text-slate-800">{item.designation}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Department / Unit:</span>
              <span className="font-medium text-slate-800">{item.department}</span>
            </div>
            <div>
              <span className="text-slate-400 block mb-0.5">Session ID:</span>
              <span className="font-mono text-slate-700">{item.session_id}</span>
            </div>
          </div>
        </div>

        {/* SECTION II: EXECUTIVE PERFORMANCE & KPI SUMMARY */}
        <div className="mb-8">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Section II: Executive Performance & KPI Summary
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Score</span>
              <span className="font-heading text-lg font-bold text-slate-900">{item.score}%</span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Mastery Index</span>
              <span className="font-heading text-lg font-bold text-teal-600">
                {item.mastery !== null ? `${(item.mastery * 100).toFixed(0)}%` : "N/A"}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Confidence</span>
              <span className="font-heading text-lg font-bold text-blue-600">
                {(item.confidence * 100).toFixed(0)}%
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Coverage</span>
              <span className="font-heading text-lg font-bold text-indigo-600">
                {(item.coverage * 100).toFixed(0)}%
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Uncertainty</span>
              <span className="font-heading text-lg font-bold text-slate-700">
                {(item.uncertainty ?? 0.15).toFixed(2)}
              </span>
            </div>
            <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
              <span className="text-[11px] text-slate-400 block">Assessed</span>
              <span className="font-heading text-lg font-bold text-slate-900">{item.assessed_count}</span>
            </div>
          </div>
        </div>

        {/* SECTION III: AUDIT TRAIL, PROVENANCE & RELIABILITY */}
        <div className="mb-8">
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Section III: Audit Trail, Provenance & Reliability
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200">
            <div>
              <span className="text-slate-400 block">Evidence Type:</span>
              <span className="font-mono text-slate-800 font-semibold">{item.evidence_type}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Reliability Status:</span>
              <span className="font-mono text-emerald-700 font-semibold">{item.reliability_status}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Content Provenance:</span>
              <span className="font-mono text-slate-800">{item.provenance}</span>
            </div>
            <div>
              <span className="text-slate-400 block">Cognitive Weight:</span>
              <span className="font-mono text-slate-800">{item.weight.toFixed(1)}</span>
            </div>
          </div>
        </div>

        {/* SECTION IV: DIAGNOSTIC QUESTION-BY-QUESTION ANALYSIS */}
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-3">
            Section IV: Diagnostic Question-By-Question Analysis (15 Items)
          </h3>
          <div className="space-y-3">
            {(item.items || []).map((q, idx) => (
              <div
                key={idx}
                className={cn(
                  "p-4 rounded-xl border transition",
                  q.is_correct
                    ? "bg-white border-slate-200"
                    : "bg-rose-50/40 border-rose-200"
                )}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200">
                        {q.question_number || `Q${idx + 1}`}
                      </span>
                      <span className="text-xs font-semibold text-slate-600">
                        {q.subskill_name}
                      </span>
                    </div>
                    <p className="text-xs sm:text-sm font-medium text-slate-900 pt-1">
                      {q.question_text}
                    </p>
                  </div>

                  <div className="shrink-0 text-right">
                    {q.is_correct ? (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                        Correct
                      </span>
                    ) : (
                      <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                        <AlertCircle className="w-3 h-3 text-rose-600" />
                        Incorrect
                      </span>
                    )}
                    <div className="text-[11px] text-slate-500 font-mono mt-1">
                      Selected: <strong className="text-slate-800">{q.user_selected}</strong> | Key: <strong className="text-emerald-700">{q.correct_option}</strong>
                    </div>
                  </div>
                </div>

                {!q.is_correct && (
                  <div className="mt-3 pt-3 border-t border-rose-200/60 text-xs space-y-1.5">
                    {q.misconception_hint && (
                      <div className="flex items-start gap-1.5 text-rose-800">
                        <HelpCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-600" />
                        <div>
                          <strong className="font-semibold">Identified Misconception:</strong> {q.misconception_hint}
                        </div>
                      </div>
                    )}
                    {q.remediation_steps && (
                      <div className="flex items-start gap-1.5 text-slate-700">
                        <Lightbulb className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                        <div>
                          <strong className="font-semibold">Remediation:</strong> {q.remediation_steps}
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* SECTION V: INTERACTIVE AI DIAGNOSTIC COACH & REMEDIATION ASSISTANT */}
        <div className="mt-8 pt-8 border-t border-slate-200">
          <div className="bg-gradient-to-br from-indigo-50/90 via-blue-50/50 to-slate-50 border border-indigo-100 rounded-2xl p-6 sm:p-7 relative overflow-hidden shadow-xs">
            {/* Ambient background glow */}
            <div className="absolute -top-12 -right-12 w-44 h-44 bg-blue-400/10 rounded-full blur-2xl pointer-events-none" />

            <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 mb-4">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-blue-600 flex items-center justify-center text-white shadow-sm shrink-0">
                  <Bot className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-indigo-700">
                      Section V: AI Performance & Remediation Coach
                    </span>
                    <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      Live Chatbot
                    </span>
                  </div>
                  <h3 className="font-heading text-lg sm:text-xl font-bold text-slate-900 mt-0.5">
                    Interactive Cadre Advisory & Remediation Chatbot
                  </h3>
                </div>
              </div>

              {/* Exact OmniDimension Web Widget Trigger Button */}
              <button
                id="omni-open-widget-btn"
                className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold text-white bg-gradient-to-r from-indigo-600 via-blue-600 to-indigo-700 hover:from-indigo-700 hover:to-blue-700 transition shadow-md hover:shadow-lg active:scale-95 transform shrink-0"
              >
                <MessageSquare className="w-4 h-4" />
                <span>Open Widget</span>
              </button>
            </div>

            <p className="text-xs text-slate-600 leading-relaxed max-w-3xl mb-4">
              Discuss this evaluation report directly with GyanSetu&apos;s grounded AI assistant. Ask questions regarding 
              identified misconceptions, request formula step-by-step derivations, or get tailored guidance on practical 
              workplace exercises to boost your competency mastery index ({item.score}%).
            </p>

            {/* Suggested inquiries */}
            <div className="space-y-1.5">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-slate-500 block">
                Suggested Inquiries for This Evaluation Report:
              </span>
              <div className="flex flex-wrap gap-2">
                {[
                  "Why did I miss questions on this evaluation?",
                  "What practical tasks should I take to improve?",
                  "Explain Neyman Allocation and sampling variance in survey design",
                  `How can I raise my confidence from ${Math.round(item.confidence * 100)}% to 85%?`,
                ].map((promptText, pIdx) => (
                  <button
                    key={pIdx}
                    onClick={() => {
                      const btn = document.getElementById("omni-open-widget-btn");
                      if (btn) btn.click();
                    }}
                    className="text-xs bg-white/95 hover:bg-white text-slate-700 hover:text-indigo-700 border border-indigo-100 hover:border-indigo-300 px-3 py-1.5 rounded-lg shadow-xs transition text-left"
                  >
                    💬 &ldquo;{promptText}&rdquo;
                  </button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* OmniDimension Web Widget Script */}
        <Script
          id="omnidimension-web-widget"
          src="https://omnidim.io/web_widget.js?secret_key=2d39775642b445f9974532e7e04acd6e"
          strategy="afterInteractive"
        />
      </div>
    </div>
  );
}
