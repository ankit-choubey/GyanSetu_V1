"use client";

import React from "react";
import { motion } from "framer-motion";
import { Search, ShieldCheck } from "lucide-react";
import { GridOverlay } from "@/components/ui/GridOverlay";
import { DotPattern } from "@/components/ui/DotPattern";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function HeroSection() {
  const shouldReduceMotion = useReducedMotion();

  const headlineLines = [
    "IDENTIFY GAPS.",
    "TARGET INTERVENTIONS.",
    "PROVE LEARNING.",
  ];

  return (
    <section
      id="hero"
      className="relative min-h-screen pt-32 pb-24 px-6 flex items-center justify-center flex-col text-center overflow-hidden bg-white"
    >
      {/* Background Decorative Patterns */}
      <GridOverlay />
      <DotPattern />

      {/* Scoped Hero Content (Layered above z-0 at z-10 per §2.7) */}
      <div className="relative z-10 max-w-4xl mx-auto flex flex-col items-center">
        {/* Section Label */}
        <SectionLabel number="01" text="COMPETENCY INTELLIGENCE" />

        {/* 3-Line Bebas Neue Headline with Staggered Entrance */}
        <h1 className="font-heading text-5xl sm:text-7xl md:text-[80px] uppercase tracking-[0.02em] leading-[1.05] text-[#0F172A] mb-6 select-none">
          {headlineLines.map((line, idx) => (
            <motion.span
              key={line}
              className="block"
              initial={
                shouldReduceMotion
                  ? false
                  : { opacity: 0, y: 30, filter: "blur(12px)" }
              }
              animate={
                shouldReduceMotion
                  ? {}
                  : { opacity: 1, y: 0, filter: "blur(0px)" }
              }
              transition={{
                duration: 0.6,
                delay: 0.2 + idx * 0.18,
                ease: "easeOut",
              }}
            >
              {line}
            </motion.span>
          ))}
        </h1>

        {/* Subtitle */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
          animate={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.8, ease: "easeOut" }}
          className="font-body text-base sm:text-lg md:text-xl text-[#475569] max-w-2xl leading-relaxed mb-10"
        >
          GyanSetu uses AI-driven evidence fusion to identify, fix, and verify
          competency gaps in India&apos;s official statistical workforce.
        </motion.p>

        {/* Stylized Input Bar (Valley.co Pattern A §1.5) */}
        <motion.div
          initial={
            shouldReduceMotion ? false : { opacity: 0, scale: 0.95, y: 15 }
          }
          animate={shouldReduceMotion ? {} : { opacity: 1, scale: 1, y: 0 }}
          transition={{ duration: 0.45, delay: 1.0, ease: "easeOut" }}
          className="w-full max-w-md bg-white border border-[#CBD5E1] rounded-[12px] p-2 pl-4 flex items-center justify-between gap-3 shadow-[0_2px_8px_rgba(0,0,0,0.04)] hover:border-[#94A3B8] hover:shadow-[0_4px_16px_rgba(0,0,0,0.08)] transition-all duration-200 mb-8"
        >
          <div className="flex items-center gap-2.5 text-[#94A3B8] overflow-hidden">
            <Search className="w-4 h-4 shrink-0 text-[#94A3B8]" />
            <span className="font-body text-xs sm:text-sm text-[#94A3B8] truncate select-all">
              officer.sharma@mospi.gov.in
            </span>
          </div>

          <button
            type="button"
            className="shrink-0 bg-[#0F172A] hover:bg-[#1E293B] text-white font-body text-xs font-semibold px-4 py-2.5 rounded-[8px] transition-transform active:scale-95"
            onClick={() => {
              const el = document.getElementById("problem");
              el?.scrollIntoView({ behavior: "smooth" });
            }}
          >
            Find my gap
          </button>
        </motion.div>

        {/* Social Proof Line (Valley.co Pattern A / §2.9) */}
        {/* ILLUSTRATIVE — replace with measured value or remove before any public/demo/judge-facing use */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0 }}
          animate={shouldReduceMotion ? {} : { opacity: 1 }}
          transition={{ duration: 0.4, delay: 1.2 }}
          className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#F8FAFC] border border-[#E2E8F0]"
        >
          <span className="w-4 h-4 rounded-full bg-[#EFF6FF] flex items-center justify-center text-[#3B82F6]">
            <ShieldCheck className="w-3 h-3" />
          </span>
          <p className="font-body text-[11px] sm:text-xs font-semibold uppercase tracking-[0.06em] text-[#475569]">
            NSSTA IMPROVED{" "}
            <span className="text-[#3B82F6] font-bold">72%</span> TRAINING
            RESULTS
          </p>
        </motion.div>
      </div>
    </section>
  );
}
