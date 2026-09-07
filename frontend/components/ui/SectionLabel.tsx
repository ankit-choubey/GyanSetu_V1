"use client";

import React from "react";
import { motion } from "framer-motion";
import { cn } from "@/lib/cn";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export interface SectionLabelProps {
  number: string;
  text: string;
  className?: string;
  light?: boolean;
}

export function SectionLabel({
  number,
  text,
  className,
  light = false,
}: SectionLabelProps) {
  const shouldReduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={shouldReduceMotion ? false : { x: -30, opacity: 0 }}
      whileInView={shouldReduceMotion ? {} : { x: 0, opacity: 1 }}
      viewport={{ once: true, amount: 0.3 }}
      transition={{ duration: 0.5, ease: "easeOut" }}
      className={cn(
        "font-mono text-xs md:text-[13px] font-medium uppercase tracking-[0.1em] mb-4 inline-block select-none",
        light ? "text-[#94A3B8]" : "text-[#94A3B8]",
        className
      )}
    >
      <span className={light ? "text-[#60A5FA]" : "text-[#3B82F6]"}>[ {number} ]</span>{" "}
      <span>{text}</span>
    </motion.div>
  );
}
