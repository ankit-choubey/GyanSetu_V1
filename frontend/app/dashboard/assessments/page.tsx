
"use client";

import React, { useEffect, useState, useCallback, useMemo } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldAlert, CheckCircle2, Lock, PlayCircle, FileSpreadsheet, ArrowRight } from "lucide-react";
import { cn } from "@/lib/cn";
import { AssessmentRunner } from "@/components/assessments/AssessmentRunner";
import { StatusChip } from "@/components/ui/dashboard/primitives";
import { getLocalLedgerItems } from "@/lib/api/ledger";

type TierStatus = {
  id: "easy" | "medium" | "tough";
  name: string;
  badgeColor: string;
  difficultyText: string;
  unlocked: boolean;
  completed: boolean;
  score: number | null;
  passing_score: number;
  description: string;
  unlock_requirement?: string;
};

// Mock Tiers
const initialTiers: TierStatus[] = [
  {
    id: "easy",
    name: "Tier 1: Foundation",
    badgeColor: "text-emerald-600 bg-emerald-50 border-emerald-200",
    difficultyText: "Easy • Recall & Definitions",
    unlocked: true,
    completed: false,
    score: null,
    passing_score: 70,
    description: "Core definitions, terminology, and foundational knowledge of the statistical concept."
  },
  {
    id: "medium",
    name: "Tier 2: Application",
    badgeColor: "text-amber-600 bg-amber-50 border-amber-200",
    difficultyText: "Medium • Formulas & Calculations",
    unlocked: false,
    completed: false,
    score: null,
    passing_score: 70,
    description: "Apply formulas and solve direct computational problems using real data sets.",
    unlock_requirement: "Complete Tier 1 with ≥ 70% to unlock."
  },
  {
    id: "tough",
    name: "Tier 3: Analysis",
    badgeColor: "text-purple-600 bg-purple-50 border-purple-200",
    difficultyText: "Hard • Multi-Step & Policy",
    unlocked: false,
    completed: false,
    score: null,
    passing_score: 70,
    description: "Complex multi-step problems requiring deep analytical reasoning and policy trade-offs.",
    unlock_requirement: "Complete Tier 2 with ≥ 70% to unlock."
  }
];

function getResolvedTiers(currentSessionId: string): TierStatus[] {
  let result: TierStatus[] = initialTiers.map(t => ({ ...t }));
  if (typeof window === "undefined") return result;

  try {
    const isExplicitSession = !!(
      currentSessionId && 
      currentSessionId !== "demo_session" && 
      currentSessionId !== "default"
    );
    const sessionKey = isExplicitSession ? `gyansetu_tiers_${currentSessionId}` : "gyansetu_tiers_default";
    const sessionData = localStorage.getItem(sessionKey);

    if (sessionData) {
      const parsed = JSON.parse(sessionData);
      if (Array.isArray(parsed) && parsed.length === 3) {
        result = parsed;
      }
    }

    // Only reconcile with ledger for the EXACT matching session!
    // Never apply unrelated historical ledger items to a fresh or new session.
    const ledgerItems = getLocalLedgerItems();
    if (Array.isArray(ledgerItems) && ledgerItems.length > 0) {
      const targetSession = isExplicitSession ? currentSessionId : "sess_mospi_base_001";
      const matchingItems = ledgerItems.filter(item => item.session_id === targetSession);

      matchingItems.forEach(item => {
        const itemTier = (item.tier || "").toLowerCase();
        const tierId = 
          itemTier.includes("tier 1") || itemTier.includes("foundation") ? "easy" :
          itemTier.includes("tier 2") || itemTier.includes("application") ? "medium" :
          itemTier.includes("tier 3") || itemTier.includes("analysis") ? "tough" : null;

        if (tierId) {
          const idx = result.findIndex(t => t.id === tierId);
          if (idx > -1) {
            if (!result[idx].completed || result[idx].score === null) {
              result[idx].completed = true;
              result[idx].score = typeof item.score === "number" ? item.score : 70;
            }
            if ((result[idx].score ?? 0) >= result[idx].passing_score && idx + 1 < result.length) {
              result[idx + 1].unlocked = true;
            }
          }
        }
      });
    }
  } catch (err) {
    console.warn("Failed resolving assessment tiers:", err);
  }

  return result;
}

