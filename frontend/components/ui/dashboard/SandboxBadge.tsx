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
  label = "LIVE SYNCED",
}: SandboxBadgeProps) {
  const isLive = label.toUpperCase().includes("LIVE") || label.toUpperCase().includes("SYNC");
  return (
    <div
      className={cn(
        "inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold",
        isLive
          ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
          : "bg-amber-50 text-amber-800 border border-amber-200",
        className
      )}
      title={isLive ? "Live synchronized mode" : "Official Operational Mode"}
    >
      <span className={cn("w-1.5 h-1.5 rounded-full", isLive ? "bg-emerald-500 animate-pulse" : "bg-blue-500")} />
      <span>{label}</span>
    </div>
  );
}
