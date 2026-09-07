"use client";

import React from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { ArrowRight, Sparkles } from "lucide-react";
import { DotPattern } from "@/components/ui/DotPattern";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function Footer() {
  const shouldReduceMotion = useReducedMotion();

  return (
    <footer id="footer" className="w-full">
      {/* ========================================================================= */}
      {/* DARK CTA BLOCK (var(--blue-900) #1E3A5F) */}
      {/* ========================================================================= */}
      <section className="relative py-24 md:py-32 px-6 bg-[#1E3A5F] text-white text-center overflow-hidden">
        {/* Dark Dot Pattern Overlay */}
        <DotPattern variant="dark" />

        <div className="relative z-10 max-w-3xl mx-auto flex flex-col items-center">
          <motion.div
            initial={shouldReduceMotion ? false : { scale: 0.9, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5 }}
            className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/10 border border-white/20 text-xs font-mono font-medium text-blue-200 uppercase tracking-wider mb-6"
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-300" />
            <span>Autonomous Intelligence Loop</span>
          </motion.div>

          <motion.h2
            initial={shouldReduceMotion ? false : { y: 25, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.6, ease: "easeOut" }}
            className="font-heading text-4xl sm:text-5xl md:text-6xl uppercase tracking-[0.02em] leading-tight mb-4 text-white"
          >
            READY TO CLOSE THE LOOP?
          </motion.h2>

          <motion.p
            initial={shouldReduceMotion ? false : { y: 15, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
            className="font-body text-base md:text-xl text-blue-100/80 leading-relaxed mb-10 max-w-xl"
          >
            Start identifying competency gaps with verifiable evidence, not
            guesswork. Empower officers across every statistical cadre.
          </motion.p>

          <motion.div
            initial={shouldReduceMotion ? false : { scale: 0.95, opacity: 0 }}
            whileInView={shouldReduceMotion ? {} : { scale: 1, opacity: 1 }}
            viewport={{ once: true, amount: 0.2 }}
            transition={{ duration: 0.4, delay: 0.2 }}
          >
            <button
              type="button"
              onClick={() => {
                const el = document.getElementById("features");
                el?.scrollIntoView({ behavior: "smooth" });
              }}
              className="h-12 px-8 rounded-full bg-white text-[#1E3A5F] font-body font-bold text-base tracking-wide shadow-xl hover:scale-105 hover:shadow-[0_0_50px_rgba(255,255,255,0.6)] active:scale-95 transition-all duration-200 flex items-center gap-2"
            >
              <span>Start Assessment</span>
              <ArrowRight className="w-4 h-4" />
            </button>
          </motion.div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* MAIN FOOTER (var(--gray-900) #0F172A) */}
      {/* ========================================================================= */}
      <section className="bg-[#0F172A] text-white pt-16 pb-12 px-6 border-t border-[#1E293B]">
        <div className="max-w-[1280px] mx-auto">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-10 pb-12 border-b border-[#1E293B]">
            {/* Col 1: Brand Info */}
            <div>
              <span className="font-heading text-2xl tracking-wider text-[#3B82F6] block mb-3">
                GYANSETU
              </span>
              <p className="font-body text-xs text-[#94A3B8] leading-relaxed mb-4">
                AI-driven competency intelligence platform for India&apos;s
                official statistical workforce. Closing the loop between training
                hours and job execution mastery.
              </p>
              <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded bg-[#1E293B] border border-[#334155] text-[10px] font-mono text-[#94A3B8]">
                <span>Status: 103 Tests Passing</span>
              </div>
            </div>

            {/* Col 2: Navigation */}
            <div>
              <h4 className="font-body text-xs font-bold uppercase tracking-wider text-white mb-4">
                Platform
              </h4>
              <ul className="space-y-2.5 font-body text-xs text-[#94A3B8]">
                <li>
                  <Link href="#hero" className="hover:text-white transition-colors">
                    Competency Intelligence
                  </Link>
                </li>
                <li>
                  <Link href="#problem" className="hover:text-white transition-colors">
                    The Problem
                  </Link>
                </li>
                <li>
                  <Link href="#solution" className="hover:text-white transition-colors">
                    Closed Loop Solution
                  </Link>
                </li>
                <li>
                  <Link href="#how-it-works" className="hover:text-white transition-colors">
                    How It Works
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 3: Architecture */}
            <div>
              <h4 className="font-body text-xs font-bold uppercase tracking-wider text-white mb-4">
                Architecture
              </h4>
              <ul className="space-y-2.5 font-body text-xs text-[#94A3B8]">
                <li>
                  <Link href="#features" className="hover:text-white transition-colors">
                    Adaptive Assessment Engine
                  </Link>
                </li>
                <li>
                  <Link href="#features" className="hover:text-white transition-colors">
                    Evidence Fusion Model
                  </Link>
                </li>
                <li>
                  <Link href="#technology" className="hover:text-white transition-colors">
                    ChromaDB Vector Store
                  </Link>
                </li>
                <li>
                  <Link href="#technology" className="hover:text-white transition-colors">
                    4-Tier Fallback Resilience
                  </Link>
                </li>
              </ul>
            </div>

            {/* Col 4: Ecosystem & Hackathon */}
            <div>
              <h4 className="font-body text-xs font-bold uppercase tracking-wider text-white mb-4">
                Ecosystem
              </h4>
              <ul className="space-y-2.5 font-body text-xs text-[#94A3B8]">
                <li>Ministry of Statistics & Programme Implementation (MoSPI)</li>
                <li>National Statistical Systems Training Academy (NSSTA)</li>
                <li>Training Programme Advisory Committee (TPAC)</li>
                <li>Smart India Hackathon (SIH 2026)</li>
              </ul>
            </div>
          </div>

          {/* Bottom Copyright Bar */}
          <div className="pt-8 flex flex-col sm:flex-row items-center justify-between gap-4 font-body text-xs text-[#64748B]">
            <p>© 2026 GyanSetu. Built for Smart India Hackathon (SIH 2026).</p>
            <p className="font-mono text-[11px]">
              Team CodeHashiras · Precision Competency Platform
            </p>
          </div>
        </div>
      </section>
    </footer>
  );
}
