"use client";

import React from "react";
import { motion } from "framer-motion";
import { StripeFiberBurst } from "./StripeFiberBurst";
import { useReducedMotion } from "@/hooks/useReducedMotion";

// GyanSetu Official Content (Default) & Stripe Benchmark Scale
const GYANSETU_METRICS = [
  {
    value: "45,000+",
    label: "statistical officers & cadre personnel nationwide",
  },
  {
    value: "99.98%",
    label: "competency diagnostics & IRT reliability index",
  },
  {
    value: "6 Sources",
    label: "continuous multimodal evidence fused in real-time",
  },
  {
    value: "100%",
    label: "explainable, audit-proof intervention recommendations",
  },
];

export function SocialProofSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="social-proof"
      className="relative h-screen pb-0 px-4 sm:px-6 md:px-8 overflow-hidden text-white"
      style={{
        background: "linear-gradient(180deg, #13143e 0%, #0f1035 50%, #090a24 100%)",
      }}
    >
      {/* Background Subtle Radial Indigo Sheen */}
      <div
        className="absolute inset-0 pointer-events-none opacity-40"
        style={{
          background:
            "radial-gradient(circle at 50% 15%, rgba(99, 102, 241, 0.2) 0%, rgba(37, 99, 235, 0.08) 45%, transparent 75%)",
        }}
      />

      <div className="relative max-w-7xl mx-auto text-center z-10 flex flex-col h-full pt-16 sm:pt-20 md:pt-24">
        {/* ========================================================================= */}
        {/* COMPACT HEADLINE (Clean Sans-Serif Mixed Case matching Stripe) */}
        {/* ========================================================================= */}
        <motion.div
          initial={shouldReduceMotion ? false : { y: 15, opacity: 0 }}
          whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.5 }}
          className="max-w-4xl mx-auto mb-8 md:mb-12"
        >
          <h2 className="font-body text-4xl sm:text-5xl md:text-6xl font-bold text-white tracking-tight leading-[1.15]">
            The backbone
            <br />
            of India&apos;s statistical intelligence
          </h2>
        </motion.div>

        {/* ========================================================================= */}
        {/* HORIZONTAL DIVIDER */}
        {/* ========================================================================= */}
        <div className="relative w-full max-w-7xl mx-auto mb-8">
          <div className="h-[1px] w-full bg-white/15" />
          {/* Glowing Center Sheen */}
          <div className="absolute top-0 left-1/4 right-1/4 h-[1px] bg-gradient-to-r from-transparent via-blue-400 to-transparent shadow-[0_0_12px_rgba(147,197,253,0.85)]" />
        </div>

        {/* ========================================================================= */}
        {/* 4-COLUMN METRICS GRID */}
        {/* ========================================================================= */}
        <div className="relative max-w-7xl mx-auto mb-6 pb-8 border-b border-white/10">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6 md:gap-0 items-start text-left">
            {GYANSETU_METRICS.map((metric, idx) => (
              <div
                key={idx}
                className={`relative px-4 sm:px-6 md:px-8 ${
                  idx !== GYANSETU_METRICS.length - 1
                    ? "md:border-r md:border-white/10"
                    : ""
                }`}
              >
                <div className="font-body text-3xl sm:text-4xl lg:text-5xl font-bold text-white tracking-tight leading-none mb-2">
                  {metric.value}
                </div>
                <p className="font-body text-sm sm:text-base text-[#94A3B8] leading-snug max-w-[240px]">
                  {metric.label}
                </p>
              </div>
            ))}
          </div>
        </div>

        <div className="relative w-full flex-1 min-h-0">
          <StripeFiberBurst />
        </div>
      </div>
    </section>
  );
}
