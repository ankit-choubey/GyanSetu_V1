"use client";

import React, { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Sparkles,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  BookOpen,
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertCircle,
  HelpCircle,
  Flag,
} from "lucide-react";
import { NextBestAction } from "@/lib/api/types";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface NextBestActionCardProps {
  nba: NextBestAction;
  className?: string;
}

export function NextBestActionCard({ nba, className }: NextBestActionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isFlagged, setIsFlagged] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  // The 12 Explainability Fields mapped to structured pairs
  const explainabilityFields: Array<{
    id: string;
    number: string;
    label: string;
    value: string;
    icon?: React.ReactNode;
  }> = [
    {
      id: "action",
      number: "01",
      label: "Selected Action",
      value: nba.selected_action,
    },
    {
      id: "justification",
      number: "02",
      label: "Causal Justification",
      value: nba.justification,
    },
    {
      id: "role_relevance",
      number: "03",
      label: "Role Relevance (SSS/JSO)",
      value: nba.role_relevance,
    },
    {
      id: "competency_alignment",
      number: "04",
      label: "Competency Alignment",
      value: nba.competency_alignment,
    },
    {
      id: "subskill_coverage",
      number: "05",
      label: "Subskill Coverage",
      value: nba.subskill_coverage,
    },
    {
      id: "prerequisites",
      number: "06",
      label: "Prerequisites Verified",
      value: nba.prerequisites,
    },
    {
      id: "gap_severity",
      number: "07",
      label: "Gap Severity",
      value: `${nba.gap_severity} Priority Deficit`,
    },
    {
      id: "evidence_confidence",
      number: "08",
      label: "Evidence Confidence",
      value: `${nba.evidence_confidence} Calibration (Fused from multi-modal assessment)`,
    },
    {
      id: "learner_state",
      number: "09",
      label: "Learner Workload & State",
      value: nba.learner_state,
    },
    {
      id: "modality",
      number: "10",
      label: "Delivery Modality",
      value: nba.modality,
    },
    {
      id: "availability",
      number: "11",
      label: "Resource Availability",
      value: nba.availability,
    },
    {
      id: "expected_outcome",
      number: "12",
      label: "Measurable Expected Gain",
      value: nba.expected_outcome,
    },
  ];

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-blue-200/90 p-6 shadow-sm hover:shadow transition-all relative overflow-hidden",
        className
      )}
    >
      {/* Top Gradient Stripe */}
      <div className="absolute top-0 left-0 right-0 h-1.5 bg-gradient-to-r from-blue-600 via-indigo-600 to-teal-400" />

      {/* Header Row: Badge, Modality & Availability */}
      <div className="flex flex-wrap items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-mono font-medium bg-blue-50 text-blue-800 border border-blue-200">
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            NEXT-BEST-ACTION RECOMMENDATION
          </span>
          <span className="text-xs font-mono text-slate-400">
            [XAI 12-Facet Engine]
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono bg-indigo-50 text-indigo-700 border border-indigo-200">
            <BookOpen className="w-3 h-3" />
            {nba.modality}
          </span>
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono bg-teal-50 text-teal-700 border border-teal-200">
            <Clock className="w-3 h-3" />
            {nba.availability}
          </span>
        </div>
      </div>

      {/* Primary Recommended Action Title */}
      <div className="mb-4">
        <h3 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal leading-snug">
          {nba.selected_action}
        </h3>
        <p className="text-xs font-mono text-blue-600 mt-1">
          {nba.competency_alignment}
        </p>
      </div>

      {/* Core Visible Justification & Expected Outcome (Above Disclosure) */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-5 text-xs">
        <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
          <div className="font-mono text-[11px] text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
            Why This Action (Causal Justification)
          </div>
          <p className="text-slate-700 leading-relaxed">{nba.justification}</p>
        </div>

        <div className="bg-teal-50/40 p-4 rounded-lg border border-teal-100">
          <div className="font-mono text-[11px] text-teal-700 uppercase tracking-wider mb-1 flex items-center gap-1">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
            Projected Measurable Outcome
          </div>
          <p className="text-teal-950 leading-relaxed font-medium">
            {nba.expected_outcome}
          </p>
        </div>
      </div>

      {/* Expandable 12-Field Explainability Accordion */}
      <div className="border-t border-slate-100 pt-4">
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setIsExpanded(!isExpanded)}
            className="inline-flex items-center gap-2 text-xs font-mono font-medium text-blue-700 hover:text-blue-800 transition py-1"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="w-4 h-4" />
                <span>Hide 12-Point Explainability Audit Record</span>
              </>
            ) : (
              <>
                <ChevronDown className="w-4 h-4" />
                <span>Why this recommendation? (Inspect all 12 XAI facets)</span>
              </>
            )}
          </button>

          {/* Calibrated Trust Affordance (§3.2) */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => setIsFlagged(!isFlagged)}
              className={cn(
                "text-[11px] font-mono inline-flex items-center gap-1 transition px-2 py-1 rounded border",
                isFlagged
                  ? "bg-amber-100 text-amber-900 border-amber-300"
                  : "text-slate-500 hover:text-slate-700 border-transparent hover:border-slate-200"
              )}
              title="Calibrated Trust: You can challenge the AI's recommendation or request an alternative."
            >
              <Flag className="w-3 h-3" />
              <span>{isFlagged ? "Feedback Flagged to Supervisor" : "Not relevant? / Request Alternative"}</span>
            </button>

            <a
              href="https://igotkarmayogi.gov.in"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-blue-600 hover:bg-blue-700 text-white transition shadow-sm"
            >
              <span>Launch Module</span>
              <ExternalLink className="w-3.5 h-3.5" />
            </a>
          </div>
        </div>

        {/* 12-Field Audit Grid Content */}
        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={shouldReduceMotion ? false : { opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={shouldReduceMotion ? undefined : { opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden mt-4 pt-4 border-t border-slate-100"
            >
              <div className="bg-slate-50/80 rounded-lg p-5 border border-slate-200">
                <div className="flex items-center justify-between mb-3 border-b border-slate-200 pb-2">
                  <span className="font-mono text-xs font-semibold text-slate-800 uppercase tracking-wider">
                    Full Causal & Operational Audit Record (12 Facets)
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">
                    KCM / TPAC Algorithmic Policy v1.4
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-4">
                  {explainabilityFields.map((field) => (
                    <div
                      key={field.id}
                      className="border-b border-slate-200/60 pb-2 last:border-b-0"
                    >
                      <div className="flex items-center gap-1.5 font-mono text-[11px] text-slate-500 uppercase tracking-wide">
                        <span className="text-blue-600 font-bold">{field.number}.</span>
                        <span>{field.label}</span>
                      </div>
                      <p className="mt-1 text-xs text-slate-800 font-sans leading-relaxed">
                        {field.value}
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}
