"use client";

import { useEffect, useState } from "react";
import { useReducedMotion as useFramerReducedMotion } from "framer-motion";

export function useReducedMotion(): boolean {
  const framerMotionReduced = useFramerReducedMotion();
  const [systemReduced, setSystemReduced] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const mediaQuery = window.matchMedia("(prefers-reduced-motion: reduce)");
    setSystemReduced(mediaQuery.matches);

    const handler = (event: MediaQueryListEvent) => {
      setSystemReduced(event.matches);
    };

    mediaQuery.addEventListener("change", handler);
    return () => mediaQuery.removeEventListener("change", handler);
  }, []);

  return Boolean(framerMotionReduced ?? systemReduced);
}
