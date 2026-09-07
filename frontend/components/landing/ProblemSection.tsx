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
      className="relative py-28 md:py-36 lg:py-44 px-4 sm:px-6 bg-[#FAFAFC] border-y border-[#E2E8F0] overflow-hidden"
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

      <div className="relative z-10 max-w-[1440px] mx-auto text-center">
        {/* Top Section Pill Badge */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: -10 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.4 }}
          className="inline-flex items-center gap-2 px-3.5 py-1.5 rounded-full bg-white border border-[#E2E8F0] shadow-2xs mb-4"
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
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, delay: 0.1 }}
          className="font-heading text-5xl sm:text-6xl md:text-[68px] text-[#0F172A] tracking-[0.02em] leading-tight mb-4 select-none"
        >
          COMPLETION ≠ COMPETENCY
        </motion.h2>

        {/* Subtitle */}
        <motion.p
          initial={shouldReduceMotion ? false : { opacity: 0, y: 15 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.05 }}
          transition={{ duration: 0.5, delay: 0.15 }}
          className="font-body text-base sm:text-lg text-[#475569] max-w-2xl mx-auto leading-relaxed mb-8 sm:mb-14"
        >
          Current civil service training platforms measure course attendance, not
          actual statistical proficiency or survey readiness in the field.
        </motion.p>

        {/* ========================================================================= */}
        {/* DESKTOP PIPELINE STAGE (lg: >= 1024px) — Expanded Canvas 1360 x 660 */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative w-[1360px] h-[660px] mx-auto select-none my-6 lg:scale-[0.9] xl:scale-100 origin-center transition-transform">
          {/* SVG Connector Lines Layer */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1 }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.6 }}
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
          >
          <svg
            className="w-full h-full"
            viewBox="0 0 1360 660"
          >
            <defs>
              <pattern
                id="dashFlow"
                width="12"
                height="12"
                patternUnits="userSpaceOnUse"
              />
            </defs>

            {/* Concentric Dashed Orbit Rings around Center (680, 330) */}
            {/* Outer dashed ring (radius 165) */}
            <circle
              cx="680"
              cy="330"
              r="165"
              fill="none"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-[spin_45s_linear_infinite] origin-[680px_330px]"}
            />
            {/* Inner faint ring (radius 115) */}
            <circle
              cx="680"
              cy="330"
              r="115"
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
              strokeDasharray="4 4"
            />

            {/* Red alert arc segment on top-right of outer ring */}
            <path
              d="M 775 195 A 165 165 0 0 1 815 235"
              fill="none"
              stroke="#FB7185"
              strokeWidth="2"
              strokeDasharray="4 4"
            />

            {/* 6 Straight Dashed Connector Lines from outer ring to cards with SVG flow */}
            {/* 1. Top-Left diagonal line to Card 1 */}
            <line
              x1="347"
              y1="115"
              x2="541"
              y2="240"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 2. Middle-Left horizontal line with terminal dot to Card 2 */}
            <line
              x1="292"
              y1="330"
              x2="515"
              y2="330"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
            <circle cx="292" cy="330" r="3.5" fill="#94A3B8" />

            {/* 3. Bottom-Left diagonal line cleanly anchoring to Alert badge */}
            <line
              x1="347"
              y1="545"
              x2="548"
              y2="454"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 4. Top-Right diagonal line cleanly anchoring to Disconnect (X) badge */}
            <line
              x1="1013"
              y1="115"
              x2="812"
              y2="206"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />

            {/* 5. Middle-Right horizontal line with terminal dot to Card 5 */}
            <line
              x1="1068"
              y1="330"
              x2="845"
              y2="330"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
            <circle cx="1068" cy="330" r="3.5" fill="#94A3B8" />

            {/* 6. Bottom-Right diagonal line to Card 6 */}
            <line
              x1="1013"
              y1="545"
              x2="819"
              y2="420"
              stroke="#CBD5E1"
              strokeWidth="1.5"
              strokeDasharray="5 5"
              className={shouldReduceMotion ? "" : "animate-dash-flow"}
            />
          </svg>
          </motion.div>

          {/* ========================================== */}
          {/* CENTER COMPONENT (Training Hub + Badges)   */}
          {/* ========================================== */}
          {/* Outer static positioning wrapper prevents Framer Motion transform overwrite */}
          <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[330px] h-[330px] flex items-center justify-center z-10 pointer-events-none">
            <motion.div
              initial={shouldReduceMotion ? false : { scale: 0.85, opacity: 0 }}
              whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
              viewport={{ once: true, amount: 0.05 }}
              transition={{ duration: 0.5, ease: "easeOut" }}
              className="relative w-full h-full flex items-center justify-center pointer-events-auto"
            >
              {/* Circular Training Hub Core */}
              <div className="w-[136px] h-[136px] rounded-full bg-[#EFF6FF] border-2 border-[#BFDBFE] flex flex-col items-center justify-center shadow-md shadow-blue-500/10">
                <BookOpen className="w-10 h-10 text-[#3B82F6] mb-1.5 stroke-[1.75]" />
                <span className="font-mono text-[10.5px] font-bold text-[#3B82F6] tracking-wider uppercase">
                  TRAINING HUB
                </span>
              </div>

              {/* Floating Top-Right (X) Disconnect Badge on outer ring (exact 45deg node) */}
              <div
                className="absolute bg-white rounded-full p-1 border border-rose-300 shadow-md text-rose-500 z-20"
                style={{ top: "32px", right: "32px" }}
                title="Pipeline Disconnect"
              >
                <div className="w-6 h-6 rounded-full bg-rose-50 border border-rose-400 flex items-center justify-center">
                  <X className="w-3.5 h-3.5 stroke-[2.5] text-rose-600" />
                </div>
              </div>

              {/* Floating Bottom-Left (!) Alert Badge on outer ring (exact 225deg node) */}
              <div
                className="absolute bg-white rounded-full p-1 border border-rose-300 shadow-md text-rose-500 z-20"
                style={{ bottom: "32px", left: "32px" }}
                title="Unmeasured Gaps"
              >
                <div className="w-6 h-6 rounded-full bg-rose-50 border border-rose-400 flex items-center justify-center">
                  <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5] text-rose-600" />
                </div>
              </div>
            </motion.div>
          </div>

          {/* Status Badge below Center Hub cleanly outside the ring */}
          <div className="absolute left-1/2 -translate-x-1/2 z-10" style={{ top: "515px" }}>
            <span className="inline-block font-mono text-[11px] uppercase tracking-wider text-slate-500 bg-white/95 backdrop-blur-xs px-4 py-1.5 rounded-md border border-[#E2E8F0] shadow-xs">
              STATUS: UNCONNECTED PIPELINE
            </span>
          </div>

          {/* ========================================== */}
          {/* THE 6 SATELLITE CARDS (Proper Proportions) */}
          {/* ========================================== */}

          {/* CARD 1: TOP-LEFT — CADRE OFFICER QUOTE */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-blue-200 transition-all z-20 cursor-default"
            style={{ left: "135px", top: "60px" }}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                <MessageSquare className="w-3.5 h-3.5" />
              </div>
              <span className="font-mono text-[10px] font-bold text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded-full uppercase">
                14 COURSES
              </span>
            </div>
            <p className="font-body text-xs font-semibold text-[#0F172A] leading-snug mb-1">
              “I passed 14 courses but can’t sample.”
            </p>
            <p className="font-body text-[10.5px] text-[#64748B] leading-tight">
              Cadre officer field audit
            </p>
          </motion.div>

          {/* CARD 2: MIDDLE-LEFT — 0 SUBSKILL GAPS */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.15 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-rose-200 transition-all z-20 cursor-default"
            style={{ left: "80px", top: "275px" }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
                <AlertTriangle className="w-4 h-4" />
              </div>
              <span className="font-heading text-3xl font-bold text-[#EF4444] leading-none">
                0
              </span>
            </div>
            <p className="font-body text-xs text-[#475569] leading-snug">
              subskill gaps identified by iGOT
            </p>
          </motion.div>

          {/* CARD 3: BOTTOM-LEFT — 0 RETENTION CHECKS */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: -20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-blue-200 transition-all z-20 cursor-default"
            style={{ left: "135px", top: "490px" }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                <Lock className="w-4 h-4" />
              </div>
              <span className="font-heading text-3xl font-bold text-[#2563EB] leading-none">
                0
              </span>
            </div>
            <p className="font-body text-xs text-[#475569] leading-snug">
              retention checks performed
            </p>
          </motion.div>

          {/* CARD 4: TOP-RIGHT — 73% COURSES COMPLETED */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.1 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-blue-200 transition-all z-20 cursor-default"
            style={{ right: "135px", top: "60px" }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                <BarChart3 className="w-4 h-4" />
              </div>
              <span className="font-heading text-3xl font-bold text-[#2563EB] leading-none">
                <AnimatedCounter target={73} suffix="%" />
              </span>
            </div>
            <p className="font-body text-xs text-[#475569] leading-snug">
              courses completed, gaps unmeasured
            </p>
          </motion.div>

          {/* CARD 5: MIDDLE-RIGHT — 100% SAME TRAINING */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.15 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-amber-200 transition-all z-20 cursor-default"
            style={{ right: "80px", top: "275px" }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center">
                <Equal className="w-4 h-4" />
              </div>
              <span className="font-heading text-3xl font-bold text-[#D97706] leading-none">
                <AnimatedCounter target={100} suffix="%" />
              </span>
            </div>
            <p className="font-body text-xs text-[#475569] leading-snug">
              same training for all roles
            </p>
          </motion.div>

          {/* CARD 6: BOTTOM-RIGHT — 41% CAPABILITY GAPS */}
          <motion.div
            initial={shouldReduceMotion ? false : { opacity: 0, x: 20 }}
            whileInView={shouldReduceMotion ? {} : { opacity: 1, x: 0 }}
            whileHover={shouldReduceMotion ? {} : { y: -3, transition: { duration: 0.2 } }}
            viewport={{ once: true, amount: 0.05 }}
            transition={{ duration: 0.45, delay: 0.2 }}
            className="absolute w-[212px] bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.05)] hover:shadow-md hover:border-rose-200 transition-all z-20 cursor-default"
            style={{ right: "135px", top: "490px" }}
          >
            <div className="flex items-center gap-2.5 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
                <EyeOff className="w-4 h-4" />
              </div>
              <span className="font-heading text-3xl font-bold text-[#EF4444] leading-none">
                <AnimatedCounter target={41} suffix="%" />
              </span>
            </div>
            <p className="font-body text-xs text-[#475569] leading-snug">
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
              <div className="flex items-center justify-between mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                  <MessageSquare className="w-3.5 h-3.5" />
                </div>
                <span className="font-mono text-[10px] font-bold text-[#2563EB] bg-[#EFF6FF] px-2 py-0.5 rounded-full uppercase">
                  14 COURSES
                </span>
              </div>
              <p className="font-body text-xs font-semibold text-[#0F172A] leading-snug mb-1">
                “I passed 14 courses but can’t sample.”
              </p>
              <p className="font-body text-[10.5px] text-[#64748B]">
                Cadre officer field audit
              </p>
            </div>

            {/* Card 2 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
                  <AlertTriangle className="w-4 h-4" />
                </div>
                <span className="font-heading text-2xl font-bold text-[#EF4444] leading-none">
                  0
                </span>
              </div>
              <p className="font-body text-xs text-[#64748B]">
                subskill gaps identified by iGOT
              </p>
            </div>

            {/* Card 3 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                  <Lock className="w-4 h-4" />
                </div>
                <span className="font-heading text-2xl font-bold text-[#2563EB] leading-none">
                  0
                </span>
              </div>
              <p className="font-body text-xs text-[#64748B]">
                retention checks performed
              </p>
            </div>

            {/* Card 4 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#EFF6FF] text-[#2563EB] flex items-center justify-center">
                  <BarChart3 className="w-4 h-4" />
                </div>
                <span className="font-heading text-2xl font-bold text-[#2563EB] leading-none">
                  <AnimatedCounter target={73} suffix="%" />
                </span>
              </div>
              <p className="font-body text-xs text-[#64748B]">
                courses completed, gaps unmeasured
              </p>
            </div>

            {/* Card 5 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#FEF3C7] text-[#D97706] flex items-center justify-center">
                  <Equal className="w-4 h-4" />
                </div>
                <span className="font-heading text-2xl font-bold text-[#D97706] leading-none">
                  <AnimatedCounter target={100} suffix="%" />
                </span>
              </div>
              <p className="font-body text-xs text-[#64748B]">
                same training for all roles
              </p>
            </div>

            {/* Card 6 */}
            <div className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-xs">
              <div className="flex items-center gap-2.5 mb-2">
                <div className="w-7 h-7 rounded-lg bg-[#FEE2E2] text-[#EF4444] flex items-center justify-center">
                  <EyeOff className="w-4 h-4" />
                </div>
                <span className="font-heading text-2xl font-bold text-[#EF4444] leading-none">
                  <AnimatedCounter target={41} suffix="%" />
                </span>
              </div>
              <p className="font-body text-xs text-[#64748B]">
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