export default function AssessmentsPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const rawSessionId = searchParams?.get("session_id");

  const [sessionId, setSessionId] = useState<string>(() => {
    if (rawSessionId && rawSessionId !== "demo_session") return rawSessionId;
    if (typeof window !== "undefined") {
      return localStorage.getItem("active_session_id") || "";
    }
    return "";
  });

  const [sourceTitle, setSourceTitle] = useState<string | null>(() => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("active_source_title") || null;
    }
    return null;
  });

  const [tiers, setTiers] = useState<TierStatus[]>(() => {
    const initialSession = rawSessionId && rawSessionId !== "demo_session" 
      ? rawSessionId 
      : (typeof window !== "undefined" ? localStorage.getItem("active_session_id") || "" : "");
    return getResolvedTiers(initialSession);
  });

  const [activeTier, setActiveTier] = useState<"easy" | "medium" | "tough" | null>(null);

  // Synchronize tiers and session context when URL param or storage changes
  const syncState = useCallback(() => {
    const effectiveSession = rawSessionId && rawSessionId !== "demo_session"
      ? rawSessionId
      : (typeof window !== "undefined" ? localStorage.getItem("active_session_id") || "" : "");

    setSessionId(effectiveSession);

    if (typeof window !== "undefined") {
      setSourceTitle(localStorage.getItem("active_source_title") || null);
    }

    const resolved = getResolvedTiers(effectiveSession);
    setTiers(resolved);
  }, [rawSessionId]);

  useEffect(() => {
    syncState();

    const handleUpdate = () => syncState();
    window.addEventListener("gyansetu:assessment_updated", handleUpdate);
    window.addEventListener("gyansetu:ledger_updated", handleUpdate);
    window.addEventListener("storage", handleUpdate);

    return () => {
      window.removeEventListener("gyansetu:assessment_updated", handleUpdate);
      window.removeEventListener("gyansetu:ledger_updated", handleUpdate);
      window.removeEventListener("storage", handleUpdate);
    };
  }, [syncState]);

  const handleStartTier = (tierId: "easy" | "medium" | "tough") => {
    setActiveTier(tierId);
  };

  const handleCloseRunner = (score?: number, passed?: boolean) => {
    if (activeTier && score !== undefined && passed !== undefined) {
      setTiers(prev => {
        const newTiers = [...prev];
        const currentIdx = newTiers.findIndex(t => t.id === activeTier);
        if (currentIdx > -1) {
          newTiers[currentIdx] = {
            ...newTiers[currentIdx],
            completed: true,
            score: score
          };
          
          // Unlock next tier if passed
          if (passed && currentIdx + 1 < newTiers.length) {
            newTiers[currentIdx + 1] = {
              ...newTiers[currentIdx + 1],
              unlocked: true
            };
          }
        }
        if (typeof window !== "undefined") {
          try {
            const isExplicitSession = !!(sessionId && sessionId !== "demo_session" && sessionId !== "default");
            const sessionKey = isExplicitSession ? `gyansetu_tiers_${sessionId}` : "gyansetu_tiers_default";
            localStorage.setItem(sessionKey, JSON.stringify(newTiers));
            if (!isExplicitSession) {
              localStorage.setItem("gyansetu_tiers_default", JSON.stringify(newTiers));
            }
            window.dispatchEvent(new Event("gyansetu:assessment_updated"));
          } catch (e) {
            console.warn("Failed saving tiers to localStorage:", e);
          }
        }
        return newTiers;
      });
    }
    setActiveTier(null);
  };

  const completedTiers = useMemo(() => tiers.filter(t => t.completed && t.score !== null), [tiers]);
  const hasGivenAssessment = completedTiers.length > 0;
  const latestCompletedTier = completedTiers.length > 0 ? completedTiers[completedTiers.length - 1] : null;
  const latestScore = latestCompletedTier?.score ?? null;
  const latestPassed = latestCompletedTier ? (latestCompletedTier.score ?? 0) >= latestCompletedTier.passing_score : false;

  const matchingReports = useMemo(() => {
    const items = getLocalLedgerItems();
    const map: Record<string, any> = {};
    if (Array.isArray(items)) {
      items.forEach(item => {
        if (!sessionId || item.session_id === sessionId) {
          const t = (item.tier || "").toLowerCase();
          const tierKey = t.includes("tier 1") || t.includes("foundation") ? "easy" :
                          t.includes("tier 2") || t.includes("application") ? "medium" :
                          t.includes("tier 3") || t.includes("analysis") ? "tough" : null;
          if (tierKey && !map[tierKey]) {
            map[tierKey] = item;
          }
        }
      });
    }
    return map;
  }, [sessionId, tiers]);

  const latestReport = useMemo(() => {
    const items = getLocalLedgerItems();
    if (!Array.isArray(items) || items.length === 0) return null;
    if (sessionId) {
      const match = items.find(it => it.session_id === sessionId);
      if (match) return match;
    }
    return items[0];
  }, [sessionId, tiers]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1, transition: { staggerChildren: 0.1 } }
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: { y: 0, opacity: 1, transition: { type: "spring", stiffness: 400, damping: 30 } }
  };

  if (activeTier) {
    return (
      <AssessmentRunner 
        sessionId={sessionId} 
        tier={activeTier} 
        onClose={handleCloseRunner} 
      />
    );
  }

  return (
    <motion.div 
      className="space-y-6 w-full"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      <motion.div variants={itemVariants} className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-wide mb-1">
            Assessment
          </h2>
          <p className="text-sm text-slate-600 font-sans">
            Three levels, unlocked in order
          </p>
        </div>
        {sourceTitle ? (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-50 rounded-lg text-xs text-blue-800 border border-blue-200 font-medium">
            <span className="w-2 h-2 rounded-full bg-blue-600 animate-pulse" />
            <span className="truncate max-w-xs sm:max-w-md font-semibold">Material: {sourceTitle}</span>
          </div>
        ) : sessionId ? (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-slate-100 rounded-lg text-xs text-slate-700 border border-slate-200 font-medium">
            <span className="w-2 h-2 rounded-full bg-blue-600" />
            <span>Material: {sessionId.replace("lib_", "Library Material #").replace("doc_", "Document #")}</span>
          </div>
        ) : (
          <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-50 rounded-lg text-xs text-emerald-800 border border-emerald-200 font-medium">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span>Official Diagnostic Cadre</span>
          </div>
        )}
      </motion.div>

      {/* REAL-TIME REVIEW PERCENTAGE & PERFORMANCE CONSISTENCY BANNER */}
      {hasGivenAssessment && latestScore !== null && (
        <motion.div
          variants={itemVariants}
          className={cn(
            "rounded-2xl border p-5 sm:p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4 font-sans transition-all",
            latestPassed 
              ? "bg-gradient-to-r from-teal-50/70 via-white to-emerald-50/40 border-teal-200" 
              : "bg-gradient-to-r from-rose-50/70 via-white to-amber-50/40 border-rose-200"
          )}
        >
          <div className="flex items-center gap-4">
            <div className={cn(
              "w-12 h-12 rounded-xl flex items-center justify-center shrink-0 border shadow-xs",
              latestPassed 
                ? "bg-teal-500 text-white border-teal-600" 
                : "bg-rose-500 text-white border-rose-600"
            )}>
              {latestPassed ? <CheckCircle2 className="w-6 h-6" /> : <ShieldAlert className="w-6 h-6" />}
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <span className="text-xs font-bold uppercase tracking-wider px-2.5 py-0.5 rounded border bg-white text-slate-800 border-slate-200">
                  Real-Time Assessment Review
                </span>
                <span className={cn(
                  "text-xs font-bold px-2.5 py-0.5 rounded border",
                  latestPassed ? "bg-teal-100/70 text-teal-800 border-teal-200" : "bg-rose-100/70 text-rose-800 border-rose-200"
                )}>
                  {latestPassed ? "Threshold Satisfied (Passed)" : "Remediation Advised (Needs Review)"}
                </span>
                <span className="text-[11px] text-slate-500 font-medium flex items-center gap-1 bg-white/80 px-2 py-0.5 rounded border border-slate-200">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Live Synced
                </span>
              </div>
              <p className="text-sm font-semibold text-slate-900 mt-1.5">
                {completedTiers.length} of 3 Tiers Completed • {latestCompletedTier?.name} ({latestCompletedTier?.difficultyText})
              </p>
              <p className="text-xs text-slate-600 mt-0.5">
                {latestPassed 
                  ? "Standard met (≥ 70% threshold). Evaluation record verified & next tier unlocked." 
                  : "Proficiency score is below 70%. Review coach insights & misconceptions before retaking."}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-4 self-stretch md:self-auto justify-between md:justify-end border-t md:border-t-0 pt-3 md:pt-0 border-slate-200/60 flex-wrap">
            <div className="text-right">
              <div className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">Review Percentage</div>
              <div className={cn(
                "font-heading text-4xl sm:text-5xl tabular-nums font-bold leading-none mt-0.5",
                latestPassed ? "text-teal-700" : "text-rose-600"
              )}>
                {latestScore}%
              </div>
              <div className="text-[11px] font-medium text-slate-500 mt-1">
                {latestPassed ? "Passed Standard" : "Needs Review"}
              </div>
            </div>

            <button
              onClick={() => {
                if (latestReport?.numeric_id) {
                  router.push(`/dashboard/ledger/${latestReport.numeric_id}`);
                } else {
                  router.push(`/dashboard/ledger?session_id=${sessionId}`);
                }
              }}
              className="px-4 py-2.5 rounded-xl bg-slate-900 hover:bg-slate-800 text-white text-xs font-semibold flex items-center gap-2 shadow-sm transition shrink-0"
            >
              <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
              <span>Report Ledger & DOCX</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </motion.div>
      )}

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {tiers.map((tier) => (
          <div 
            key={tier.id}
            className={cn(
              "relative border rounded-2xl overflow-hidden flex flex-col justify-between min-h-[300px] transition-all duration-300",
              !tier.unlocked 
                ? "bg-slate-50 border-slate-200 opacity-60" 
                : "bg-white border-slate-200 shadow-sm hover:shadow-md hover:border-blue-300"
            )}
          >
            {/* Top color strip */}
            <div className={cn(
              "h-1 w-full",
              tier.id === "easy" ? "bg-teal-500" :
              tier.id === "medium" ? "bg-amber-500" : "bg-rose-500"
            )} />

            <div className="p-6 flex-1 flex flex-col">
              <div className="flex items-start justify-between mb-4">
                <StatusChip
                  status={tier.id === "easy" ? "high" : tier.id === "medium" ? "med" : "low"}
                  size="md"
                >
                  {tier.name}
                </StatusChip>
                {!tier.unlocked && <Lock className="w-4 h-4 text-slate-400" />}
                {tier.completed && <CheckCircle2 className="w-5 h-5 text-teal-600" />}
              </div>

              <h3 className="font-heading text-xl sm:text-2xl text-slate-900 mb-2.5 tracking-wide">{tier.difficultyText}</h3>
              <p className="text-sm text-slate-600 flex-1 leading-relaxed font-sans mb-4">{tier.description}</p>

              {tier.completed && tier.score !== null && (
                <div className="mt-4 pt-3 border-t border-slate-100 font-sans">
                  <div className="flex justify-between items-center text-sm">
                    <span className="text-slate-500 font-medium">Review Score:</span>
                    <span className={cn(
                      "font-bold tabular-nums text-base",
                      tier.score >= tier.passing_score ? "text-teal-600" : "text-rose-600"
                    )}>
                      {tier.score}% {tier.score >= tier.passing_score ? "(Passed)" : "(Needs review)"}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="p-5 border-t border-slate-100 bg-slate-50/50">
              {tier.unlocked ? (
                <div className="space-y-2">
                  <button
                    onClick={() => handleStartTier(tier.id)}
                    className={cn(
                      "w-full py-2.5 px-4 rounded-xl text-sm font-bold flex items-center justify-center gap-2 transition shadow-xs",
                      tier.completed 
                        ? "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50" 
                        : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md"
                    )}
                  >
                    <span>{tier.completed ? "Retake Assessment" : "Start Assessment"}</span>
                    <PlayCircle className="w-4 h-4" />
                  </button>

                  {tier.completed ? (
                    <button
                      onClick={() => {
                        const targetReport = matchingReports[tier.id];
                        if (targetReport?.numeric_id) {
                          router.push(`/dashboard/ledger/${targetReport.numeric_id}`);
                        } else {
                          router.push(`/dashboard/ledger?session_id=${sessionId}`);
                        }
                      }}
                      className="w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition text-indigo-700 bg-indigo-50/90 hover:bg-indigo-100 border border-indigo-200 shadow-2xs"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5 text-indigo-600" />
                      <span>Redirect to Report Ledger (DOCX & Chat)</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  ) : (
                    <button
                      onClick={() => router.push("/dashboard/ledger")}
                      className="w-full py-2 px-3 rounded-xl text-xs font-semibold flex items-center justify-center gap-1.5 transition text-slate-600 bg-white hover:bg-slate-100 border border-slate-200"
                    >
                      <FileSpreadsheet className="w-3.5 h-3.5 text-slate-400" />
                      <span>View Report Ledger</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  )}
                </div>
              ) : (
                <div className="space-y-2">
                  <div className="w-full py-2.5 px-4 rounded-xl bg-slate-100 text-slate-400 text-xs font-semibold text-center flex items-center justify-center gap-2 cursor-not-allowed" title={tier.unlock_requirement}>
                    <Lock className="w-4 h-4" />
                    <span>Locked ({tier.unlock_requirement || "Complete previous tier"})</span>
                  </div>
                  <button
                    onClick={() => router.push("/dashboard/ledger")}
                    className="w-full py-1.5 px-3 rounded-xl text-[11px] font-semibold flex items-center justify-center gap-1.5 transition text-slate-500 bg-white hover:bg-slate-50 border border-slate-200"
                  >
                    <FileSpreadsheet className="w-3 h-3 text-slate-400" />
                    <span>Check Ledger Standards</span>
                    <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              )}
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
