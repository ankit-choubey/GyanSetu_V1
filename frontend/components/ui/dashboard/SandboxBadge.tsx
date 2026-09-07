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
  label = "DEMO DATA",
}: SandboxBadgeProps) {
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium",
        "bg-amber-50 text-amber-800 border border-amber-200 shadow-xs",
        className
      )}
      title="Demonstration data mode"
    >
      <AlertCircle className="w-3 h-3 text-amber-600 shrink-0" />
      <span>{label}</span>
    </div>
  );
}
