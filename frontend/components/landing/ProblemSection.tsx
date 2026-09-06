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
  desktopCoords: { left: string; top: string };
  floatDelay: string;
}

const PROBLEM_ITEMS: ProblemItem[] = [
  {
    id: 1,
    icon: MessageSquare,
    quote: '"I passed 14 courses but can\'t sample."',
    description: "Theoretical completion without execution capability",
    desktopCoords: { left: "12%", top: "18%" },
    floatDelay: "0s",
  },
  {
    id: 2,
    icon: BarChart3,
    target: 73,
    suffix: "%",
    description: "courses completed, gaps unmeasured",
    desktopCoords: { left: "88%", top: "18%" },
    floatDelay: "1s",
  },
  {
    id: 3,
    icon: AlertTriangle,
    target: 0,
    suffix: "",
    description: "subskill gaps identified by legacy LMS",
    desktopCoords: { left: "6%", top: "50%" },
    floatDelay: "2s",
  },
  {
    id: 4,
    icon: Equal,
    target: 100,
    suffix: "%",
    description: "same training for all statistical roles",
    desktopCoords: { left: "94%", top: "50%" },
    floatDelay: "1.5s",
  },
  {
    id: 5,
    icon: Lock,
    target: 0,
    suffix: "",
    description: "retention checks performed post-training",
    desktopCoords: { left: "18%", top: "84%" },
    floatDelay: "0.5s",
  },
  {
    id: 6,
    icon: EyeOff,
    target: 41,
    suffix: "%",
    description: "capability gaps unseen by direct supervisors",
    desktopCoords: { left: "82%", top: "84%" },
    floatDelay: "2.5s",
  },
];

