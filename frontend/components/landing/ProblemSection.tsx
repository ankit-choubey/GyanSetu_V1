"use client";

import React from "react";
import { motion } from "framer-motion";
import {
  BookOpen,
  XCircle,
  AlertTriangle,
  MessageSquare,
  BarChart3,
  Equal,
  Lock,
  EyeOff,
  Zap,
} from "lucide-react";
import { SectionLabel } from "@/components/ui/SectionLabel";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { AnimatedCounter } from "@/components/ui/AnimatedCounter";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface ProblemItem {
  id: number;
  icon: React.ComponentType<{ className?: string }>;
  stat?: string;
  target?: number;
  suffix?: string;
  quote?: string;
  description: string;
  // Angular position on orbit: 60-degree increments
  angleDeg: number;
  // Offset from center in pixels (Stage is 960x640, Center at 480, 320)
  offsetX: number;
  offsetY: number;
  floatDelay: number;
}

// 6 Orbiting Cards placed at equal distance & equal 60-degree angles around center (480, 320)
const PROBLEM_ITEMS: ProblemItem[] = [
  {
    id: 1,
    icon: MessageSquare,
    quote: '"I passed 14 courses but can\'t sample."',
    description: "Theoretical completion without execution capability",
    angleDeg: 210, // Top-Left
    offsetX: -340,
    offsetY: -160,
    floatDelay: 0,
  },
  {
    id: 2,
    icon: BarChart3,
    target: 73,
    suffix: "%",
    description: "courses completed, gaps unmeasured",
    angleDeg: 270, // Top-Center
    offsetX: 0,
    offsetY: -225,
    floatDelay: 1.2,
  },
  {
    id: 3,
    icon: AlertTriangle,
    target: 0,
    suffix: "",
    description: "subskill gaps identified by legacy LMS",
    angleDeg: 330, // Top-Right
    offsetX: 340,
    offsetY: -160,
    floatDelay: 2.4,
  },
  {
    id: 4,
    icon: Equal,
    target: 100,
    suffix: "%",
    description: "same training for all statistical roles",
    angleDeg: 30, // Bottom-Right
    offsetX: 340,
    offsetY: 160,
    floatDelay: 0.8,
  },
  {
    id: 5,
    icon: Lock,
    target: 0,
    suffix: "",
    description: "retention checks performed post-training",
    angleDeg: 90, // Bottom-Center
    offsetX: 0,
    offsetY: 225,
    floatDelay: 2.0,
  },
  {
    id: 6,
    icon: EyeOff,
    target: 41,
    suffix: "%",
    description: "capability gaps unseen by direct supervisors",
    angleDeg: 150, // Bottom-Left
    offsetX: -340,
    offsetY: 160,
    floatDelay: 1.6,
  },
];

