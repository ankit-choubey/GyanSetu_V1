"use client";

import React, { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Target,
  Search,
  Lightbulb,
  Wrench,
  CheckCircle2,
  X,
  Check,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const LOOP_NODES = [
  { id: 1, label: "Assess", icon: Target, desc: "Diagnostic Baseline" },
  { id: 2, label: "Find Gap", icon: Search, desc: "Subskill Isolation" },
  { id: 3, label: "Recommend", icon: Lightbulb, desc: "Explainable Action" },
  { id: 4, label: "Intervene", icon: Wrench, desc: "Targeted Training" },
  { id: 5, label: "Verify", icon: CheckCircle2, desc: "Evidence Fusion" },
];

export function SolutionSection() {
  const [activeNodeIndex, setActiveNodeIndex] = useState(0);
  const shouldReduceMotion = useReducedMotion();

  // Sequential active node cycle per §2.3 & §3.4
  useEffect(() => {
    if (shouldReduceMotion) return;
    const interval = setInterval(() => {
      setActiveNodeIndex((prev) => (prev + 1) % LOOP_NODES.length);
    }, 1800);
    return () => clearInterval(interval);
  }, [shouldReduceMotion]);

  return (
    <section
      id="solution"
      className="relative py-24 md:py-32 px-6 bg-white overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="03" text="THE SOLUTION" />
        <SectionHeading
          title="THE EVIDENCE-DRIVEN CLOSED LOOP"
          subtitle="Not another LMS. A continuous cycle that identifies, fixes, and verifies competency — forever."
        />

        {/* ========================================================================= */}
        {/* DESKTOP CLOSED-LOOP DIAGRAM (lg: >= 1024px) */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative max-w-5xl mx-auto my-12 pt-4 pb-20">
          {/* Loop-Back SVG Path underneath nodes (z-index: 1 per §2.7 & §3.4) */}
          <svg
            className="absolute inset-x-0 top-12 w-full h-[180px] pointer-events-none z-1"
            viewBox="0 0 1000 180"
            fill="none"
          >
            <defs>
              <marker
                id="loopArrow"
                markerWidth="8"
                markerHeight="8"
                refX="4"
                refY="4"
                orient="auto"
              >
                <polygon points="0 0, 8 4, 0 8" fill="#3B82F6" />
              </marker>
            </defs>
            {/* Smooth rounded curve from node 5 (x=900) back to node 1 (x=100) */}
            <path
              d="M 900 40 C 900 150, 650 160, 500 160 C 350 160, 100 150, 100 40"
              stroke="#3B82F6"
              strokeWidth="2"
              strokeDasharray="6 4"
              className="animate-dash-flow"
              markerEnd="url(#loopArrow)"
            />
          </svg>

          {/* 5 Nodes Row with Connecting Lines */}
          <div className="relative z-10 flex items-center justify-between">
            {LOOP_NODES.map((node, index) => {
              const Icon = node.icon;
              const isActive = activeNodeIndex === index;

              return (
                <React.Fragment key={node.id}>
                  {/* Node Card */}
                  <motion.div
                    initial={
                      shouldReduceMotion ? false : { y: 30, opacity: 0 }
                    }
                    whileInView={
                      shouldReduceMotion ? {} : { y: 0, opacity: 1 }
                    }
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{ duration: 0.45, delay: index * 0.12 }}
                    className={`relative flex flex-col items-center justify-center w-28 h-28 rounded-2xl border transition-all duration-300 ${
                      isActive
                        ? "bg-[#EFF6FF] border-[#3B82F6] shadow-[0_0_24px_rgba(59,130,246,0.22)] scale-105"
                        : "bg-white border-[#E2E8F0] shadow-sm hover:border-[#CBD5E1]"
                    }`}
                  >
                    <div
                      className={`p-2 rounded-xl mb-1.5 transition-colors ${
                        isActive
                          ? "bg-[#3B82F6] text-white"
                          : "bg-[#F1F5F9] text-[#475569]"
                      }`}
                    >
                      <Icon className="w-6 h-6" />
                    </div>
                    <span className="font-body text-xs font-bold text-[#0F172A]">
                      {node.label}
                    </span>
                    <span className="font-body text-[10px] text-[#64748B]">
                      {node.desc}
                    </span>

                    {/* Active Step Indicator Pill */}
                    {isActive && (
                      <span className="absolute -top-3 px-2 py-0.5 rounded-full bg-[#3B82F6] text-white font-mono text-[9px] font-bold uppercase tracking-wider shadow-sm">
                        Step 0{node.id}
                      </span>
                    )}
                  </motion.div>

                  {/* Connecting Flow Arrow between nodes */}
                  {index < LOOP_NODES.length - 1 && (
                    <div className="flex-1 flex items-center justify-center px-2">
                      <svg className="w-full h-4" viewBox="0 0 100 16">
                        <line
                          x1="0"
                          y1="8"
                          x2="100"
                          y2="8"
                          stroke="#CBD5E1"
                          strokeWidth="2"
                          strokeDasharray="6 4"
                          className="animate-dash-flow"
                        />
                      </svg>
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* MOBILE & TABLET FALLBACK (< 1024px) — Vertical Step Column */}
        {/* ========================================================================= */}
        <div className="lg:hidden flex flex-col items-center my-10 max-w-sm mx-auto">
          {LOOP_NODES.map((node, index) => {
            const Icon = node.icon;
            const isActive = activeNodeIndex === index;

            return (
              <React.Fragment key={node.id}>
                <div
                  className={`w-full flex items-center gap-4 p-4 rounded-xl border transition-all duration-300 ${
                    isActive
                      ? "bg-[#EFF6FF] border-[#3B82F6] shadow-md"
                      : "bg-white border-[#E2E8F0]"
                  }`}
                >
                  <div
                    className={`p-2.5 rounded-lg ${
                      isActive
                        ? "bg-[#3B82F6] text-white"
                        : "bg-[#F1F5F9] text-[#475569]"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="text-left">
                    <span className="font-mono text-[10px] text-[#3B82F6] font-semibold uppercase">
                      Step 0{node.id}
                    </span>
                    <h4 className="font-body text-sm font-bold text-[#0F172A]">
                      {node.label}
                    </h4>
                    <p className="font-body text-xs text-[#64748B]">
                      {node.desc}
                    </p>
                  </div>
                </div>

                {index < LOOP_NODES.length - 1 && (
                  <div className="h-6 w-0.5 border-l-2 border-dashed border-[#CBD5E1] my-1" />
                )}
              </React.Fragment>
            );
          })}
          <div className="mt-4 inline-flex items-center gap-1.5 text-xs font-mono font-medium text-[#3B82F6] bg-[#EFF6FF] px-3 py-1 rounded-full">
            <span>↺ Loop closes and cycles continuously</span>
          </div>
        </div>

        {/* ========================================================================= */}
        {/* COMPARISON CARDS (Regular LMS vs GyanSetu) */}
        {/* ========================================================================= */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl mx-auto mt-8 text-left">
          {/* Left Card: Regular LMS */}
          <motion.div
            initial={shouldReduceMotion ? false : { x: -40, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { x: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="bg-white border border-[#E2E8F0] rounded-2xl p-6 md:p-8 shadow-sm"
          >
            <span className="font-mono text-xs uppercase font-bold text-[#94A3B8] tracking-wider">
              TRADITIONAL TRAINING
            </span>
            <h3 className="font-heading text-2xl md:text-3xl text-[#0F172A] mt-1 mb-4">
              REGULAR LMS
            </h3>

            <p className="font-body text-sm text-[#64748B] italic mb-6 border-l-2 border-[#CBD5E1] pl-3">
              &quot;You completed 14 video courses. 100% finished. Certificate
              awarded.&quot;
            </p>

            <ul className="space-y-3 font-body text-sm text-[#475569]">
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#FFF1F2] text-[#FB7185] shrink-0 mt-0.5">
                  <X className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>No subskill gap diagnosis</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#FFF1F2] text-[#FB7185] shrink-0 mt-0.5">
                  <X className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>No multi-source evidence fusion</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#FFF1F2] text-[#FB7185] shrink-0 mt-0.5">
                  <X className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>Zero post-training retention verification</span>
              </li>
            </ul>
          </motion.div>

          {/* Right Card: GyanSetu */}
          <motion.div
            initial={shouldReduceMotion ? false : { x: 40, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { x: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
            className="bg-[#EFF6FF] border-2 border-[#3B82F6] rounded-2xl p-6 md:p-8 shadow-[0_4px_20px_rgba(59,130,246,0.12)]"
          >
            <span className="font-mono text-xs uppercase font-bold text-[#3B82F6] tracking-wider">
              CLOSED LOOP INTELLIGENCE
            </span>
            <h3 className="font-heading text-2xl md:text-3xl text-[#0F172A] mt-1 mb-4">
              GYANSETU
            </h3>

            <p className="font-body text-sm text-[#1E3A5F] font-medium mb-6 border-l-2 border-[#3B82F6] pl-3">
              &quot;Role: JSO. Mastery in Sampling Design is 0.52. Gap: Variance
              Estimation. Next: NSSTA Practical Task.&quot;
            </p>

            <ul className="space-y-3 font-body text-sm text-[#0F172A]">
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#F0FDFA] text-[#0D9488] shrink-0 mt-0.5">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>Subskill precision down to exact statistical gaps</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#F0FDFA] text-[#0D9488] shrink-0 mt-0.5">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>6 distinct evidence types fused, not averaged</span>
              </li>
              <li className="flex items-start gap-2.5">
                <span className="p-0.5 rounded-full bg-[#F0FDFA] text-[#0D9488] shrink-0 mt-0.5">
                  <Check className="w-3.5 h-3.5 stroke-[3]" />
                </span>
                <span>Scheduled re-testing proves memory retention</span>
              </li>
            </ul>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
