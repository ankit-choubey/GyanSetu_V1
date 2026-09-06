"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import {
  LogIn,
  HelpCircle,
  Activity,
  AlertCircle,
  Lightbulb,
  CheckCircle,
  ArrowUpRight,
  Sparkles,
  Check,
  ChevronRight,
  RefreshCw,
  Award,
  Zap,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { useReducedMotion } from "@/hooks/useReducedMotion";

// =============================================================================
// STEP 1: INTERACTIVE LOGIN ILLUSTRATION
// =============================================================================
function Step1LoginCard() {
  const [signedIn, setSignedIn] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSignIn = () => {
    if (signedIn) {
      setSignedIn(false);
      return;
    }
    setLoading(true);
    setTimeout(() => {
      setLoading(false);
      setSignedIn(true);
    }, 400);
  };

  return (
    <div className="w-full max-w-[400px] xl:max-w-[430px] bg-white border border-[#E2E8F0] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:shadow-lg transition-all text-left">
      {/* Browser Bar */}
      <div className="flex items-center justify-between pb-3 mb-4 border-b border-[#F1F5F9]">
        <div className="flex items-center gap-2">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-400" />
          <div className="w-2.5 h-2.5 rounded-full bg-amber-400" />
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
          <span className="font-mono text-[11px] text-[#94A3B8] ml-1">
            auth.mospi.gov.in
          </span>
        </div>
        <span className="font-mono text-[10px] text-emerald-600 bg-emerald-50 px-2 py-0.5 rounded-full font-semibold">
          {signedIn ? "ACTIVE SESSION" : "SSO GATEWAY"}
        </span>
      </div>

      {!signedIn ? (
        <div className="space-y-3">
          <div>
            <label className="block text-[11px] font-mono text-[#64748B] mb-1 uppercase font-semibold">
              Official Email
            </label>
            <div className="h-9 w-full bg-[#F8FAFC] rounded-lg border border-[#E2E8F0] px-3 flex items-center text-xs text-[#0F172A] font-mono shadow-2xs">
              officer.sharma@mospi.gov.in
            </div>
          </div>
          <div>
            <label className="block text-[11px] font-mono text-[#64748B] mb-1 uppercase font-semibold">
              Passkey / SSO Credential
            </label>
            <div className="h-9 w-full bg-[#F8FAFC] rounded-lg border border-[#E2E8F0] px-3 flex items-center text-xs text-[#94A3B8] tracking-widest shadow-2xs">
              ••••••••••••••••
            </div>
          </div>
          <button
            onClick={handleSignIn}
            disabled={loading}
            className="w-full h-10 mt-1 rounded-xl bg-[#2563EB] hover:bg-[#1D4ED8] active:scale-[0.98] text-white font-body text-xs font-semibold flex items-center justify-center gap-2 shadow-sm transition-all cursor-pointer"
          >
            {loading ? (
              <RefreshCw className="w-4 h-4 animate-spin" />
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In (JSO Cadre)</span>
                <span className="text-[10px] font-mono opacity-70 bg-blue-700/50 px-1.5 py-0.5 rounded">
                  CLICK ME
                </span>
              </>
            )}
          </button>
        </div>
      ) : (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="space-y-3 py-1"
        >
          <div className="flex items-center gap-3 p-3 bg-[#EFF6FF] border border-[#BFDBFE] rounded-xl">
            <div className="w-10 h-10 rounded-full bg-[#2563EB] text-white flex items-center justify-center font-heading text-lg font-bold">
              RS
            </div>
            <div>
              <div className="font-body text-xs font-bold text-[#0F172A] flex items-center gap-1.5">
                <span>R. Sharma</span>
                <span className="px-1.5 py-0.2 rounded bg-blue-200/70 text-[#1D4ED8] text-[9px] font-mono font-bold uppercase">
                  JSO Cadre
                </span>
              </div>
              <p className="font-mono text-[10.5px] text-[#2563EB]">
                DESK #4 · MOSPI / NSSO HQ
              </p>
            </div>
          </div>
          <div className="p-2.5 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] text-[11px] text-[#475569] flex items-center justify-between">
            <span className="flex items-center gap-1.5 text-emerald-700 font-medium">
              <Check className="w-3.5 h-3.5 text-emerald-600" />
              Role baseline resolved automatically
            </span>
            <button
              onClick={handleSignIn}
              className="text-[10px] font-mono text-[#2563EB] underline hover:text-blue-800 cursor-pointer"
            >
              Reset
            </button>
          </div>
        </motion.div>
      )}
    </div>
  );
}

