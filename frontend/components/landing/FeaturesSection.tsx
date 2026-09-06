"use client";

import React from "react";
import { motion } from "framer-motion";
import { Brain, Layers, Target, Workflow, Clock } from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { Card } from "@/components/ui/Card";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function FeaturesSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="features"
      className="relative py-24 md:py-32 px-6 bg-white border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="07" text="DIFFERENTIATORS" />
        <SectionHeading
          title="WHAT MAKES GYANSETU DIFFERENT"
          subtitle="Built specifically for the rigorous statistical precision required by the Ministry of Statistics and Programme Implementation."
        />

        {/* Bento Grid (§3.8) */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 max-w-5xl mx-auto my-12 text-left">
          {/* Card 1: Adaptive Assessment */}
          <motion.div
            initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5 }}
          >
            <Card className="h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6] mb-4">
                  <Brain className="w-6 h-6" />
                </div>
                <h3 className="font-body font-bold text-xl text-[#0F172A] mb-2">
                  Adaptive Assessment
                </h3>
                <p className="font-body text-sm text-[#64748B] leading-relaxed mb-6">
                  Questions calibrate to officer proficiency in real-time.
                  Increases difficulty on correct answers, isolates weak
                  subskills on errors.
                </p>
              </div>

              {/* Mini Visual: Difficulty Slider */}
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
                <div className="flex justify-between text-[10px] font-mono text-[#64748B] mb-1.5">
                  <span>EASY</span>
                  <span className="text-[#3B82F6] font-bold">MEDIUM (ACTIVE)</span>
                  <span>HARD</span>
                </div>
                <div className="relative h-2 w-full bg-[#E2E8F0] rounded-full overflow-hidden">
                  <div className="h-full bg-[#3B82F6] w-3/5 rounded-full" />
                </div>
              </div>
            </Card>
          </motion.div>

          {/* Card 2: Evidence Fusion */}
          <motion.div
            initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.1 }}
          >
            <Card className="h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6] mb-4">
                  <Layers className="w-6 h-6" />
                </div>
                <h3 className="font-body font-bold text-xl text-[#0F172A] mb-2">
                  Evidence Fusion
                </h3>
                <p className="font-body text-sm text-[#64748B] leading-relaxed mb-6">
                  6 distinct evidence types fused, never averaged. Inconsistencies
                  between theoretical tests and practical work are flagged
                  transparently.
                </p>
              </div>

              {/* Mini Visual: Stacked Evidence Chips */}
              <div className="flex flex-wrap gap-1.5 p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl">
                <span className="px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] text-[10px] font-mono font-medium border border-[#DBEAFE]">
                  ● Diagnostic MCQ
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#F0FDFA] text-[#0D9488] text-[10px] font-mono font-medium border border-[#CCFBF1]">
                  ● NSSTA Task
                </span>
                <span className="px-2 py-0.5 rounded-full bg-[#FEF3C7] text-[#D97706] text-[10px] font-mono font-medium border border-[#FDE68A]">
                  ● Field Survey Audit
                </span>
              </div>
            </Card>
          </motion.div>

          {/* Card 3: Next Best Action */}
          <motion.div
            initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.2 }}
          >
            <Card className="h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6] mb-4">
                  <Target className="w-6 h-6" />
                </div>
                <h3 className="font-body font-bold text-xl text-[#0F172A] mb-2">
                  Next Best Action
                </h3>
                <p className="font-body text-sm text-[#64748B] leading-relaxed mb-6">
                  12 explainability parameters. Not a generic catalog suggestion —
                  precise explanation of WHY, for THIS gap, at THIS career priority.
                </p>
              </div>

              {/* Mini Visual: Explainable Recommendation */}
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl text-left">
                <span className="text-[10px] font-mono font-bold text-[#3B82F6]">
                  WHY THIS INTERVENTION:
                </span>
                <p className="text-[11px] font-body text-[#475569] mt-0.5">
                  High role impact for NSS 79th round data processing.
                </p>
              </div>
            </Card>
          </motion.div>

          {/* Card 4 (Wide span-2 on desktop): Agentic AI Pipeline */}
          <motion.div
            initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.3 }}
            className="lg:col-span-2"
          >
            <Card className="h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6] mb-4">
                  <Workflow className="w-6 h-6" />
                </div>
                <h3 className="font-body font-bold text-xl text-[#0F172A] mb-2">
                  Agentic AI Pipeline
                </h3>
                <p className="font-body text-sm text-[#64748B] leading-relaxed mb-6">
                  Three autonomous multi-agent systems — Diagnostic Agent,
                  Intervention Agent, and Monitoring Agent — synchronized by a
                  central deterministic orchestrator to guarantee non-hallucinatory
                  pedagogical guidance.
                </p>
              </div>

              {/* Mini Visual: Sequential Agent Timeline */}
              <div className="p-3.5 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl flex items-center justify-between">
                {[
                  "Diagnostic Agent",
                  "Orchestrator",
                  "Intervention Agent",
                  "Monitoring Agent",
                ].map((agent, i, arr) => (
                  <React.Fragment key={agent}>
                    <div className="flex flex-col items-center">
                      <div className="w-3 h-3 rounded-full bg-[#3B82F6] shadow-[0_0_8px_rgba(59,130,246,0.6)] mb-1" />
                      <span className="text-[10px] font-mono text-[#0F172A] font-semibold text-center">
                        {agent}
                      </span>
                    </div>
                    {i < arr.length - 1 && (
                      <div className="h-0.5 flex-1 bg-[#CBD5E1] mx-2" />
                    )}
                  </React.Fragment>
                ))}
              </div>
            </Card>
          </motion.div>

          {/* Card 5: Retention Verification */}
          <motion.div
            initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.4 }}
          >
            <Card className="h-full flex flex-col justify-between">
              <div>
                <div className="w-12 h-12 rounded-xl bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6] mb-4">
                  <Clock className="w-6 h-6" />
                </div>
                <h3 className="font-body font-bold text-xl text-[#0F172A] mb-2">
                  Retention Verification
                </h3>
                <p className="font-body text-sm text-[#64748B] leading-relaxed mb-6">
                  Knowledge decay curves are modeled quantitatively. Re-testing is
                  automated at 14, 30, and 90 days to prove long-term capability.
                </p>
              </div>

              {/* Mini Visual: Retention Decay Curve SVG */}
              <div className="p-3 bg-[#F8FAFC] border border-[#E2E8F0] rounded-xl flex flex-col items-center">
                <svg className="w-full h-12" viewBox="0 0 200 48" fill="none">
                  <path
                    d="M 10 10 Q 50 35, 100 15 T 190 12"
                    stroke="#3B82F6"
                    strokeWidth="2"
                  />
                  <circle cx="10" cy="10" r="3" fill="#3B82F6" />
                  <circle cx="100" cy="15" r="3" fill="#3B82F6" />
                  <circle cx="190" cy="12" r="3" fill="#3B82F6" />
                </svg>
                <span className="font-mono text-[9px] text-[#94A3B8] mt-1">
                  Ebbinghaus Memory Reinforcement Cycle
                </span>
              </div>
            </Card>
          </motion.div>
        </div>
      </div>
    </section>
  );
}
