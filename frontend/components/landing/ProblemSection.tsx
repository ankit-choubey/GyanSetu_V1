"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  X,
  AlertTriangle,
  MessageSquare,
  Equal,
  Lock,
  EyeOff,
  BarChart3,
} from "lucide-react";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function ProblemSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="problem"
      className="relative py-20 md:py-28 px-4 sm:px-6 bg-[#FAFAFC] border-y border-[#E2E8F0] overflow-hidden"
    >
      {/* Blueprint Grid Background matching reference design */}
      <div
        className="absolute inset-0 pointer-events-none opacity-60"
        style={{
          backgroundImage: `
            linear-gradient(to right, rgba(226, 232, 240, 0.6) 1px, transparent 1px),
            linear-gradient(to bottom, rgba(226, 232, 240, 0.6) 1px, transparent 1px)
          `,
          backgroundSize: "36px 36px",
        }}
      />

      <div className="relative z-10 max-w-[1240px] mx-auto text-center">
        {/* Top Section Pill Badge */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -10 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#E2E8F0] shadow-2xs mb-4"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-rose-500" />
          <span className="font-mono text-xs text-slate-500 tracking-wider">
            [ 02 ] THE PROBLEM
          </span>
        </motion.div>

        {/* Section Headline */}
        <motion.h2
          initial={shouldReduceMotion ? false : { opacity: 0, y: 15 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="font-heading text-4xl sm:text-5xl md:text-[56px] text-[#0F172A] tracking-[0.02em] leading-tight mb-3 select-none"
        >
          COMPLETION ≠ COMPETENCY
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 15 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="font-body text-sm sm:text-base text-[#475569] max-w-xl mx-auto leading-relaxed mb-6 sm:mb-12"
        >
          Current civil service training platforms measure course attendance, not
          actual statistical proficiency or survey readiness in the field.
        </motion.p>

        {/* ========================================================================= */}
        {/* DESKTOP PIPELINE STAGE (lg: >= 1024px) */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative w-[1080px] h-[520px] mx-auto select-none my-4">
          {/* SVG Connector Lines Layer */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
            viewBox="0 0 1080 520"
          >
            <defs>
              <pattern
                id="dashFlow"
                width="12"
                height="12"
                patternUnits="userSpaceOnUse"
              />
            </defs>

            {/* Concentric Dashed Orbit Rings around Center (540, 260) */}
            {/* Outer dashed ring */}
            <circle
              cx="540"
              cy="260"
              r="125"
              fill="none"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-[spin_45s_linear_infinite] origin-[540px_260px]"}
            />
            {/* Inner faint ring */}
            <circle
              cx="540"
              cy="260"
              r="85"
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
              strokeDasharray="4 4"
            />

            {/* Red alert arc segment on top-right of outer ring */}
            <path
              d="M 628 171 A 125 125 0 0 1 656 220"
              fill="none"
              stroke="#FB7185"
              strokeWidth="1.75"
              strokeDasharray="4 4"
            />

            {/* 6 Straight Dashed Connector Lines from outer ring to cards with SVG flow */}
            {/* 1. Top-Left diagonal line */}
            <line
              x1="320"
              y1="130"
              x2="451"
              y2="172"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 2. Middle-Left horizontal line with terminal dot */}
            <line
              x1="290"
              y1="260"
              x2="415"
              y2="260"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
            <circle cx="298" cy="260" r="3" fill="#94A3B8" />

            {/* 3. Bottom-Left diagonal line */}
            <line
              x1="330"
              y1="390"
              x2="451"
              y2="348"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 4. Top-Right diagonal line */}
            <line
              x1="760"
              y1="130"
              x2="628"
              y2="172"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 5. Middle-Right horizontal line with terminal dot */}
            <line
              x1="790"
              y1="260"
              x2="665"
              y2="260"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
            <circle cx="782" cy="260" r="3" fill="#94A3B8" />

            {/* 6. Bottom-Right diagonal line */}
            <line
              x1="750"
              y1="390"
              x2="628"
              y2="348"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
          </svg>

          {/* ========================================== */}
          {/* CENTER COMPONENT (Training Hub + Badges)   */}
          {/* ========================================== */}
          <motion.div
            initial={shouldReduceMotion ? false : { scale: 0.85, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.5, ease: "easeOut" }}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[250px] h-[250px] flex items-center justify-center z-10"
          >
            {/* Circular Training Hub Core */}
            <div className="w-[102px] h-[102px] rounded-full bg-[#EFF6FF] border border-[#BFDBFE] flex flex-col items-center justify-center shadow-xs">
              <BookOpen className="w-8 h-8 text-[#3B82F6] mb-1 stroke-[1.75]" />
              <span className="font-mono text-[9px] font-bold text-[#3B82F6] tracking-wider uppercase">
                TRAINING HUB
              </span>
            </div>

            {/* Floating Top-Right (X) Badge on outer ring */}
            <div
              className="absolute bg-white rounded-full p-1 border border-rose-200 shadow-2xs text-rose-500"
              style={{ top: "34px", right: "42px" }}
              title="Pipeline Disconnect"
            >
              <div className="w-5 h-5 rounded-full border border-rose-400 flex items-center justify-center">
                <X className="w-3.5 h-3.5 stroke-[2.5]" />
              </div>
            </div>

            {/* Floating Bottom-Left (!) Badge on outer ring */}
            <div
              className="absolute bg-white rounded-full p-1 border border-rose-200 shadow-2xs text-rose-500"
              style={{ bottom: "42px", left: "38px" }}
              title="Unmeasured Gaps"
            >
              <div className="w-5 h-5 rounded-full flex items-center justify-center">
                <AlertTriangle className="w-4 h-4 stroke-[2.2]" />
              </div>
            </div>
          </motion.div>

          {/* Status Badge below Center Hub */}
          <div className="absolute left-1/2 -translate-x-1/2 z-10" style={{ top: "374px" }}>
            <span className="inline-block font-mono text-[10px] uppercase tracking-wider text-slate-400 bg-white/90 backdrop-blur-xs px-3 py-1 rounded-md border border-[#E2E8F0] shadow-2xs">
              STATUS: UNCONNECTED PIPELINE
            </span>
          </div>

          {/* ========================================== */}
          {/* THE 6 SATELLITE CARDS                      */}
          {/* ========================================== */}

          {/* CARD 1: TOP-LEFT — CADRE 14 COURSES */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ left: "115px", top: "45px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2.5">
              <MessageSquare className="w-3.5 h-3.5" />
            </div>
            <div className="font-body text-xs font-bold text-[#0F172A] mb-1">
              CADRE{" "}
              <span className="text-[#3B82F6] font-bold">14 COURSES</span>
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              “I passed 14 courses but can’t sample.”
            </p>
          </motion.div>

          {/* CARD 2: MIDDLE-LEFT — 0 SUBSKILL GAPS IDENTIFIED */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.15 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ left: "85px", top: "195px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#FEE2E2] text-rose-500 flex items-center justify-center mb-2">
              <AlertTriangle className="w-3.5 h-3.5" />
            </div>
            <div className="font-heading text-3xl font-bold text-[#2563EB] leading-none mb-1">
              0
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              subskill gaps identified by iGOT
            </p>
          </motion.div>

          {/* CARD 3: BOTTOM-LEFT — 0 RETENTION CHECKS */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ left: "125px", top: "340px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
              <Lock className="w-3.5 h-3.5" />
            </div>
            <div className="font-heading text-3xl font-bold text-[#2563EB] leading-none mb-1">
              0
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              retention checks performed
            </p>
          </motion.div>

          {/* CARD 4: TOP-RIGHT — 73% COURSES COMPLETED */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ right: "115px", top: "45px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
              <BarChart3 className="w-3.5 h-3.5" />
            </div>
            <div className="font-heading text-3xl font-bold text-[#2563EB] leading-none mb-1">
              <AnimatedCounter target={73} suffix="%" />
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              courses completed, gaps unmeasured
            </p>
          </motion.div>

          {/* CARD 5: MIDDLE-RIGHT — 100% SAME TRAINING */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.15 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ right: "85px", top: "195px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
              <Equal className="w-3.5 h-3.5" />
            </div>
            <div className="font-heading text-3xl font-bold text-[#2563EB] leading-none mb-1">
              <AnimatedCounter target={100} suffix="%" />
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              same training for all roles
            </p>
          </motion.div>

          {/* CARD 6: BOTTOM-RIGHT — 41% CAPABILITY GAPS */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            className="absolute w-[205px] bg-white border border-[#E2E8F0] rounded-[18px] p-4 text-left shadow-[0_4px_20px_rgba(0,0,0,0.04)] hover:shadow-md transition-shadow z-20"
            style={{ right: "125px", top: "340px" }}
          >
            <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
              <EyeOff className="w-3.5 h-3.5" />
            </div>
            <div className="font-heading text-3xl font-bold text-[#2563EB] leading-none mb-1">
              <AnimatedCounter target={41} suffix="%" />
            </div>
            <p className="font-body text-[11px] text-[#64748B] leading-snug">
              capability gaps unseen by directors
            </p>
          </motion.div>
        </div>

        {/* ========================================================================= */}
        {/* MOBILE & TABLET STACK (< 1024px) */}
        {/* ========================================================================= */}
        <div className="lg:hidden flex flex-col items-center mt-6">
          {/* Center Hub Graphic */}
          <div className="relative w-[180px] h-[180px] mb-8 flex items-center justify-center">
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 180 180">
              <circle
                cx="90"
                cy="90"
                r="70"
                fill="none"
                stroke="#CBD5E1"
                strokeWidth="1.5"
                strokeDasharray="4 4"
              />
            </svg>
            <div className="w-[84px] h-[84px] rounded-full bg-[#EFF6FF] border border-[#BFDBFE] flex flex-col items-center justify-center shadow-xs">
              <BookOpen className="w-6 h-6 text-[#3B82F6] mb-0.5" />
              <span className="font-mono text-[8px] font-bold text-[#3B82F6]">
                TRAINING HUB
              </span>
            </div>
          </div>

          {/* Cards Grid: 1 column on mobile, 2 columns on tablet */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5 w-full max-w-lg mx-auto mb-8">
            {/* Card 1 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
                <MessageSquare className="w-3.5 h-3.5" />
              </div>
              <div className="font-body text-xs font-bold text-[#0F172A] mb-1">
                CADRE <span className="text-[#3B82F6]">14 COURSES</span>
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                “I passed 14 courses but can’t sample.”
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
                <BarChart3 className="w-3.5 h-3.5" />
              </div>
              <div className="font-heading text-2xl font-bold text-[#2563EB] leading-none mb-1">
                <AnimatedCounter target={73} suffix="%" />
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                courses completed, gaps unmeasured
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#FEE2E2] text-rose-500 flex items-center justify-center mb-2">
                <AlertTriangle className="w-3.5 h-3.5" />
              </div>
              <div className="font-heading text-2xl font-bold text-[#2563EB] leading-none mb-1">
                0
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                subskill gaps identified by iGOT
              </p>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
                <Equal className="w-3.5 h-3.5" />
              </div>
              <div className="font-heading text-2xl font-bold text-[#2563EB] leading-none mb-1">
                <AnimatedCounter target={100} suffix="%" />
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                same training for all roles
              </p>
            </div>

            {/* Card 5 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
                <Lock className="w-3.5 h-3.5" />
              </div>
              <div className="font-heading text-2xl font-bold text-[#2563EB] leading-none mb-1">
                0
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                retention checks performed
              </p>
            </div>

            {/* Card 6 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="w-6 h-6 rounded-md bg-[#EFF6FF] text-[#3B82F6] flex items-center justify-center mb-2">
                <EyeOff className="w-3.5 h-3.5" />
              </div>
              <div className="font-heading text-2xl font-bold text-[#2563EB] leading-none mb-1">
                <AnimatedCounter target={41} suffix="%" />
              </div>
              <p className="font-body text-[11px] text-[#64748B]">
                capability gaps unseen by directors
              </p>
            </div>
          </div>
        </div>

        {/* Bottom Audit Strip matching reference design */}
        <div className="mt-8 pt-4 border-t border-[#E2E8F0] flex flex-col sm:flex-row items-center justify-between gap-2 text-[10px] sm:text-[11px] font-mono text-slate-400">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 inline-block" />
            <span className="uppercase tracking-wider">
              DIAGNOSTIC VECTOR: CADRE DEFICIENCY DISCONNECT
            </span>
          </div>
          <div className="uppercase tracking-wider">
            NSSO &amp; MOSPI TRAINING AUDIT REF // 2024-Q3 &nbsp;&nbsp; DATA_SOURCE: iGOT_KARMASHAALA
          </div>
        </div>
      </div>
    </section>
  );
}
