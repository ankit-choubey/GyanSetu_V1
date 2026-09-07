"use client";

import React, { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import { motion } from "framer-motion";
import { ShieldAlert, CheckCircle2, Lock, ArrowRight, Loader2, PlayCircle } from "lucide-react";
import { cn } from "@/lib/cn";
import { AssessmentRunner } from "@/components/assessments/AssessmentRunner";
import { StatusChip } from "@/components/ui/dashboard/primitives";

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

export default function AssessmentsPage() {
  const searchParams = useSearchParams();
  const sessionId = searchParams?.get("session_id") || "demo_session";

  const [tiers, setTiers] = useState<TierStatus[]>(initialTiers);
  const [activeTier, setActiveTier] = useState<"easy" | "medium" | "tough" | null>(null);

  // In a real app, fetch tiers status from GET /api/v1/assessment/tiers
  useEffect(() => {
    // We are using the mock data above for now.
  }, [sessionId]);

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
        return newTiers;
      });
    }
    setActiveTier(null);
  };

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
      <motion.div variants={itemVariants} className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="font-heading text-xl sm:text-2xl text-slate-900 tracking-normal mb-0.5">
            Assessment
          </h2>
          <p className="text-xs text-slate-500 font-sans">
            Three levels, unlocked in order
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs text-slate-500 font-sans">
          <span>Session:</span>
          <span className="font-mono text-xs bg-slate-100 px-2 py-0.5 rounded text-slate-700 border border-slate-200 font-medium">
            {sessionId}
          </span>
        </div>
      </motion.div>

      <motion.div variants={itemVariants} className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {tiers.map((tier) => (
          <div 
            key={tier.id}
            className={cn(
              "relative border rounded-xl overflow-hidden flex flex-col h-full transition-all duration-300",
              !tier.unlocked 
                ? "bg-slate-50 border-slate-200 opacity-60" 
                : "bg-white border-slate-200 shadow-sm hover:shadow-md hover:border-blue-300"
            )}
          >
            {/* Top color strip (thin 2px rule, semantic status only) */}
            <div className={cn(
              "h-0.5 w-full",
              tier.id === "easy" ? "bg-teal-500" :
              tier.id === "medium" ? "bg-amber-500" : "bg-rose-500"
            )} />

            <div className="p-6 flex-1 flex flex-col">
              <div className="flex items-start justify-between mb-4">
                <StatusChip
                  status={tier.id === "easy" ? "high" : tier.id === "medium" ? "med" : "low"}
                  size="sm"
                >
                  {tier.name}
                </StatusChip>
                {!tier.unlocked && <Lock className="w-4 h-4 text-slate-400" />}
                {tier.completed && <CheckCircle2 className="w-4 h-4 text-teal-600" />}
              </div>

              <h3 className="font-heading text-lg text-slate-900 mb-2">{tier.difficultyText}</h3>
              <p className="text-xs text-slate-600 flex-1 leading-relaxed font-sans">{tier.description}</p>

              {tier.completed && tier.score !== null && (
                <div className="mt-4 py-2 border-t border-slate-100 font-sans">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-slate-500 font-medium">Score:</span>
                    <span className={cn(
                      "font-bold tabular-nums",
                      tier.score >= tier.passing_score ? "text-teal-600" : "text-rose-600"
                    )}>
                      {tier.score}% {tier.score >= tier.passing_score ? "(Passed)" : "(Needs review)"}
                    </span>
                  </div>
                </div>
              )}
            </div>

            <div className="p-4 border-t border-slate-100 bg-slate-50/50">
              {tier.unlocked ? (
                <button
                  onClick={() => handleStartTier(tier.id)}
                  className={cn(
                    "w-full py-2.5 px-4 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition shadow-sm",
                    tier.completed 
                      ? "bg-white border border-slate-200 text-slate-700 hover:bg-slate-50" 
                      : "bg-blue-600 text-white hover:bg-blue-700 hover:shadow-md"
                  )}
                >
                  {tier.completed ? "Retake Assessment" : "Start Assessment"}
                  <PlayCircle className="w-4 h-4" />
                </button>
              ) : (
                <div className="w-full py-2.5 px-4 rounded-lg bg-slate-100 text-slate-400 text-xs font-medium text-center flex items-center justify-center gap-2 cursor-not-allowed" title={tier.unlock_requirement}>
                  <Lock className="w-3.5 h-3.5" />
                  Locked
                </div>
              )}
            </div>
          </div>
        ))}
      </motion.div>
    </motion.div>
  );
}
