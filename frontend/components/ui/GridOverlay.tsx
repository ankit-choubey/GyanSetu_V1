import React from "react";
import { cn } from "@/lib/cn";

export interface GridOverlayProps {
  className?: string;
}

export function GridOverlay({ className }: GridOverlayProps) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "absolute inset-0 z-0 pointer-events-none overflow-hidden select-none",
        className
      )}
      style={{
        backgroundImage: `
          linear-gradient(to right, #E2E8F0 1px, transparent 1px),
          linear-gradient(to bottom, #E2E8F0 1px, transparent 1px)
        `,
        backgroundSize: "80px 80px",
        opacity: 0.65,
      }}
    />
  );
}
