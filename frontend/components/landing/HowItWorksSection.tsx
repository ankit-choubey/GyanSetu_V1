"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  LogIn,
  HelpCircle,
  Activity,
  AlertCircle,
  Lightbulb,
  CheckCircle,
  ArrowUpRight,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface StepData {
  number: string;
  title: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
  renderIllustration: () => React.ReactNode;
}

const STEPS: StepData[] = [
  {
    number: "01",
    title: "OFFICER LOGS IN",
    description:
      "Profile loaded. Role-based competency requirements and baseline skills are automatically resolved.",
    icon: LogIn,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border border-[#E2E8F0] rounded-xl p-4 shadow-sm select-none">
        <div className="flex items-center gap-2 mb-3">
          <div className="w-2.5 h-2.5 rounded-full bg-[#CBD5E1]" />
          <div className="w-2.5 h-2.5 rounded-full bg-[#E2E8F0]" />
          <span className="font-mono text-[10px] text-[#94A3B8]">auth.mospi.gov.in</span>
        </div>
        <div className="h-6 w-full bg-[#F1F5F9] rounded mb-2 border border-[#E2E8F0] px-2 flex items-center text-[10px] text-[#94A3B8]">
          officer.sharma@mospi.gov.in
        </div>
        <div className="h-6 w-full bg-[#F1F5F9] rounded mb-3 border border-[#E2E8F0] px-2 flex items-center text-[10px] text-[#94A3B8]">
          ••••••••••••
        </div>
        <div className="h-6 w-full bg-[#3B82F6] rounded flex items-center justify-center text-[11px] font-semibold text-white">
          Sign In (JSO Cadre)
        </div>
      </div>
    ),
  },
  {
    number: "02",
    title: "DIAGNOSTIC ASSESSMENT",
    description:
      "Adaptive questions start — step up if correct, step down if wrong. 5–10 minutes only, zero test fatigue.",
    icon: HelpCircle,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border border-[#E2E8F0] rounded-xl p-4 shadow-sm select-none text-left">
        <div className="flex justify-between items-center mb-2">
          <span className="font-mono text-[10px] text-[#3B82F6] font-bold">Item 03 / 08</span>
          <span className="px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#3B82F6] font-mono text-[9px] font-bold">
            DIFFICULTY: MEDIUM
          </span>
        </div>
        <div className="h-1.5 w-full bg-[#F1F5F9] rounded-full overflow-hidden mb-3">
          <div className="h-full bg-[#3B82F6] w-3/5 rounded-full" />
        </div>
        <p className="font-body text-[11px] font-semibold text-[#0F172A] mb-2 leading-tight">
          What is the design effect (deff) under cluster sampling?
        </p>
        <div className="space-y-1.5">
          <div className="p-1.5 rounded border border-[#E2E8F0] text-[10px] text-[#64748B] flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 rounded-full border border-[#CBD5E1] flex items-center justify-center text-[8px]">A</span>
            <span>Ratio of cluster variance to SRS variance</span>
          </div>
          <div className="p-1.5 rounded border border-[#3B82F6] bg-[#EFF6FF] text-[10px] text-[#1E3A5F] font-medium flex items-center gap-1.5">
            <span className="w-3.5 h-3.5 rounded-full bg-[#3B82F6] text-white flex items-center justify-center text-[8px]">B</span>
            <span>1 + (m - 1) × rho</span>
          </div>
        </div>
      </div>
    ),
  },
  {
    number: "03",
    title: "COMPETENCY STATE CALCULATED",
    description:
      "5-point profile generated: Mastery, Confidence, Coverage, Recency, and Diversity fused into unified vector.",
    icon: Activity,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border border-[#E2E8F0] rounded-xl p-3 shadow-sm select-none flex flex-col items-center">
        <span className="font-mono text-[10px] font-bold text-[#64748B] uppercase mb-1">
          5-Point Competency Profile
        </span>
        <svg className="w-36 h-36" viewBox="0 0 160 160">
          {/* Faint pentagon background */}
          <polygon
            points="80,16 141,60 118,132 42,132 19,60"
            fill="#F8FAFC"
            stroke="#E2E8F0"
            strokeWidth="1"
          />
          {/* Profile radar shape */}
          <polygon
            points="80,36 125,72 105,115 55,120 45,70"
            fill="#3B82F6"
            fillOpacity="0.2"
            stroke="#3B82F6"
            strokeWidth="2"
          />
          {/* Axis Labels */}
          <text x="80" y="12" textAnchor="middle" className="text-[7px] font-mono fill-[#94A3B8]">MASTERY</text>
          <text x="145" y="62" textAnchor="start" className="text-[7px] font-mono fill-[#94A3B8]">CONF</text>
          <text x="120" y="144" textAnchor="middle" className="text-[7px] font-mono fill-[#94A3B8]">COV</text>
          <text x="40" y="144" textAnchor="middle" className="text-[7px] font-mono fill-[#94A3B8]">REC</text>
          <text x="14" y="62" textAnchor="end" className="text-[7px] font-mono fill-[#94A3B8]">DIV</text>
        </svg>
      </div>
    ),
  },
  {
    number: "04",
    title: "GAP IDENTIFIED",
    description:
      "Gaps found at precise subskill level. Priority formula = Role Importance × Gap Size × Uncertainty.",
    icon: AlertCircle,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border border-[#E2E8F0] rounded-xl p-4 shadow-sm select-none text-left">
        <div className="flex items-center justify-between mb-2">
          <span className="font-mono text-[10px] text-[#FB7185] font-bold uppercase">
            PRIORITY: HIGH (0.84)
          </span>
          <span className="w-2 h-2 rounded-full bg-[#FB7185]" />
        </div>
        <h5 className="font-body text-xs font-bold text-[#0F172A] mb-1">
          Variance Estimation
        </h5>
        <p className="font-body text-[10px] text-[#64748B] mb-2">
          Competency: Sampling Design & Estimation
        </p>
        <div className="h-2 w-full bg-[#FFF1F2] rounded-full overflow-hidden mb-1">
          <div className="h-full bg-[#FB7185] w-[42%] rounded-full" />
        </div>
        <div className="flex justify-between text-[9px] font-mono text-[#94A3B8]">
          <span>Current: 0.42</span>
          <span>Target: 0.75</span>
        </div>
      </div>
    ),
  },
  {
    number: "05",
    title: "NEXT BEST ACTION",
    description:
      "12 explainability fields. Not 'take this course' — WHY, for THIS gap, at THIS priority. Ranked by impact.",
    icon: Lightbulb,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border-2 border-[#3B82F6] rounded-xl p-3.5 shadow-sm select-none text-left">
        <div className="flex items-center justify-between mb-1.5">
          <span className="px-2 py-0.5 rounded-full bg-[#EFF6FF] text-[#3B82F6] font-mono text-[9px] font-bold">
            RECOMMENDED #1
          </span>
          <span className="text-[10px] font-mono text-[#64748B]">20 mins</span>
        </div>
        <h5 className="font-body text-xs font-bold text-[#0F172A] mb-1">
          NSSTA Practical Task — Neyman Allocation
        </h5>
        <div className="p-2 bg-[#F8FAFC] rounded border border-[#E2E8F0] mt-2">
          <p className="font-mono text-[9px] text-[#3B82F6] font-semibold mb-0.5">
            WHY THIS ACTION:
          </p>
          <p className="font-body text-[10px] text-[#475569] leading-tight">
            Directly closes high-uncertainty gap in formula application for JSO cadre.
          </p>
        </div>
      </div>
    ),
  },
  {
    number: "06",
    title: "LOOP CLOSES & RE-TESTS",
    description:
      "Officer completes intervention + post-assessment. Evidence fuses → State updates → Retention scheduled.",
    icon: CheckCircle,
    renderIllustration: () => (
      <div className="w-full max-w-[280px] bg-white border border-[#E2E8F0] rounded-xl p-4 shadow-sm select-none text-left">
        <div className="flex items-center justify-between mb-2">
          <span className="font-mono text-[10px] text-[#0D9488] font-bold uppercase">
            GAP RESOLVED
          </span>
          <CheckCircle className="w-4 h-4 text-[#0D9488]" />
        </div>
        <div className="flex items-baseline gap-2 mb-2">
          <span className="font-heading text-3xl text-[#64748B] line-through">
            0.42
          </span>
          <span className="font-heading text-4xl text-[#0D9488]">
            0.74
          </span>
          <span className="font-body text-xs text-[#0D9488] font-bold flex items-center">
            +76% <ArrowUpRight className="w-3.5 h-3.5" />
          </span>
        </div>
        <p className="font-body text-[10px] text-[#64748B]">
          Evidence logged: Task submission + Post-assessment passed.
        </p>
      </div>
    ),
  },
];

