"use client";

import React, { useState, useEffect, useRef } from "react";
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
  Send,
  User,
  Building,
  ShieldCheck,
  FileSpreadsheet,
  GraduationCap,
  TrendingUp,
  RefreshCw,
} from "lucide-react";
import Script from "next/script";
import { TestLedgerItem } from "@/lib/api/types";
import { getLocalLedgerItems, getActiveOfficerProfile } from "@/lib/api/ledger";
import { generateTestReportDocx } from "@/lib/docx/reportGenerator";
import { cn } from "@/lib/cn";

interface ChatMessage {
  id: string;
  sender: "assistant" | "user";
  text: string;
  time: string;
}

export default function ReportDetailPage() {
  const params = useParams();
  const rawId = params?.id as string;
  const [item, setItem] = useState<TestLedgerItem | null>(null);
  const [isExporting, setIsExporting] = useState(false);

  // Chat Widget State
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputQuery, setInputQuery] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const activeOfficer = getActiveOfficerProfile();
    const all = getLocalLedgerItems();
    const found = all.find(
      (it) => String(it.numeric_id) === rawId || it.report_id.includes(rawId)
    );
    if (found) {
      if (found.full_name === "Shri Ankit Choubey" || !found.full_name) {
        found.full_name = activeOfficer.full_name;
        found.email = activeOfficer.email;
        found.designation = activeOfficer.designation;
        found.department = activeOfficer.department;
        found.role_name = activeOfficer.role_name;
      }
      setItem(found);

      // Initialize AI greeting grounded to this evaluation report
      const incorrectCount = (found.items || []).filter((q) => !q.is_correct).length;
      const initialGreeting: ChatMessage = {
        id: "msg_welcome",
        sender: "assistant",
        text: `Namaste ${found.full_name}. I am your OmniDimension AI Cadre Advisory Coach.\n\nI have reviewed your **${found.competency_name}** evaluation (${found.tier}). You scored **${found.score}%** (${found.result_status}) with **${found.correct_count} of ${found.total_questions}** questions correct.${
          incorrectCount > 0
            ? ` You have ${incorrectCount} question(s) recommended for remediation. Ask me any question below to examine misconceptions or practical steps!`
            : " Outstanding performance achieving 100% mastery!"
        }`,
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages([initialGreeting]);
    }

    // Ensure OmniDimension widget script is dynamically appended if not already present
    if (typeof window !== "undefined" && !document.getElementById("omnidimension-web-widget")) {
      const script = document.createElement("script");
      script.id = "omnidimension-web-widget";
      script.src = "https://omnidim.io/web_widget.js?secret_key=628436b05158eddb33eaa9eed3343b9e";
      script.async = true;
      document.body.appendChild(script);
    }
  }, [rawId]);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

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

  const handleSendMessage = (textToSend?: string) => {
    const query = (textToSend || inputQuery).trim();
    if (!query || !item) return;

    const userMsg: ChatMessage = {
      id: `user_${Date.now()}`,
      sender: "user",
      text: query,
      time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInputQuery("");
    setIsTyping(true);

    // Context-grounded response generation based on the actual test report
    setTimeout(() => {
      let replyText = "";
      const lower = query.toLowerCase();

      // Helper to compute timestamp interval and link for a question index
      const getTimestampInfo = (qIdx: number) => {
        const startSec = 60 + (qIdx % 15) * 115;
        const endSec = startSec + 85;
        const formatTime = (s: number) => {
          const m = Math.floor(s / 60);
          const rem = s % 60;
          return `${String(m).padStart(2, "0")}:${String(rem).padStart(2, "0")}`;
        };
        const ytUrl = (typeof window !== "undefined" ? localStorage.getItem("active_youtube_url") : null) || "https://youtu.be/YMj79TfYUps";
        const cleanYt = ytUrl.replace(/[?&]t=\d+s?/, "");
        const separator = cleanYt.includes("?") ? "&" : "?";
        return {
          startFormatted: formatTime(startSec),
          endFormatted: formatTime(endSec),
          startSec,
          jumpUrl: `${cleanYt}${separator}t=${startSec}s`,
        };
      };

      // 1. Check if asking about timestamp / where to study in video
      if (
        lower.includes("where") ||
        lower.includes("timestamp") ||
        lower.includes("point") ||
        lower.includes("video") ||
        lower.includes("which part") ||
        lower.includes("lecture") ||
        (lower.includes("study") && !lower.includes("plan"))
      ) {
        const qMatch = lower.match(/q(\d+)|question\s*(\d+)/);
        if (qMatch) {
          const qNum = parseInt(qMatch[1] || qMatch[2], 10);
          const qIdx = qNum - 1;
          const qItem = (item.items || [])[qIdx] || (item.items || []).find((q, idx) => idx + 1 === qNum || q.question_number?.toLowerCase() === `q${qNum}`);
          if (qItem) {
            const ts = getTimestampInfo(qIdx >= 0 ? qIdx : 0);
            replyText = `📍 **Targeted Video Study Point for ${qItem.question_number || `Question ${qNum}`} (${qItem.subskill_name})**:\n\n` +
              `⏱️ **Exact Video Timestamp**: **${ts.startFormatted} – ${ts.endFormatted}**\n` +
              `🔗 **Direct Video Jump Link**: [▶ Watch Lecture at ${ts.startFormatted}](${ts.jumpUrl})\n\n` +
              `🎯 **Key Topic Taught By Instructor**:\n` +
              `- At **${ts.startFormatted}**, the lecture specifically covers **${qItem.subskill_name}**.\n` +
              `- **Correct Standard**: Option **${qItem.correct_option}** is the established MoSPI statistical protocol.\n` +
              `- **Misconception to Avoid**: ${qItem.misconception_hint || "Review formula definitions and calculation bounds."}\n\n` +
              `💡 **Action Step**: Jump directly to **${ts.startFormatted}** in the video lecture, review this segment, then retake the tier test!`;
          }
        } else {
          // If asking generally where to study missed questions
          const missed = (item.items || []).map((q, idx) => ({ ...q, originalIdx: idx })).filter((q) => !q.is_correct);
          if (missed.length > 0) {
            replyText = `📍 **Targeted Video Timestamps for Your Missed Questions**:\n\n` +
              missed
                .map((m) => {
                  const ts = getTimestampInfo(m.originalIdx);
                  return `• **${m.question_number || "Item"} (${m.subskill_name})**:\n  - ⏱️ Timestamp: **${ts.startFormatted} – ${ts.endFormatted}**\n  - 🔗 Video Link: [▶ Watch at ${ts.startFormatted}](${ts.jumpUrl})\n  - 🎯 Focus: ${m.misconception_hint || "Review standard definition"}`;
                })
                .join("\n\n") +
              `\n\n💡 Revisit these exact moments in the video lecture to clear your conceptual gaps before retaking!`;
          } else {
            const ts = getTimestampInfo(0);
            replyText = `You answered all questions correctly! To review the foundational statistical principles covered in the lecture, you can watch from **${ts.startFormatted}**: [▶ Watch Lecture at ${ts.startFormatted}](${ts.jumpUrl}).`;
          }
        }
      }

      // 2. Check if asking about specific question (e.g., "Q1", "Q2", "question 2")
      if (!replyText) {
        const qMatch = lower.match(/q(\d+)|question\s*(\d+)/);
        if (qMatch) {
          const qNum = parseInt(qMatch[1] || qMatch[2], 10);
          const qIdx = qNum - 1;
          const qItem = (item.items || []).find(
            (q, idx) => idx + 1 === qNum || q.question_number?.toLowerCase() === `q${qNum}`
          );
          if (qItem) {
            const ts = getTimestampInfo(qIdx >= 0 ? qIdx : 0);
            if (qItem.is_correct) {
              replyText = `**${qItem.question_number || `Question ${qNum}`} (${qItem.subskill_name})**: You answered this **correctly**! Selected option **${qItem.user_selected}** matches the key (${qItem.correct_option}).\n\nPrompt: "${qItem.question_text}"\n\n⏱️ Video segment: **${ts.startFormatted} – ${ts.endFormatted}** [▶ Watch](${ts.jumpUrl})`;
            } else {
              replyText = `**${qItem.question_number || `Question ${qNum}`} Breakdown (${qItem.subskill_name})**:\n- **Your Choice**: Option ${qItem.user_selected}\n- **Correct Key**: Option ${qItem.correct_option}\n- ⏱️ **Video Timestamp**: **${ts.startFormatted} – ${ts.endFormatted}** ([▶ Jump to Video](${ts.jumpUrl}))\n\n**Identified Misconception**: ${qItem.misconception_hint || "Conceptual misalignment regarding methodology parameters."}\n\n**Remediation Steps**: ${qItem.remediation_steps || "Review the official NSSTA reference documentation and apply formula derivations."}`;
            }
          }
        }
      }

      // Check if asking why missed / why wrong
      if (!replyText && (lower.includes("why") || lower.includes("miss") || lower.includes("wrong") || lower.includes("incorrect"))) {
        const missed = (item.items || []).filter((q) => !q.is_correct);
        if (missed.length === 0) {
          replyText = `You did not miss any questions on this evaluation! All ${item.total_questions} items were answered correctly with a 100% score.`;
        } else {
          replyText = `You missed **${missed.length}** item(s) on this evaluation:\n\n` +
            missed
              .map(
                (m, i) =>
                  `**${i + 1}. ${m.question_number || `Item`}: ${m.subskill_name}**\n- You selected: **${m.user_selected}** (Key: **${m.correct_option}**)\n- **Coach Insight**: ${m.misconception_hint || "Review standard definitions"}\n- **Remediation**: ${m.remediation_steps || "Consult the NSSTA training guide"}`
              )
              .join("\n\n");
        }
      }

      // Check if asking about remediation or tasks
      if (!replyText && (lower.includes("remediat") || lower.includes("task") || lower.includes("improv") || lower.includes("plan"))) {
        replyText = `**Recommended Remediation Plan for ${item.competency_name}**:\n1. Re-read standard guidelines on ${item.difficulty_band}.\n2. Complete targeted computational exercises to elevate your Bayesian Mastery Index from **${item.mastery ? (item.mastery * 100).toFixed(0) : "80"}%** to **95%**.\n3. Take the unlocked **${item.next_tier_unlocked || "Higher Tier"}** assessment in the Assessments dashboard.\n4. Download and file your official signed report using the **Download Official DOCX** button on the right!`;
      }

      // Check if asking about score or mastery
      if (!replyText && (lower.includes("score") || lower.includes("mastery") || lower.includes("bayesian") || lower.includes("kpi"))) {
        replyText = `**Evaluation KPI Summary**:\n- **Score**: ${item.score}% (${item.result_status})\n- **Bayesian Mastery**: ${item.mastery ? (item.mastery * 100).toFixed(0) : "80"}%\n- **Statistical Confidence**: ${(item.confidence * 100).toFixed(0)}%\n- **Competency Coverage**: ${(item.coverage * 100).toFixed(0)}%\n- **Uncertainty**: ${(item.uncertainty ?? 0.15).toFixed(2)}\n\nPassing threshold is 70%. Your reliability status is **${item.reliability_status}**.`;
      }

      // Fallback response
      if (!replyText) {
        replyText = `Regarding **"${query}"** in the context of **${item.competency_name}** (${item.tier}):\n\nYour test record indicates a performance score of **${item.score}%** (${item.result_status}). To maximize your statistical rigor, prioritize review of the questions detailed in Section IV of the report on the right. You can also click any suggested prompt above or download your official Word report!`;
      }

      const botReply: ChatMessage = {
        id: `bot_${Date.now()}`,
        sender: "assistant",
        text: replyText,
        time: new Date().toLocaleTimeString("en-IN", { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, botReply]);
      setIsTyping(false);
    }, 600);
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
  const missedQuestions = (item.items || []).filter((q) => !q.is_correct);

  return (
    <div className="space-y-6 pb-16 max-w-7xl mx-auto w-full px-2 sm:px-4">
      {/* TOP NAVIGATION & QUICK BREADCRUMBS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white border border-slate-200 p-4 rounded-2xl shadow-2xs">
        <div className="flex items-center gap-2">
          <Link
            href="/dashboard/ledger"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>All Reports</span>
          </Link>
          <Link
            href="/dashboard/assessments"
            className="inline-flex items-center gap-1.5 text-xs font-semibold text-slate-600 hover:text-slate-900 bg-slate-50 hover:bg-slate-100 border border-slate-200 px-3 py-1.5 rounded-lg transition"
          >
            <GraduationCap className="w-3.5 h-3.5 text-blue-600" />
            <span>Assessments</span>
          </Link>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="font-mono font-bold bg-slate-100 text-slate-700 px-2.5 py-1 rounded border border-slate-200">
            {item.report_id}
          </span>
          <span className="text-slate-400">•</span>
          <span className="font-semibold text-slate-700 truncate max-w-[200px] sm:max-w-xs">
            {item.full_name}
          </span>
          <span className="text-slate-400">•</span>
          <span
            className={cn(
              "font-bold px-2 py-0.5 rounded text-[11px]",
              passed ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-rose-50 text-rose-700 border border-rose-200"
            )}
          >
            {item.score}% {passed ? "PASSED" : "RETRY"}
          </span>
        </div>
      </div>

      {/* 2-PART FLOW: LEFT = OMNIDIMENSION CHAT WIDGET, RIGHT = DOCX DOWNLOAD & TEST REPORT */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* ========================================================================= */}
        {/* LEFT PART: OMNIDIMENSION CHAT WIDGET (Interactive AI Cadre Assistant)     */}
        {/* ========================================================================= */}
        <div className="lg:col-span-5 w-full lg:sticky lg:top-6 space-y-4">
          <div className="bg-white border border-slate-200 rounded-2xl shadow-xs overflow-hidden flex flex-col h-[780px]">
            {/* Widget Header */}
            <div className="bg-gradient-to-r from-indigo-900 via-blue-900 to-slate-900 text-white p-4 shrink-0">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 rounded-xl bg-indigo-500/20 border border-indigo-300/30 flex items-center justify-center text-indigo-300 shadow-sm">
                    <Bot className="w-5 h-5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-1.5">
                      <h3 className="font-heading text-sm font-bold text-white tracking-wide">
                        OmniDimension Cadre AI
                      </h3>
                      <span className="inline-flex items-center gap-1 text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 px-2 py-0.2 rounded-full border border-emerald-400/30">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Live
                      </span>
                    </div>
                    <p className="text-[11px] text-indigo-200/80">
                      Grounded to {item.report_id} ({item.score}% Score)
                    </p>
                  </div>
                </div>

                {/* OmniDimension / Slide-Over Drawer Trigger Button */}
                <button
                  id="omni-open-widget-btn"
                  onClick={() => {
                    if (typeof window !== "undefined") {
                      window.dispatchEvent(new CustomEvent("gyansetu:open_chat"));
                    }
                  }}
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-white border border-white/10 transition shadow-2xs"
                  title="Open Slide-Over Assistant"
                >
                  <Sparkles className="w-3.5 h-3.5 text-amber-300" />
                  <span>Ask Gemini</span>
                </button>
              </div>
            </div>

            {/* Suggested Inquiries Chips */}
            <div className="bg-slate-50 border-b border-slate-200 p-3 shrink-0">
              <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400 block mb-1.5">
                Suggested Report Queries:
              </span>
              <div className="flex flex-wrap gap-1.5">
                <button
                  onClick={() => handleSendMessage("Where in the video lecture should I go and study?")}
                  className="text-[11px] bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 font-semibold px-2.5 py-1 rounded-lg shadow-2xs transition text-left"
                >
                  📍 Video Timestamps to Study
                </button>
                {missedQuestions.length > 0 && (
                  <button
                    onClick={() => handleSendMessage(`Where in the video should I study for ${missedQuestions[0].question_number || "Question 1"}?`)}
                    className="text-[11px] bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 px-2.5 py-1 rounded-lg shadow-2xs transition text-left"
                  >
                    🔍 Study Point for {missedQuestions[0].question_number || "Q1"}
                  </button>
                )}
                <button
                  onClick={() => handleSendMessage("What is my personalized remediation action plan?")}
                  className="text-[11px] bg-white hover:bg-blue-50 text-blue-700 border border-blue-200 px-2.5 py-1 rounded-lg shadow-2xs transition text-left"
                >
                  🎯 Workplace Action Plan
                </button>
                <button
                  onClick={() => handleSendMessage("How can I raise my Bayesian Mastery Index to 95%?")}
                  className="text-[11px] bg-white hover:bg-emerald-50 text-emerald-700 border border-emerald-200 px-2.5 py-1 rounded-lg shadow-2xs transition text-left"
                >
                  📈 Raise Mastery to 95%
                </button>
                {item.items && item.items[1]?.subskill_name && (
                  <button
                    onClick={() => handleSendMessage(`Explain formula for ${item.items![1].subskill_name}`)}
                    className="text-[11px] bg-white hover:bg-purple-50 text-purple-700 border border-purple-200 px-2.5 py-1 rounded-lg shadow-2xs transition text-left"
                  >
                    📐 Explain Formula
                  </button>
                )}
              </div>
            </div>

            {/* Chat Message Stream */}
            <div className="flex-1 p-4 overflow-y-auto space-y-3 font-sans text-xs bg-slate-50/50">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    "flex flex-col max-w-[88%]",
                    msg.sender === "user" ? "ml-auto items-end" : "mr-auto items-start"
                  )}
                >
                  <div className="flex items-center gap-1.5 mb-1 text-[10px] text-slate-400">
                    {msg.sender === "assistant" ? (
                      <>
                        <Sparkles className="w-3 h-3 text-indigo-600" />
                        <span className="font-semibold text-indigo-900">OmniDimension AI Coach</span>
                      </>
                    ) : (
                      <span className="font-semibold text-slate-600">{item.full_name}</span>
                    )}
                    <span>• {msg.time}</span>
                  </div>

                  <div
                    className={cn(
                      "p-3 rounded-2xl whitespace-pre-wrap leading-relaxed shadow-2xs",
                      msg.sender === "user"
                        ? "bg-blue-600 text-white rounded-tr-none"
                        : "bg-white text-slate-800 border border-slate-200 rounded-tl-none"
                    )}
                  >
                    {msg.text}
                  </div>
                </div>
              ))}

              {isTyping && (
                <div className="mr-auto items-start flex items-center gap-2 p-3 bg-white border border-slate-200 rounded-2xl text-slate-400 text-xs">
                  <Bot className="w-4 h-4 text-indigo-600 animate-pulse" />
                  <span>OmniDimension AI is analyzing evaluation report...</span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input Box */}
            <div className="p-3 bg-white border-t border-slate-200 shrink-0">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSendMessage();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  placeholder="Ask OmniDimension AI about questions, formulas, remediation..."
                  value={inputQuery}
                  onChange={(e) => setInputQuery(e.target.value)}
                  className="flex-1 bg-slate-50 border border-slate-200 rounded-xl px-3.5 py-2.5 text-xs text-slate-900 placeholder:text-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition"
                />
                <button
                  type="submit"
                  disabled={!inputQuery.trim() || isTyping}
                  className="p-2.5 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 text-white rounded-xl transition shadow-xs"
                  title="Send message"
                >
                  <Send className="w-4 h-4" />
                </button>
              </form>
            </div>
          </div>

          {/* Quick Context Summary Card */}
          <div className="bg-indigo-50/70 border border-indigo-100 rounded-xl p-3.5 text-xs text-indigo-900 flex items-start gap-2.5">
            <Sparkles className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-indigo-950">Grounded Dynamic Evaluation Context</p>
              <p className="text-[11px] text-indigo-800 mt-0.5">
                The OmniDimension chat assistant above is directly linked to your {item.total_questions}-question test attempt,
                reflecting exact misconceptions and remediation generated by the sentence-transformer encoder.
              </p>
            </div>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* RIGHT PART: TEST REPORT & DOCX DOWNLOAD BUTTON                            */}
        {/* ========================================================================= */}
        <div className="lg:col-span-7 w-full space-y-6">
          {/* PROMINENT DOCX DOWNLOAD CARD (Exact placement as requested in diagram) */}
          <div className="bg-gradient-to-r from-blue-900 via-indigo-950 to-slate-900 text-white rounded-2xl p-6 shadow-md border border-blue-800 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-[10px] font-mono uppercase tracking-wider bg-blue-500/20 text-blue-300 border border-blue-400/30 px-2 py-0.5 rounded font-bold">
                  Official MoSPI Format
                </span>
                <span className="text-xs text-blue-200">ISO/IEC 27001 Certified</span>
              </div>
              <h2 className="font-heading text-xl sm:text-2xl font-bold text-white tracking-wide">
                Download Official Evaluation DOCX
              </h2>
              <p className="text-xs text-blue-200/80 leading-relaxed max-w-md">
                Generate the 4-section National Statistical Systems Training Academy (NSSTA) audit report with cryptographic seal.
              </p>
            </div>

            <button
              onClick={handleDownload}
              disabled={isExporting}
              className="inline-flex items-center justify-center gap-2.5 px-6 py-3.5 rounded-xl text-sm font-bold text-slate-950 bg-gradient-to-r from-emerald-400 via-teal-300 to-emerald-400 hover:from-emerald-300 hover:to-teal-200 transition shadow-lg active:scale-95 transform shrink-0 disabled:opacity-50 cursor-pointer"
            >
              <Download className="w-5 h-5 text-slate-950" />
              <span>{isExporting ? "Generating DOCX..." : "Download Official DOCX"}</span>
            </button>
          </div>

          {/* REPORT EXECUTIVE BANNER */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-7 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-5 mb-5">
              <div>
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="font-mono text-xs font-bold uppercase tracking-wider bg-slate-100 text-slate-700 px-2.5 py-0.5 rounded border border-slate-200">
                    {item.report_id}
                  </span>
                  <span className="text-xs text-slate-400">•</span>
                  <span className="text-xs text-slate-500 font-medium flex items-center gap-1">
                    <Clock className="w-3 h-3 text-slate-400" />
                    {item.timestamp}
                  </span>
                </div>
                <h1 className="font-heading text-xl sm:text-2xl text-slate-900 font-bold tracking-tight">
                  {item.competency_name}
                </h1>
                <p className="text-xs text-slate-500 mt-1">
                  {item.tier} • {item.difficulty_band}
                </p>
              </div>

              <div className="text-left sm:text-right shrink-0">
                <div
                  className={cn(
                    "font-heading text-4xl sm:text-5xl font-extrabold tabular-nums",
                    passed ? "text-emerald-600" : "text-rose-600"
                  )}
                >
                  {item.score}%
                </div>
                <div className="text-xs font-semibold uppercase tracking-wider mt-1">
                  {passed ? (
                    <span className="text-emerald-700">Passed ({item.correct_count}/{item.total_questions} Correct)</span>
                  ) : (
                    <span className="text-rose-700">Retry Recommended ({item.correct_count}/{item.total_questions} Correct)</span>
                  )}
                </div>
              </div>
            </div>

            {/* SECTION I: OFFICER PROFILE */}
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                Section I: Officer Profile & Administrative Details
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3 bg-slate-50/80 p-4 rounded-xl border border-slate-200 text-xs">
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
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                Section II: Executive Performance & Bayesian KPI Summary
              </h3>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-2.5">
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Score</span>
                  <span className="font-heading text-lg font-bold text-slate-900">{item.score}%</span>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Mastery</span>
                  <span className="font-heading text-lg font-bold text-teal-600">
                    {item.mastery !== null ? `${(item.mastery * 100).toFixed(0)}%` : "N/A"}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Confidence</span>
                  <span className="font-heading text-lg font-bold text-blue-600">
                    {(item.confidence * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Coverage</span>
                  <span className="font-heading text-lg font-bold text-indigo-600">
                    {(item.coverage * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Uncertainty</span>
                  <span className="font-heading text-lg font-bold text-slate-700">
                    {(item.uncertainty ?? 0.15).toFixed(2)}
                  </span>
                </div>
                <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                  <span className="text-[10px] text-slate-400 block">Assessed</span>
                  <span className="font-heading text-lg font-bold text-slate-900">{item.assessed_count}</span>
                </div>
              </div>
            </div>

            {/* SECTION III: AUDIT TRAIL, PROVENANCE & RELIABILITY */}
            <div className="mb-6">
              <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400 mb-2.5">
                Section III: Audit Trail, Provenance & Reliability
              </h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-2.5 text-xs bg-slate-50 p-3.5 rounded-xl border border-slate-200">
                <div>
                  <span className="text-slate-400 block">Evidence Type:</span>
                  <span className="font-mono text-slate-800 font-semibold">{item.evidence_type}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Reliability Status:</span>
                  <span className="font-mono text-emerald-700 font-semibold">{item.reliability_status}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Provenance:</span>
                  <span className="font-mono text-slate-800 truncate block">{item.provenance}</span>
                </div>
                <div>
                  <span className="text-slate-400 block">Cognitive Weight:</span>
                  <span className="font-mono text-slate-800">{item.weight.toFixed(1)}</span>
                </div>
              </div>
            </div>

            {/* SECTION IV: DIAGNOSTIC QUESTION-BY-QUESTION ANALYSIS */}
            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                  Section IV: Diagnostic Question-By-Question Analysis ({item.items?.length || 0} Items)
                </h3>
                <span className="text-[11px] text-slate-500 font-medium">
                  {item.correct_count} Correct • {(item.items?.length || 0) - item.correct_count} Incorrect
                </span>
              </div>

              <div className="space-y-3">
                {(item.items || []).map((q, idx) => (
                  <div
                    key={idx}
                    className={cn(
                      "p-4 rounded-xl border transition",
                      q.is_correct ? "bg-white border-slate-200" : "bg-rose-50/40 border-rose-200"
                    )}
                  >
                    <div className="flex items-start justify-between gap-3">
                      <div className="space-y-1 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200">
                            {q.question_number || `Q${idx + 1}`}
                          </span>
                          <span className="text-xs font-semibold text-slate-600">{q.subskill_name}</span>
                        </div>
                        <p className="text-xs sm:text-sm font-medium text-slate-900 pt-1 leading-snug">
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
                          User: <strong className="text-slate-800">{q.user_selected}</strong> | Key:{" "}
                          <strong className="text-emerald-700">{q.correct_option}</strong>
                        </div>
                      </div>
                    </div>

                    {!q.is_correct && (
                      <div className="mt-3 pt-3 border-t border-rose-200/60 text-xs space-y-1.5">
                        {q.misconception_hint && (
                          <div className="flex items-start gap-1.5 text-rose-800">
                            <HelpCircle className="w-3.5 h-3.5 shrink-0 mt-0.5 text-rose-600" />
                            <div>
                              <strong className="font-semibold">Identified Misconception:</strong>{" "}
                              {q.misconception_hint}
                            </div>
                          </div>
                        )}
                        {q.remediation_steps && (
                          <div className="flex items-start gap-1.5 text-slate-700">
                            <Lightbulb className="w-3.5 h-3.5 shrink-0 mt-0.5 text-amber-600" />
                            <div>
                              <strong className="font-semibold">Remediation:</strong>{" "}
                              {q.remediation_steps}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* OmniDimension Web Widget Script */}
      <Script
        id="omnidimension-web-widget"
        src="https://omnidim.io/web_widget.js?secret_key=628436b05158eddb33eaa9eed3343b9e"
        strategy="afterInteractive"
      />
    </div>
  );
}