export function ProblemSection() {
  const shouldReduceMotion = useReducedMotion();

  // Center stage coordinates
  const centerX = 480;
  const centerY = 320;

  return (
    <section
      id="problem"
      className="relative py-24 md:py-32 px-6 bg-[#F8FAFC] border-y border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header with Staggered Viewport Fade-In */}
        <motion.div
          initial={shouldReduceMotion ? false : { opacity: 0, y: 25 }}
          whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
          viewport={{ once: true, amount: 0.3 }}
          transition={{ duration: 0.6, ease: "easeOut" }}
        >
          <SectionLabel number="02" text="THE PROBLEM" />
          <SectionHeading
            title="COMPLETION ≠ COMPETENCY"
            subtitle="Legacy training portals track viewing time and course completions, while critical field execution gaps remain entirely undetected."
          />
        </motion.div>

        {/* ========================================================================= */}
        {/* DESKTOP RADIAL STAGE (lg: >= 1024px) */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative w-[960px] h-[640px] mx-auto my-8 select-none">
          {/* 1. SVG Dynamic Connector Lines & Moving Energy Beams */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none z-0"
            viewBox="0 0 960 640"
          >
            <defs>
              {/* Radial gradient for connector lines */}
              <linearGradient id="beamGradient" x1="0%" y1="0%" x2="100%" y2="100%">
                <stop offset="0%" stopColor="#3B82F6" stopOpacity="0.8" />
                <stop offset="60%" stopColor="#93C5FD" stopOpacity="0.5" />
                <stop offset="100%" stopColor="#CBD5E1" stopOpacity="0.2" />
              </linearGradient>

              {/* Glowing dot filter */}
              <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">
                <feGaussianBlur stdDeviation="2" result="blur" />
                <feComposite in="SourceGraphic" in2="blur" operator="over" />
              </filter>
            </defs>

            {/* Orbit guideline circles */}
            <circle
              cx={centerX}
              cy={centerY}
              r="225"
              fill="none"
              stroke="#E2E8F0"
              strokeWidth="1"
              strokeDasharray="6 6"
              className="opacity-70"
            />
            <circle
              cx={centerX}
              cy={centerY}
              r="375"
              fill="none"
              stroke="#F1F5F9"
              strokeWidth="1"
              strokeDasharray="4 8"
            />

            {/* Connecting lines from Center (480, 320) to each card center */}
            {PROBLEM_ITEMS.map((item) => {
              const targetX = centerX + item.offsetX;
              const targetY = centerY + item.offsetY;

              return (
                <g key={item.id}>
                  {/* Dashed connector line */}
                  <motion.line
                    initial={
                      shouldReduceMotion
                        ? false
                        : { pathLength: 0, opacity: 0 }
                    }
                    whileInView={
                      shouldReduceMotion
                        ? {}
                        : { pathLength: 1, opacity: 1 }
                    }
                    viewport={{ once: true, amount: 0.3 }}
                    transition={{
                      duration: 0.8,
                      delay: 0.2 + item.id * 0.1,
                      ease: "easeOut",
                    }}
                    x1={centerX}
                    y1={centerY}
                    x2={targetX}
                    y2={targetY}
                    stroke="url(#beamGradient)"
                    strokeWidth="1.75"
                    strokeDasharray="5 5"
                  />

                  {/* Animated Traveling Pulse along the connector line */}
                  {!shouldReduceMotion && (
                    <circle r="3.5" fill="#3B82F6" filter="url(#glow)">
                      <animateMotion
                        path={`M ${centerX} ${centerY} L ${targetX} ${targetY}`}
                        dur={`${3 + (item.id % 3)}s`}
                        repeatCount="indefinite"
                        begin={`${item.floatDelay}s`}
                      />
                    </circle>
                  )}
                </g>
              );
            })}
          </svg>

          {/* 2. CENTRAL ANIMATED COMPONENT (The Hub) */}
          <motion.div
            initial={
              shouldReduceMotion
                ? false
                : { scale: 0.5, opacity: 0 }
            }
            whileInView={
              shouldReduceMotion
                ? {}
                : { scale: 1, opacity: 1 }
            }
            viewport={{ once: true, amount: 0.3 }}
            transition={{
              type: "spring",
              stiffness: 160,
              damping: 18,
              duration: 0.8,
            }}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[280px] h-[280px] z-10 flex items-center justify-center pointer-events-auto"
          >
            {/* Ambient Pulsing Glow Halo */}
            <div className="absolute w-[240px] h-[240px] rounded-full bg-blue-400/20 blur-2xl animate-pulse pointer-events-none" />

            {/* Expanding Radar Wave Ring */}
            {!shouldReduceMotion && (
              <motion.div
                animate={{
                  scale: [1, 1.7, 2.1],
                  opacity: [0.6, 0.2, 0],
                }}
                transition={{
                  duration: 3.5,
                  repeat: Infinity,
                  ease: "easeOut",
                }}
                className="absolute w-[140px] h-[140px] rounded-full border border-blue-400/50 pointer-events-none"
              />
            )}

            {/* Outer Spinning Dashed Orbit Ring */}
            <motion.div
              animate={
                shouldReduceMotion
                  ? {}
                  : { rotate: 360 }
              }
              transition={{
                duration: 28,
                repeat: Infinity,
                ease: "linear",
              }}
              className="absolute w-[240px] h-[240px] rounded-full border-2 border-dashed border-blue-300/70"
            >
              {/* Satellite beads on ring */}
              <div className="absolute top-0 left-1/2 -translate-x-1/2 -translate-y-1/2 w-3 h-3 rounded-full bg-blue-500 shadow-[0_0_10px_#3B82F6]" />
              <div className="absolute bottom-0 left-1/2 -translate-x-1/2 translate-y-1/2 w-2.5 h-2.5 rounded-full bg-rose-400 shadow-[0_0_8px_#FB7185]" />
            </motion.div>

            {/* Counter-Rotating Middle Ring */}
            <motion.div
              animate={
                shouldReduceMotion
                  ? {}
                  : { rotate: -360 }
              }
              transition={{
                duration: 38,
                repeat: Infinity,
                ease: "linear",
              }}
              className="absolute w-[190px] h-[190px] rounded-full border border-indigo-200/60"
            >
              <div className="absolute top-1/2 right-0 translate-x-1/2 -translate-y-1/2 w-2 h-2 rounded-full bg-teal-400 shadow-[0_0_6px_#2DD4BF]" />
            </motion.div>

            {/* Floating Central Core Sphere */}
            <motion.div
              animate={
                shouldReduceMotion
                  ? {}
                  : {
                      y: [-6, 6, -6],
                    }
              }
              transition={{
                duration: 4.5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
              className="relative z-10 w-[140px] h-[140px] rounded-full bg-gradient-to-br from-white via-blue-50/90 to-blue-100 border-2 border-blue-300 shadow-[0_10px_35px_rgba(59,130,246,0.25)] flex flex-col items-center justify-center p-3"
            >
              {/* Overlaid Animated Warning Badges */}
              <motion.div
                animate={shouldReduceMotion ? {} : { scale: [1, 1.15, 1] }}
                transition={{ duration: 2.2, repeat: Infinity, ease: "easeInOut" }}
                className="absolute -top-1 -right-1 text-[#FB7185] bg-white rounded-full p-1 shadow-md border border-rose-100"
                title="Capability Deficit"
              >
                <XCircle className="w-6 h-6 fill-[#FFF1F2]" />
              </motion.div>
              <motion.div
                animate={shouldReduceMotion ? {} : { scale: [1, 1.12, 1] }}
                transition={{ duration: 2.8, repeat: Infinity, ease: "easeInOut", delay: 1 }}
                className="absolute -bottom-1 -left-1 text-amber-500 bg-white rounded-full p-1 shadow-md border border-amber-100"
                title="Unmeasured Competency"
              >
                <AlertTriangle className="w-5 h-5 fill-[#FEF3C7]" />
              </motion.div>

              {/* Center Core Content */}
              <div className="w-10 h-10 rounded-full bg-blue-100/80 flex items-center justify-center mb-1 text-blue-600">
                <BookOpen className="w-5 h-5" />
              </div>
              <span className="font-heading text-lg tracking-wider text-slate-900 leading-none">
                LEGACY LMS
              </span>
              <span className="font-mono text-[9px] font-semibold text-rose-600 uppercase tracking-widest mt-1">
                COMPLETION GAP
              </span>
            </motion.div>
          </motion.div>

          {/* 3. 6 SATELLITE PROBLEM CARDS (EQUAL DISTANCE RADIAL ORBIT) */}
          {PROBLEM_ITEMS.map((item, index) => {
            const Icon = item.icon;
            const targetX = centerX + item.offsetX;
            const targetY = centerY + item.offsetY;

            return (
              <motion.div
                key={item.id}
                initial={
                  shouldReduceMotion
                    ? false
                    : {
                        opacity: 0,
                        scale: 0.7,
                        x: item.offsetX * 0.4,
                        y: item.offsetY * 0.4,
                      }
                }
                whileInView={
                  shouldReduceMotion
                    ? {}
                    : {
                        opacity: 1,
                        scale: 1,
                        x: 0,
                        y: 0,
                      }
                }
                viewport={{ once: true, amount: 0.3 }}
                transition={{
                  duration: 0.65,
                  delay: 0.15 + index * 0.12,
                  type: "spring",
                  damping: 18,
                  stiffness: 140,
                }}
                className="absolute w-[210px] z-20"
                style={{
                  left: `${targetX}px`,
                  top: `${targetY}px`,
                  transform: "translate(-50%, -50%)",
                }}
              >
                {/* Continuous gentle floating motion */}
                <motion.div
                  animate={
                    shouldReduceMotion
                      ? {}
                      : {
                          y: [-4, 4, -4],
                        }
                  }
                  transition={{
                    duration: 4 + (index % 3),
                    repeat: Infinity,
                    ease: "easeInOut",
                    delay: item.floatDelay,
                  }}
                  className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-[0_4px_20px_rgba(15,23,42,0.06)] hover:shadow-[0_8px_28px_rgba(59,130,246,0.15)] hover:border-[#BFDBFE] transition-all duration-300 group"
                >
                  {/* Card Header: Icon + Metric */}
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="p-2 rounded-xl bg-blue-50 text-blue-600 group-hover:bg-blue-600 group-hover:text-white transition-colors duration-200">
                      <Icon className="w-4 h-4" />
                    </div>

                    {item.target !== undefined && (
                      <span className="font-heading text-3xl text-blue-600 leading-none">
                        <AnimatedCounter
                          target={item.target}
                          suffix={item.suffix}
                        />
                      </span>
                    )}
                  </div>

                  {/* Quote or Primary Heading */}
                  {item.quote && (
                    <p className="font-body text-xs font-semibold text-slate-900 leading-snug mb-1">
                      {item.quote}
                    </p>
                  )}

                  {/* Description */}
                  <p className="font-body text-[11px] text-slate-500 leading-relaxed">
                    {item.description}
                  </p>
                </motion.div>
              </motion.div>
            );
          })}
        </div>

        {/* ========================================================================= */}
        {/* MOBILE & TABLET FALLBACK (< 1024px) */}
        {/* ========================================================================= */}
        <div className="lg:hidden flex flex-col items-center mt-8">
          {/* Animated Center Hub for Mobile */}
          <motion.div
            initial={shouldReduceMotion ? false : { scale: 0.8, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
            viewport={{ once: true, amount: 0.3 }}
            className="relative w-[200px] h-[200px] mb-8 flex items-center justify-center"
          >
            {/* Pulsing ring */}
            <div className="absolute w-[180px] h-[180px] rounded-full bg-blue-400/15 blur-xl animate-pulse" />
            <motion.div
              animate={shouldReduceMotion ? {} : { rotate: 360 }}
              transition={{ duration: 25, repeat: Infinity, ease: "linear" }}
              className="absolute inset-0 rounded-full border-2 border-dashed border-blue-300"
            />

            <div className="w-[110px] h-[110px] rounded-full bg-gradient-to-br from-white to-blue-50 border-2 border-blue-300 shadow-md flex flex-col items-center justify-center relative">
              <div className="absolute -top-1 -right-1 text-rose-500 bg-white rounded-full p-0.5 shadow">
                <XCircle className="w-5 h-5 fill-rose-50" />
              </div>
              <BookOpen className="w-6 h-6 text-blue-600 mb-1" />
              <span className="font-heading text-base text-slate-900 leading-none">
                LEGACY LMS
              </span>
              <span className="font-mono text-[8px] font-semibold text-rose-600 uppercase mt-0.5">
                COMPLETION GAP
              </span>
            </div>
          </motion.div>

          {/* Cards Grid: 1 col on mobile, 2 col on tablet with staggered fade-in */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-lg mx-auto">
            {PROBLEM_ITEMS.map((item, index) => {
              const Icon = item.icon;
              return (
                <motion.div
                  key={item.id}
                  initial={shouldReduceMotion ? false : { opacity: 0, y: 20 }}
                  whileInView={shouldReduceMotion ? {} : { opacity: 1, y: 0 }}
                  viewport={{ once: true, amount: 0.2 }}
                  transition={{ duration: 0.5, delay: index * 0.1 }}
                  className="bg-white border border-[#E2E8F0] rounded-[16px] p-4 text-left shadow-sm"
                >
                  <div className="flex items-center justify-between gap-2.5 mb-2">
                    <div className="p-2 rounded-lg bg-blue-50 text-blue-600">
                      <Icon className="w-4 h-4" />
                    </div>
                    {item.target !== undefined && (
                      <span className="font-heading text-2xl text-blue-600 leading-none">
                        <AnimatedCounter
                          target={item.target}
                          suffix={item.suffix}
                        />
                      </span>
                    )}
                  </div>
                  {item.quote && (
                    <p className="font-body text-xs font-semibold text-[#0F172A] mb-1">
                      {item.quote}
                    </p>
                  )}
                  <p className="font-body text-xs text-[#64748B]">
                    {item.description}
                  </p>
                </motion.div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
