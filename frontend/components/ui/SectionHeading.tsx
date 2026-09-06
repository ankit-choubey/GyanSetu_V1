"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export interface SectionHeadingProps {
  title: string;
  subtitle?: string;
  align?: "center" | "left";
  className?: string;
  light?: boolean;
}

export function SectionHeading({
  title,
  subtitle,
  align = "center",
  className,
  light = false,
}: SectionHeadingProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <div
      className={cn(
        "mb-12 md:mb-16",
        align === "center" ? "text-center mx-auto" : "text-left",
        className
      )}
    >
      <motion.h2
        initial={shouldReduceMotion ? false : { y: 30, opacity: 0 }}
        whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
        viewport={{ once: true, amount: 0.2 }}
        transition={{ duration: 0.6, ease: "easeOut" }}
        className={cn(
          "font-heading text-4xl sm:text-5xl md:text-[56px] uppercase tracking-[0.02em] leading-[1.08] mb-4",
          light ? "text-white" : "text-[#0F172A]"
        )}
      >
        {title}
      </motion.h2>

      {subtitle && (
        <motion.p
          initial={shouldReduceMotion ? false : { y: 20, opacity: 0 }}
          whileInView={shouldReduceMotion ? {} : { y: 0, opacity: 1 }}
          viewport={{ once: true, amount: 0.2 }}
          transition={{ duration: 0.5, delay: 0.1, ease: "easeOut" }}
          className={cn(
            "font-body text-base md:text-xl leading-relaxed max-w-2xl",
            align === "center" && "mx-auto",
            light ? "text-[#94A3B8]" : "text-[#475569]"
          )}
        >
          {subtitle}
        </motion.p>
      )}
    </div>
  );
}