export function ProblemSection() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <section
      id="problem"
      className="relative py-24 md:py-32 px-6 bg-[#F8FAFC] border-y border-[#E2E8F0] overflow-x-clip"
    >
      <div className="max-w-[1280px] mx-auto text-center">
        {/* Section Header */}
        <SectionLabel number="02" text="THE PROBLEM" />
        <SectionHeading
          title="COMPLETION ≠ COMPETENCY"
          subtitle="Legacy training portals track viewing time and course completions, while critical field execution gaps remain entirely undetected."
        />

        {/* ========================================================================= */}
        {/* DESKTOP STAGE (lg: >= 1024px) — Central Graphic + Orbiting Dashed Nodes */}
        {/* ========================================================================= */}
        <div className="hidden lg:block relative w-[760px] h-[540px] mx-auto my-6">
          {/* Connector Lines (z-index: 1 per §2.7) */}
          <svg
            className="absolute inset-0 w-full h-full pointer-events-none z-1"
            viewBox="0 0 760 540"
          >
            {PROBLEM_ITEMS.map((item) => {
              // Convert percentages to approximate stage coordinates (center at 380, 270)
              const xTarget = (parseFloat(item.desktopCoords.left) / 100) * 760;
              const yTarget = (parseFloat(item.desktopCoords.top) / 100) * 540;
              return (
                <line
                  key={item.id}
                  x1="380"
                  y1="270"
                  x2={xTarget}
                  y2={yTarget}
                  stroke="#CBD5E1"
                  strokeWidth="1.5"
                  strokeDasharray="4 4"
                />
              );
            })}
          </svg>

          {/* Central Composed Hub Graphic (z-index: 10 per §2.7 & §3.3) */}
          <motion.div
            initial={shouldReduceMotion ? false : { scale: 0.8, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
            viewport={{ once: true, amount: 0.3 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-[280px] h-[280px] z-10 flex items-center justify-center select-none"
          >
            {/* Broken Loop Dashed SVG Ring */}
            <svg
              className="absolute inset-0 w-full h-full"
              viewBox="0 0 280 280"
            >
              {/* Dashed circular arc with intentional gap at top-right (270deg to 330deg) */}
              <path
                d="M 140 30 A 110 110 0 1 0 235 85"
                fill="none"
                stroke="#CBD5E1"
                strokeWidth="2.5"
                strokeDasharray="10 8"
              />
            </svg>

            {/* Overlaid Coral Status Badges */}
            <div className="absolute top-7 right-8 text-[#FB7185] bg-white rounded-full p-1 shadow-sm">
              <XCircle className="w-7 h-7 fill-[#FFF1F2]" />
            </div>
            <div className="absolute bottom-8 left-8 text-[#FB7185] bg-white rounded-full p-1 shadow-sm">
              <AlertTriangle className="w-6 h-6 fill-[#FFF1F2]" />
            </div>

            {/* Blue Center Core */}
            <div className="w-[120px] h-[120px] rounded-full bg-[#EFF6FF] border-2 border-[#DBEAFE] flex flex-col items-center justify-center shadow-inner">
              <BookOpen className="w-12 h-12 text-[#3B82F6] mb-1" />
              <span className="font-mono text-[10px] font-semibold tracking-wider text-[#3B82F6] uppercase">
                Legacy LMS
              </span>
            </div>
          </motion.div>

          {/* 6 Orbiting Floating Bubbles (z-index: 20 per §2.7 & §3.3) */}
          {PROBLEM_ITEMS.map((item) => {
            const Icon = item.icon;
            return (
              <motion.div
                key={item.id}
                initial={
                  shouldReduceMotion ? false : { scale: 0, opacity: 0 }
                }
                whileInView={
                  shouldReduceMotion ? {} : { scale: 1, opacity: 1 }
                }
                viewport={{ once: true, amount: 0.3 }}
                transition={{
                  duration: 0.5,
                  delay: 0.15 * item.id,
                  type: "spring",
                  damping: 18,
                }}
                className="absolute w-[184px] bg-white border border-[#E2E8F0] rounded-[14px] p-4 text-left shadow-[0_4px_16px_rgba(0,0,0,0.06)] hover:-translate-y-1 hover:border-[#DBEAFE] transition-all duration-200 z-20"
                style={{
                  left: item.desktopCoords.left,
                  top: item.desktopCoords.top,
                  transform: "translate(-50%, -50%)",
                }}
              >
                <div className="flex items-center gap-2 mb-2">
                  <div className="p-1.5 rounded-lg bg-[#EFF6FF] text-[#3B82F6]">
                    <Icon className="w-4 h-4" />
                  </div>
                  {item.target !== undefined && (
                    <span className="font-heading text-2xl text-[#3B82F6] leading-none">
                      {/* ILLUSTRATIVE stat per §2.9 */}
                      <AnimatedCounter
                        target={item.target}
                        suffix={item.suffix}
                      />
                    </span>
                  )}
                </div>

                {item.quote ? (
                  <p className="font-body text-xs font-semibold text-[#0F172A] leading-snug mb-1">
                    {item.quote}
                  </p>
                ) : null}

                <p className="font-body text-[11px] text-[#64748B] leading-normal">
                  {item.description}
                </p>
              </motion.div>
            );
          })}
        </div>

        {/* ========================================================================= */}
        {/* MOBILE & TABLET FALLBACK (< 1024px) — Clean Stack (No Orbit, No Scroll) */}
        {/* ========================================================================= */}
        <div className="lg:hidden flex flex-col items-center mt-6">
          {/* Mobile Center Hub Graphic */}
          <div className="relative w-[200px] h-[200px] mb-10 flex items-center justify-center">
            <svg className="absolute inset-0 w-full h-full" viewBox="0 0 200 200">
              <path
                d="M 100 20 A 80 80 0 1 0 170 60"
                fill="none"
                stroke="#CBD5E1"
                strokeWidth="2"
                strokeDasharray="8 6"
              />
            </svg>
            <div className="absolute top-4 right-5 text-[#FB7185]">
              <XCircle className="w-5 h-5 fill-white" />
            </div>
            <div className="w-[90px] h-[90px] rounded-full bg-[#EFF6FF] border border-[#DBEAFE] flex flex-col items-center justify-center">
              <BookOpen className="w-8 h-8 text-[#3B82F6] mb-0.5" />
              <span className="font-mono text-[9px] font-semibold text-[#3B82F6]">
                LMS GAP
              </span>
            </div>
          </div>

          {/* Cards Grid: 1 col on mobile, 2 col on tablet */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-lg mx-auto">
            {PROBLEM_ITEMS.map((item) => {
              const Icon = item.icon;
              return (
                <div
                  key={item.id}
                  className="bg-white border border-[#E2E8F0] rounded-[14px] p-4 text-left shadow-sm"
                >
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="p-1.5 rounded-lg bg-[#EFF6FF] text-[#3B82F6]">
                      <Icon className="w-4 h-4" />
                    </div>
                    {item.target !== undefined && (
                      <span className="font-heading text-2xl text-[#3B82F6] leading-none">
                        {/* ILLUSTRATIVE stat per §2.9 */}
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
                </div>
              );
            })}
          </div>
        </div>
      </div>
    </section>
  );
}