export function HowItWorksSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="how-it-works"
      className="relative py-24 md:py-32 px-6 bg-[#F8FAFC] border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="04" text="HOW IT WORKS" />
        <SectionHeading
          title="FROM LOGIN TO VERIFIED COMPETENCY"
          subtitle="A continuous intelligence pipeline executing real-time diagnostics, targeted actions, and measurable proof."
        />

        {/* ========================================================================= */}
        {/* DESKTOP ALTERNATING TIMELINE (lg: >= 1024px) */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative max-w-4xl mx-auto my-16">
          {/* Central Vertical Timeline Line (z-index: 1 per §2.7 & §3.5) */}
          <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-0.5 bg-[#3B82F6]" />

          {/* Alternating Steps */}
          <div className="space-y-20">
            {STEPS.map((step, idx) => {
              const isEven = idx % 2 === 0;

              return (
                <div
                  key={step.number}
                  className="relative flex items-center justify-between"
                >
                  {/* Left Side Container */}
                  <div
                    className={`w-[42%] ${
                      isEven ? "text-right pr-6" : "text-left pl-6 order-2"
                    }`}
                  >
                    {isEven ? (
                      /* Text on Left */
                      <motion.div
                        initial={
                          shouldReduceMotion ? false : { x: -30, opacity: 0 }
                        }
                        whileInView={
                          shouldReduceMotion ? {} : { x: 0, opacity: 1 }
                        }
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.5 }}
                        className="relative"
                      >
                        {/* Giant Watermark Number behind text per §3.5 */}
                        <span className="absolute -top-10 -right-4 font-heading text-8xl text-[#DBEAFE]/40 pointer-events-none select-none z-0">
                          {step.number}
                        </span>
                        <div className="relative z-10">
                          <h4 className="font-heading text-2xl text-[#0F172A] mb-1">
                            {step.title}
                          </h4>
                          <p className="font-body text-sm text-[#64748B] leading-relaxed">
                            {step.description}
                          </p>
                        </div>
                      </motion.div>
                    ) : (
                      /* Illustration on Left */
                      <motion.div
                        initial={
                          shouldReduceMotion ? false : { scale: 0.9, opacity: 0 }
                        }
                        whileInView={
                          shouldReduceMotion ? {} : { scale: 1, opacity: 1 }
                        }
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.5 }}
                        className="flex justify-start"
                      >
                        {step.renderIllustration()}
                      </motion.div>
                    )}
                  </div>

                  {/* Central Pin Marker on Timeline Line */}
                  <div className="relative z-10 w-4 h-4 rounded-full bg-[#3B82F6] border-4 border-white shadow-sm shrink-0" />

                  {/* Right Side Container */}
                  <div
                    className={`w-[42%] ${
                      isEven ? "text-left pl-6 order-2" : "text-left pr-6 order-1"
                    }`}
                  >
                    {isEven ? (
                      /* Illustration on Right */
                      <motion.div
                        initial={
                          shouldReduceMotion ? false : { scale: 0.9, opacity: 0 }
                        }
                        whileInView={
                          shouldReduceMotion ? {} : { scale: 1, opacity: 1 }
                        }
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.5 }}
                        className="flex justify-start"
                      >
                        {step.renderIllustration()}
                      </motion.div>
                    ) : (
                      /* Text on Right */
                      <motion.div
                        initial={
                          shouldReduceMotion ? false : { x: 30, opacity: 0 }
                        }
                        whileInView={
                          shouldReduceMotion ? {} : { x: 0, opacity: 1 }
                        }
                        viewport={{ once: true, amount: 0.2 }}
                        transition={{ duration: 0.5 }}
                        className="relative"
                      >
                        {/* Giant Watermark Number behind text per §3.5 */}
                        <span className="absolute -top-10 -left-4 font-heading text-8xl text-[#DBEAFE]/40 pointer-events-none select-none z-0">
                          {step.number}
                        </span>
                        <div className="relative z-10">
                          <h4 className="font-heading text-2xl text-[#0F172A] mb-1">
                            {step.title}
                          </h4>
                          <p className="font-body text-sm text-[#64748B] leading-relaxed">
                            {step.description}
                          </p>
                        </div>
                      </motion.div>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ========================================================================= */}
        {/* TABLET & MOBILE (< 1024px) — Single Left-Rail Column (§3.5) */}
        {/* ========================================================================= */}
        <div className="lg:hidden relative text-left max-w-lg mx-auto my-10 pl-8">
          {/* Left Rail Timeline Line */}
          <div className="absolute top-0 bottom-0 left-3 w-0.5 bg-[#3B82F6]" />

          <div className="space-y-12">
            {STEPS.map((step) => (
              <div key={step.number} className="relative">
                {/* Pin Circle Marker */}
                <div className="absolute -left-[27px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#3B82F6] border-2 border-white shadow-sm" />

                <div>
                  <span className="font-mono text-xs font-bold text-[#3B82F6]">
                    STEP {step.number}
                  </span>
                  <h4 className="font-heading text-xl text-[#0F172A] mt-0.5 mb-1">
                    {step.title}
                  </h4>
                  <p className="font-body text-xs text-[#64748B] mb-4 leading-relaxed">
                    {step.description}
                  </p>

                  {/* Illustration below text on mobile per §3.5 */}
                  <div>{step.renderIllustration()}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
