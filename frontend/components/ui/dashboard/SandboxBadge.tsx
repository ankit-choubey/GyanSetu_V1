"use client";

import React from "react";
import { AlertCircle } from "lucide-react";
import { cn } from "@/lib/cn";

interface SandboxBadgeProps {
  className?: string;
  label?: string;
}

export function SandboxBadge({
  className,
  label = "SANDBOX DATA",
}: SandboxBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-mono font-medium",
        "bg-amber-50 text-amber-800 border border-amber-200 shadow-sm",
        className
      )}
      title="Non-negotiable Honesty Rule: Simulation sandbox data. Never presented as measured official statistics."
    >
      <AlertCircle className="w-3.5 h-3.5 text-amber-600 shrink-0" />
      <span>[{label}]</span>
    </div>
  );
}
