"use client";

import React from "react";
import { motion } from "framer-motion";
import { ArrowUp, CheckCircle2, AlertTriangle, Sparkles } from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function HeroMomentSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="hero-moment"
      className="relative py-24 md:py-32 px-6 bg-gradient-to-b from-white via-[#F8FAFC] to-white border-b border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="05" text="THE RESULT" />
        <SectionHeading
          title="THE HERO MOMENT"
          subtitle="Watch competency state transform in real-time after an officer completes an AI-targeted intervention."
        />

        {/* Side-by-Side Comparison Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto my-12 text-left">
          {/* ========================================================================= */}
          {/* BEFORE CARD */}
          {/* ========================================================================= */}
          <motion.div
            initial={shouldReduceMotion ? false : { x: -50, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { x: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="bg-white border border-[#E2E8F0] rounded-2xl p-6 md:p-8 shadow-sm flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-[#E2E8F0] mb-6">
                <span className="font-mono text-xs uppercase font-bold text-[#FB7185] tracking-wider">
                  BEFORE INTERVENTION
                </span>
                <span className="px-2.5 py-1 rounded-full bg-[#FFF1F2] text-[#FB7185] font-mono text-[10px] font-bold flex items-center gap-1">
                  <AlertTriangle className="w-3 h-3" /> Needs Work
                </span>
              </div>

              {/* Metrics List */}
              <div className="space-y-4 font-body">
                <div>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-sm text-[#64748B]">Mastery:</span>
                    <span className="font-heading text-3xl text-[#FB7185]">
                      <AnimatedCounter target={0.42} decimals={2} />
                    </span>
                  </div>
                  <div className="h-2 w-full bg-[#F1F5F9] rounded-full overflow-hidden">
                    <motion.div
                      initial={shouldReduceMotion ? false : { width: "0%" }}
                      whileInView={shouldReduceMotion ? {} : { width: "42%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.2, ease: "easeOut" }}
                      className="h-full bg-[#FB7185] rounded-full"
                    />
                  </div>
                </div>

                <div className="flex justify-between text-sm py-1 border-b border-[#F1F5F9]">
                  <span className="text-[#64748B]">Confidence:</span>
                  <span className="font-semibold text-[#0F172A]">Low (0.30)</span>
                </div>
                <div className="flex justify-between text-sm py-1 border-b border-[#F1F5F9]">
                  <span className="text-[#64748B]">Coverage:</span>
                  <span className="font-semibold text-[#0F172A]">25% of Domain</span>
                </div>
                <div className="flex justify-between text-sm py-1 border-b border-[#F1F5F9]">
                  <span className="text-[#64748B]">Evidence:</span>
                  <span className="font-semibold text-[#0F172A]">1 Source (Assessment Only)</span>
                </div>
              </div>

              {/* Collapsed Radar Chart SVG (Exact pre-calculated points per §3.6) */}
              <div className="my-6 flex flex-col items-center">
                <span className="font-mono text-[10px] text-[#94A3B8] uppercase mb-1">
                  Collapsed Radar Polygon
                </span>
                <svg className="w-44 h-44" viewBox="0 0 200 200">
                  {/* Outer Polygon Grid */}
                  <polygon
                    points="100,20 176.09,75.28 147.02,164.72 52.98,164.72 23.91,75.28"
                    fill="#F8FAFC"
                    stroke="#E2E8F0"
                    strokeWidth="1"
                  />
                  {/* Spokes */}
                  <line x1="100" y1="100" x2="100" y2="20" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="176.09" y2="75.28" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="147.02" y2="164.72" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="52.98" y2="164.72" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="23.91" y2="75.28" stroke="#E2E8F0" strokeWidth="1" />
                  {/* BEFORE Profile Polygon */}
                  <polygon
                    points="100,66.4 122.83,92.58 111.76,116.18 83.54,122.65 84.78,95.06"
                    fill="#FB7185"
                    fillOpacity="0.25"
                    stroke="#FB7185"
                    strokeWidth="2"
                  />
                </svg>
              </div>
            </div>

            <div className="p-3 bg-[#FFF1F2] border border-[#FFE4E6] rounded-xl text-xs font-medium text-[#FB7185]">
              ❌ Variance Estimation subskill gap identified (Priority 0.84)
            </div>
          </motion.div>

          {/* ========================================================================= */}
          {/* AFTER CARD */}
          {/* ========================================================================= */}
          <motion.div
            initial={shouldReduceMotion ? false : { x: 50, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { x: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, delay: 0.15, ease: "easeOut" }}
            className="bg-gradient-to-br from-white to-[#F0FDFA] border-2 border-[#2DD4BF] rounded-2xl p-6 md:p-8 shadow-[0_8px_30px_rgba(45,212,191,0.15)] flex flex-col justify-between"
          >
            <div>
              <div className="flex items-center justify-between pb-4 border-b border-[#CCFBF1] mb-6">
                <span className="font-mono text-xs uppercase font-bold text-[#0D9488] tracking-wider">
                  POST INTERVENTION
                </span>
                <span className="px-2.5 py-1 rounded-full bg-[#F0FDFA] text-[#0D9488] border border-[#CCFBF1] font-mono text-[10px] font-bold flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" /> Verified Mastery
                </span>
              </div>

              {/* Metrics List */}
              <div className="space-y-4 font-body">
                <div>
                  <div className="flex justify-between items-baseline mb-1">
                    <span className="text-sm text-[#64748B]">Mastery:</span>
                    <div className="flex items-center gap-1.5 font-heading text-3xl text-[#0D9488]">
                      <AnimatedCounter target={0.74} decimals={2} />
                      <span className="text-sm font-body font-bold flex items-center text-[#0D9488]">
                        <ArrowUp className="w-4 h-4 stroke-[3]" /> +76%
                      </span>
                    </div>
                  </div>
                  <div className="h-2 w-full bg-[#F1F5F9] rounded-full overflow-hidden">
                    <motion.div
                      initial={shouldReduceMotion ? false : { width: "0%" }}
                      whileInView={shouldReduceMotion ? {} : { width: "74%" }}
                      viewport={{ once: true }}
                      transition={{ duration: 1.5, delay: 0.2, ease: "easeOut" }}
                      className="h-full bg-[#2DD4BF] rounded-full"
                    />
                  </div>
                </div>

                <div className="flex justify-between text-sm py-1 border-b border-[#E2E8F0]">
                  <span className="text-[#64748B]">Confidence:</span>
                  <span className="font-semibold text-[#0D9488] flex items-center gap-1">
                    High (0.80) <ArrowUp className="w-3 h-3 text-[#0D9488]" />
                  </span>
                </div>
                <div className="flex justify-between text-sm py-1 border-b border-[#E2E8F0]">
                  <span className="text-[#64748B]">Coverage:</span>
                  <span className="font-semibold text-[#0D9488] flex items-center gap-1">
                    60% of Domain <ArrowUp className="w-3 h-3 text-[#0D9488]" />
                  </span>
                </div>
                <div className="flex justify-between text-sm py-1 border-b border-[#E2E8F0]">
                  <span className="text-[#64748B]">Evidence:</span>
                  <span className="font-semibold text-[#0D9488] flex items-center gap-1">
                    2 Types (Assessment + Practical Task) <ArrowUp className="w-3 h-3 text-[#0D9488]" />
                  </span>
                </div>
              </div>

              {/* Expanded Radar Chart SVG (Exact pre-calculated points per §3.6) */}
              <div className="my-6 flex flex-col items-center">
                <span className="font-mono text-[10px] text-[#0D9488] uppercase mb-1">
                  Expanded Competency Profile
                </span>
                <svg className="w-44 h-44" viewBox="0 0 200 200">
                  <polygon
                    points="100,20 176.09,75.28 147.02,164.72 52.98,164.72 23.91,75.28"
                    fill="#F8FAFC"
                    stroke="#E2E8F0"
                    strokeWidth="1"
                  />
                  <line x1="100" y1="100" x2="100" y2="20" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="176.09" y2="75.28" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="147.02" y2="164.72" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="52.98" y2="164.72" stroke="#E2E8F0" strokeWidth="1" />
                  <line x1="100" y1="100" x2="23.91" y2="75.28" stroke="#E2E8F0" strokeWidth="1" />
                  {/* AFTER Profile Polygon */}
                  <polygon
                    points="100,40.8 160.87,80.22 128.21,138.83 67.09,145.3 58.15,86.4"
                    fill="#2DD4BF"
                    fillOpacity="0.3"
                    stroke="#0D9488"
                    strokeWidth="2.5"
                  />
                </svg>
              </div>
            </div>

            <div className="p-3 bg-[#F0FDFA] border border-[#CCFBF1] rounded-xl text-xs font-medium text-[#0D9488]">
              ✅ Variance Estimation resolved & certified for field deployment
            </div>
          </motion.div>
        </div>

        {/* Bottom Intervention Badge */}
        <motion.div
          initial={shouldReduceMotion ? false : { y: 20, opacity: 0 }}
          whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="inline-flex items-center gap-2.5 px-6 py-3 rounded-xl bg-[#EFF6FF] border border-[#DBEAFE] text-left shadow-sm"
        >
          <Sparkles className="w-5 h-5 text-[#3B82F6] shrink-0" />
          <p className="font-body text-xs sm:text-sm font-semibold text-[#1E3A5F]">
            COMPLETED INTERVENTION:{" "}
            <span className="text-[#2563EB] font-bold">
              NSSTA Practical Task — Neyman Allocation Simulation Module
            </span>
          </p>
        </motion.div>
      </div>
    </section>
  );
}
