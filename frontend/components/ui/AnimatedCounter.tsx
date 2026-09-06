"use client";

import React, { useEffect, useRef } from "react";
import { useInView, useMotionValue, useTransform, animate, motion } from "framer-motion";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export interface AnimatedCounterProps {
  target: number;
  decimals?: number;
  duration?: number;
  delay?: number;
  prefix?: string;
  suffix?: string;
  className?: string;
}

export function AnimatedCounter({
  target,
  decimals = 0,
  duration = 2,
  delay = 0,
  prefix = "",
  suffix = "",
  className,
}: AnimatedCounterProps) {
  const ref = useRef<HTMLSpanElement>(null);
  const isInView = useInView(ref, { once: true, amount: 0.2 });
  const shouldReduceMotion = useReducedMotion();

  const count = useMotionValue(0);
  const rounded = useTransform(count, (val) => {
    return val.toFixed(decimals);
  });

  useEffect(() => {
    if (shouldReduceMotion) {
      count.set(target);
      return;
    }

    if (isInView) {
      const controls = animate(count, target, {
        duration,
        delay,
        ease: "easeInOut",
      });
      return controls.stop;
    }
  }, [isInView, target, duration, delay, shouldReduceMotion, count]);

  if (shouldReduceMotion) {
    return (
      <span className={className}>
        {prefix}
        {target.toFixed(decimals)}
        {suffix}
      </span>
    );
  }

  return (
    <span ref={ref} className={className}>
      {prefix}
      <motion.span>{rounded}</motion.span>
      {suffix}
    </span>
  );
}
