import React from "react";
import { cn } from "@/lib/cn";

export interface DotPatternProps {
  className?: string;
  variant?: "light" | "dark";
}

export function DotPattern({
  className,
  variant = "light",
}: DotPatternProps) {
  const dotColor = variant === "light" ? "#CBD5E1" : "rgba(255, 255, 255, 0.08)";

  return (
    <div
      aria-hidden="true"
      className={cn(
        "absolute inset-0 z-0 pointer-events-none overflow-hidden select-none",
        className
      )}
      style={{
        backgroundImage: `radial-gradient(circle, ${dotColor} 1.2px, transparent 1.2px)`,
        backgroundSize: "24px 24px",
      }}
    />
  );
}