// =============================================================================
// STEP 2: INTERACTIVE DIAGNOSTIC QUESTION
// =============================================================================
function Step2DiagnosticCard() {
  const [selectedOption, setSelectedOption] = useState<"A" | "B" | null>("B");

  return (
    <div className="w-full max-w-[400px] xl:max-w-[430px] bg-white border border-[#E2E8F0] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:shadow-lg transition-all text-left">
      <div className="flex justify-between items-center mb-3">
        <span className="font-mono text-xs text-[#2563EB] font-bold flex items-center gap-1">
          <HelpCircle className="w-3.5 h-3.5" /> Item 03 / 08
        </span>
        <span className="px-2.5 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] font-mono text-[10px] font-bold border border-[#BFDBFE]">
          ADAPTIVE LEVEL: MEDIUM
        </span>
      </div>

      {/* Progress Bar */}
      <div className="h-2 w-full bg-[#F1F5F9] rounded-full overflow-hidden mb-4">
        <div className="h-full bg-[#2563EB] w-3/5 rounded-full" />
      </div>

      <p className="font-body text-xs md:text-[13px] font-semibold text-[#0F172A] mb-3 leading-snug">
        What is the design effect (deff) under cluster sampling with intra-cluster correlation ρ?
      </p>

      {/* Clickable Choices */}
      <div className="space-y-2">
        <div
          onClick={() => setSelectedOption("A")}
          className={`p-2.5 rounded-xl border text-xs flex items-center justify-between cursor-pointer transition-all ${
            selectedOption === "A"
              ? "border-rose-400 bg-rose-50/70 text-[#0F172A]"
              : "border-[#E2E8F0] hover:border-slate-300 hover:bg-slate-50 text-[#64748B]"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                selectedOption === "A"
                  ? "bg-rose-500 text-white"
                  : "border border-[#CBD5E1] text-slate-500"
              }`}
            >
              A
            </span>
            <span className="font-medium text-[11.5px]">
              Ratio of cluster variance to SRS variance
            </span>
          </div>
          {selectedOption === "A" && (
            <span className="text-[10px] font-mono text-rose-600 font-bold">
              Formula variant
            </span>
          )}
        </div>

        <div
          onClick={() => setSelectedOption("B")}
          className={`p-2.5 rounded-xl border text-xs flex items-center justify-between cursor-pointer transition-all ${
            selectedOption === "B"
              ? "border-[#2563EB] bg-[#EFF6FF] text-[#0F172A] shadow-xs"
              : "border-[#E2E8F0] hover:border-blue-300 hover:bg-blue-50/40 text-[#64748B]"
          }`}
        >
          <div className="flex items-center gap-2.5">
            <span
              className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                selectedOption === "B"
                  ? "bg-[#2563EB] text-white"
                  : "border border-[#CBD5E1] text-slate-500"
              }`}
            >
              B
            </span>
            <span className="font-medium text-[11.5px]">
              1 + (m - 1) × rho
            </span>
          </div>
          {selectedOption === "B" && (
            <span className="text-[10px] font-mono text-emerald-600 bg-emerald-100/70 px-2 py-0.5 rounded-full font-bold flex items-center gap-1">
              <Check className="w-3 h-3 stroke-[3]" /> +0.14 θ
            </span>
          )}
        </div>
      </div>
      <p className="text-[10px] font-mono text-slate-400 mt-2 text-right">
        Click options to test interactive response
      </p>
    </div>
  );
}

// =============================================================================
// STEP 3: HOVER-EXPANDING RADAR GRAPH
// =============================================================================
function Step3RadarCard() {
  const [hoveredAxis, setHoveredAxis] = useState<string | null>(null);

  return (
    <div className="group w-full max-w-[400px] xl:max-w-[430px] bg-white border border-[#E2E8F0] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:shadow-xl hover:border-blue-300 transition-all text-center flex flex-col items-center cursor-pointer">
      <div className="flex items-center justify-between w-full mb-1">
        <span className="font-mono text-xs font-bold text-[#64748B] uppercase tracking-wider">
          5-Point Competency Profile
        </span>
        <span className="text-[10px] font-mono text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded-full font-bold group-hover:bg-blue-600 group-hover:text-white transition-colors">
          HOVER TO EXPAND
        </span>
      </div>

      {/* Radar SVG with Smooth Scaling Transition on Hover */}
      <div className="relative py-2 flex items-center justify-center">
        <svg
          className="w-44 h-44 sm:w-52 sm:h-52 transform group-hover:scale-115 transition-transform duration-300 ease-out origin-center"
          viewBox="0 0 160 160"
        >
          {/* Faint Outer Ring */}
          <circle cx="80" cy="80" r="65" fill="none" stroke="#F1F5F9" strokeWidth="1" />
          {/* Faint pentagon background */}
          <polygon
            points="80,16 141,60 118,132 42,132 19,60"
            fill="#F8FAFC"
            stroke="#E2E8F0"
            strokeWidth="1.2"
          />
          {/* Mid grid pentagon */}
          <polygon
            points="80,48 110,70 99,106 61,106 50,70"
            fill="none"
            stroke="#E2E8F0"
            strokeWidth="0.8"
            strokeDasharray="3 3"
          />

          {/* Profile radar shape */}
          <polygon
            points="80,36 125,72 105,115 55,120 45,70"
            fill="#3B82F6"
            fillOpacity="0.25"
            stroke="#2563EB"
            strokeWidth="2.5"
            className="group-hover:fill-opacity-40 transition-all duration-300"
          />

          {/* Vertex Highlight Dots */}
          <circle cx="80" cy="36" r="3.5" fill="#2563EB" />
          <circle cx="125" cy="72" r="3.5" fill="#2563EB" />
          <circle cx="105" cy="115" r="3.5" fill="#2563EB" />
          <circle cx="55" cy="120" r="3.5" fill="#2563EB" />
          <circle cx="45" cy="70" r="3.5" fill="#2563EB" />

          {/* Axis Labels */}
          <text
            x="80"
            y="12"
            textAnchor="middle"
            className="text-[7.5px] font-mono font-bold fill-[#2563EB]"
          >
            MASTERY (0.52)
          </text>
          <text
            x="146"
            y="62"
            textAnchor="start"
            className="text-[7.5px] font-mono font-bold fill-[#475569]"
          >
            CONF (0.78)
          </text>
          <text
            x="120"
            y="145"
            textAnchor="middle"
            className="text-[7.5px] font-mono font-bold fill-[#475569]"
          >
            COV (0.90)
          </text>
          <text
            x="40"
            y="145"
            textAnchor="middle"
            className="text-[7.5px] font-mono font-bold fill-[#FB7185]"
          >
            REC (0.45)
          </text>
          <text
            x="12"
            y="62"
            textAnchor="end"
            className="text-[7.5px] font-mono font-bold fill-[#475569]"
          >
            DIV (0.85)
          </text>
        </svg>
      </div>

      <div className="w-full mt-2 pt-2 border-t border-[#F1F5F9] flex items-center justify-between text-[11px] font-mono text-[#64748B]">
        <span>Fused Vector Dimension: 5D</span>
        <span className="text-[#2563EB] font-bold">Theta: +0.48 σ</span>
      </div>
    </div>
  );
}

// =============================================================================
// STEP 4: INTERACTIVE GAP IDENTIFIER
// =============================================================================
function Step4GapCard() {
  const [inspected, setInspected] = useState(false);

  return (
    <div
      onClick={() => setInspected(!inspected)}
      className="w-full max-w-[400px] xl:max-w-[430px] bg-white border border-[#E2E8F0] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:shadow-lg hover:border-rose-300 transition-all text-left cursor-pointer"
    >
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs text-[#EF4444] font-bold uppercase flex items-center gap-1.5">
          <span className="w-2.5 h-2.5 rounded-full bg-rose-500 animate-pulse" />
          PRIORITY: HIGH (0.84)
        </span>
        <span className="font-mono text-[10px] text-slate-400 bg-slate-100 px-2 py-0.5 rounded">
          {inspected ? "COLLAPSE" : "CLICK TO INSPECT"}
        </span>
      </div>

      <h5 className="font-body text-sm font-bold text-[#0F172A] mb-1">
        Variance Estimation
      </h5>
      <p className="font-body text-xs text-[#64748B] mb-3">
        Competency: Sampling Design &amp; Statistical Estimation
      </p>

      {/* Progress Gap Bar */}
      <div className="h-2.5 w-full bg-rose-50 rounded-full overflow-hidden mb-1.5 border border-rose-100">
        <div className="h-full bg-rose-500 w-[42%] rounded-full" />
      </div>

      <div className="flex justify-between text-[11px] font-mono mb-2">
        <span className="text-rose-600 font-bold">Current: 0.42</span>
        <span className="text-slate-500">Target: 0.75</span>
        <span className="text-rose-500 font-bold">Gap: Δ -0.33</span>
      </div>

      {/* Expandable Breakdown Formula */}
      <div
        className={`p-2.5 rounded-xl transition-all duration-300 text-[11px] font-mono ${
          inspected
            ? "bg-rose-50 border border-rose-200 text-rose-900 mt-2"
            : "bg-[#F8FAFC] border border-[#E2E8F0] text-[#64748B]"
        }`}
      >
        <span className="font-bold text-rose-600 block mb-0.5">
          PRIORITY FORMULA:
        </span>
        Role Weight (0.9) × Gap Size (0.33) × Uncertainty (0.85) ={" "}
        <span className="font-bold text-[#EF4444]">0.84 HIGH</span>
      </div>
    </div>
  );
}

// =============================================================================
// STEP 5: INTERACTIVE NEXT BEST ACTION
// =============================================================================
function Step5ActionCard() {
  const [queued, setQueued] = useState(false);

  return (
    <div className="w-full max-w-[400px] xl:max-w-[430px] bg-white border-2 border-[#3B82F6] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(59,130,246,0.12)] hover:shadow-xl transition-all text-left">
      <div className="flex items-center justify-between mb-2">
        <span className="px-2.5 py-0.5 rounded-full bg-[#EFF6FF] text-[#2563EB] font-mono text-[10.5px] font-bold border border-[#BFDBFE]">
          RECOMMENDED #1 OF 12
        </span>
        <span className="text-xs font-mono text-[#64748B] flex items-center gap-1">
          <Zap className="w-3.5 h-3.5 text-amber-500" /> 20 mins
        </span>
      </div>

      <h5 className="font-body text-sm md:text-base font-bold text-[#0F172A] mb-1">
        NSSTA Practical Task — Neyman Allocation
      </h5>

      <div className="p-3 bg-[#F8FAFC] rounded-xl border border-[#E2E8F0] my-3">
        <p className="font-mono text-[10px] text-[#2563EB] font-bold mb-1 uppercase tracking-wider">
          WHY THIS ACTION:
        </p>
        <p className="font-body text-xs text-[#475569] leading-relaxed">
          Directly closes high-uncertainty gap in formula application for JSO cadre. Ranked #1 out of 14 catalog interventions.
        </p>
      </div>

      <button
        onClick={() => setQueued(!queued)}
        className={`w-full h-9 rounded-xl font-body text-xs font-semibold flex items-center justify-center gap-2 transition-all cursor-pointer ${
          queued
            ? "bg-emerald-600 text-white shadow-sm"
            : "bg-[#2563EB] hover:bg-blue-700 text-white shadow-sm"
        }`}
      >
        {queued ? (
          <>
            <Check className="w-4 h-4" />
            <span>Assigned to Officer Queue</span>
          </>
        ) : (
          <>
            <Sparkles className="w-4 h-4" />
            <span>Assign Intervention (Click to Test)</span>
          </>
        )}
      </button>
    </div>
  );
}

// =============================================================================
// STEP 6: INTERACTIVE RETEST & PROOF
// =============================================================================
function Step6RetestCard() {
  const [retested, setRetested] = useState(false);

  return (
    <div className="w-full max-w-[400px] xl:max-w-[430px] bg-white border border-[#E2E8F0] rounded-2xl p-5 md:p-6 shadow-[0_4px_24px_rgba(0,0,0,0.06)] hover:shadow-lg hover:border-emerald-300 transition-all text-left">
      <div className="flex items-center justify-between mb-2">
        <span className="font-mono text-xs text-[#0D9488] font-bold uppercase flex items-center gap-1.5">
          <CheckCircle className="w-4 h-4 text-emerald-600" />
          {retested ? "GAP RESOLVED & VERIFIED" : "POST-ASSESSMENT READY"}
        </span>
        <span className="font-mono text-[10px] text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold">
          EVIDENCE FUSED
        </span>
      </div>

      <div className="flex items-baseline gap-3 my-2">
        <span className="font-heading text-3xl text-[#94A3B8] line-through">
          0.42
        </span>
        <span className="font-heading text-4xl md:text-5xl text-[#0D9488]">
          {retested ? "0.81" : "0.74"}
        </span>
        <span className="font-body text-xs text-[#0D9488] font-bold flex items-center bg-emerald-50 px-2 py-1 rounded-md">
          {retested ? "+93% GAIN" : "+76% GAIN"} <ArrowUpRight className="w-4 h-4" />
        </span>
      </div>

      <p className="font-body text-xs text-[#64748B] mb-3 leading-relaxed">
        Evidence logged: Practical Task submission + Post-assessment passed. Next retention verification scheduled in 14 days.
      </p>

      <button
        onClick={() => setRetested(!retested)}
        className="w-full h-8.5 rounded-xl border border-emerald-300 bg-emerald-50/60 hover:bg-emerald-100 text-emerald-800 font-mono text-[11px] font-bold flex items-center justify-center gap-1.5 transition-colors cursor-pointer"
      >
        <RefreshCw className="w-3.5 h-3.5" />
        <span>{retested ? "Reset Test Simulation" : "Click to Simulate Re-Test Check"}</span>
      </button>
    </div>
  );
}

// =============================================================================
// STEP CONFIGURATION ARRAY
// =============================================================================
interface StepData {
  number: string;
  title: string;
  description: string;
  renderIllustration: () => React.ReactNode;
}

const STEPS: StepData[] = [
  {
    number: "01",
    title: "OFFICER LOGS IN",
    description:
      "Profile loaded. Role-based competency requirements and baseline skills are automatically resolved.",
    renderIllustration: () => <Step1LoginCard />,
  },
  {
    number: "02",
    title: "DIAGNOSTIC ASSESSMENT",
    description:
      "Adaptive questions start — step up if correct, step down if wrong. 5–10 minutes only, zero test fatigue.",
    renderIllustration: () => <Step2DiagnosticCard />,
  },
  {
    number: "03",
    title: "COMPETENCY STATE CALCULATED",
    description:
      "5-point profile generated: Mastery, Confidence, Coverage, Recency, and Diversity fused into unified vector.",
    renderIllustration: () => <Step3RadarCard />,
  },
  {
    number: "04",
    title: "GAP IDENTIFIED",
    description:
      "Gaps found at precise subskill level. Priority formula = Role Importance × Gap Size × Uncertainty.",
    renderIllustration: () => <Step4GapCard />,
  },
  {
    number: "05",
    title: "NEXT BEST ACTION",
    description:
      "12 explainability fields. Not 'take this course' — WHY, for THIS gap, at THIS priority. Ranked by impact.",
    renderIllustration: () => <Step5ActionCard />,
  },
  {
    number: "06",
    title: "LOOP CLOSES & RE-TESTS",
    description:
      "Officer completes intervention + post-assessment. Evidence fuses → State updates → Retention scheduled.",
    renderIllustration: () => <Step6RetestCard />,
  },
];

// =============================================================================
// MAIN COMPONENT EXPORT
// =============================================================================
export function HowItWorksSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="how-it-works"
      className="relative py-28 md:py-36 lg:py-44 px-6 bg-[#F8FAFC] border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1360px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="04" text="HOW IT WORKS" />
        <SectionHeading
          title="FROM LOGIN TO VERIFIED COMPETENCY"
          subtitle="A continuous intelligence pipeline executing real-time diagnostics, targeted actions, and measurable proof."
        />

        {/* ========================================================================= */}
        {/* DESKTOP ALTERNATING TIMELINE (lg: >= 1024px) — Expanded Scale */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative max-w-6xl xl:max-w-[1240px] mx-auto my-20">
          {/* Central Vertical Timeline Line */}
          <div className="absolute top-0 bottom-0 left-1/2 -translate-x-1/2 w-1 bg-gradient-to-b from-blue-400 via-blue-500 to-teal-400" />

          {/* Alternating Steps */}
          <div className="space-y-24">
            {STEPS.map((step, idx) => {
              const isEven = idx % 2 === 0;

              return (
                <div
                  key={step.number}
                  className="relative flex items-center justify-between"
                >
                  {/* Left Side Container */}
                  <div
                    className={`w-[46%] ${
                      isEven ? "text-right pr-8" : "text-left pl-8 order-2"
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
                        {/* Giant Watermark Number behind text */}
                        <span className="absolute -top-12 -right-6 font-heading text-9xl text-[#DBEAFE]/40 pointer-events-none select-none z-0">
                          {step.number}
                        </span>
                        <div className="relative z-10">
                          <span className="font-mono text-xs font-bold text-[#2563EB] uppercase tracking-wider block mb-1">
                            PHASE {step.number}
                          </span>
                          <h4 className="font-heading text-3xl md:text-4xl text-[#0F172A] mb-2 leading-tight">
                            {step.title}
                          </h4>
                          <p className="font-body text-base text-[#64748B] leading-relaxed max-w-md ml-auto">
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
                  <div className="relative z-10 w-6 h-6 rounded-full bg-[#2563EB] border-4 border-white shadow-md ring-4 ring-blue-100 shrink-0" />

                  {/* Right Side Container */}
                  <div
                    className={`w-[46%] ${
                      isEven ? "text-left pl-8 order-2" : "text-left pr-8 order-1"
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
                        {/* Giant Watermark Number behind text */}
                        <span className="absolute -top-12 -left-6 font-heading text-9xl text-[#DBEAFE]/40 pointer-events-none select-none z-0">
                          {step.number}
                        </span>
                        <div className="relative z-10">
                          <span className="font-mono text-xs font-bold text-[#2563EB] uppercase tracking-wider block mb-1">
                            PHASE {step.number}
                          </span>
                          <h4 className="font-heading text-3xl md:text-4xl text-[#0F172A] mb-2 leading-tight">
                            {step.title}
                          </h4>
                          <p className="font-body text-base text-[#64748B] leading-relaxed max-w-md">
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
        {/* TABLET & MOBILE (< 1024px) — Single Left-Rail Column */}
        {/* ========================================================================= */}
        <div className="lg:hidden relative text-left max-w-lg mx-auto my-12 pl-8">
          {/* Left Rail Timeline Line */}
          <div className="absolute top-0 bottom-0 left-3 w-1 bg-gradient-to-b from-blue-400 to-teal-400" />

          <div className="space-y-16">
            {STEPS.map((step) => (
              <div key={step.number} className="relative">
                {/* Pin Circle Marker */}
                <div className="absolute -left-[29px] top-1.5 w-5 h-5 rounded-full bg-[#2563EB] border-4 border-white shadow-sm ring-2 ring-blue-100" />

                <div>
                  <span className="font-mono text-xs font-bold text-[#2563EB]">
                    PHASE {step.number}
                  </span>
                  <h4 className="font-heading text-2xl text-[#0F172A] mt-0.5 mb-1.5">
                    {step.title}
                  </h4>
                  <p className="font-body text-sm text-[#64748B] mb-5 leading-relaxed">
                    {step.description}
                  </p>

                  {/* Illustration below text on mobile */}
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
