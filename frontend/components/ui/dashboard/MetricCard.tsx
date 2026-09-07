"use client";

import React from "react";
import { cn } from "@/lib/cn";
import { StatusChip } from "@/components/ui/dashboard/primitives";

export interface MetricCardProps {
  label: string;
  value: number | string | null;
  displayValue?: string;
  sublabel?: string;
  confidence?: "Low" | "Medium" | "High" | null;
  confidenceScore?: number;
  type?: "mastery" | "confidence" | "coverage" | "recency" | "diversity";
  sparklineData?: number[];
  className?: string;
}

export const MetricCard = React.memo(function MetricCard({
  label,
  value,
  displayValue,
  sublabel,
  confidence,
  confidenceScore,
  type = "mastery",
  className,
}: MetricCardProps) {
  const isUnassessed = value === null || value === undefined;

  // Status color applied to the number only (never tint the whole card)
  let valueColor = "text-slate-900";
  let statusIndicatorColor = "bg-slate-300";

  if (isUnassessed) {
    valueColor = "text-slate-400";
    statusIndicatorColor = "bg-slate-300";
  } else if (typeof value === "number") {
    if (type === "mastery") {
      if (value >= 0.7) {
        valueColor = "text-teal-600";
        statusIndicatorColor = "bg-teal-500";
      } else if (value >= 0.4) {
        valueColor = "text-amber-600";
        statusIndicatorColor = "bg-amber-500";
      } else {
        valueColor = "text-rose-600";
        statusIndicatorColor = "bg-rose-500";
      }
    } else if (type === "coverage" || type === "confidence") {
      valueColor = "text-slate-900";
      statusIndicatorColor = value >= 0.7 ? "bg-teal-500" : "bg-blue-500";
    }
  }

  // Format value strictly in Inter with tabular-nums
  const renderFormattedValue = () => {
    if (isUnassessed) {
      return (
        <div className="flex items-center gap-1.5">
          <span className="font-body font-semibold text-2xl tracking-tight text-slate-400">
            Unassessed
          </span>
        </div>
      );
    }

    if (displayValue) {
      return (
        <span className={cn("font-body font-bold text-3xl tabular-nums tracking-tight", valueColor)}>
          {displayValue}
        </span>
      );
    }

    if (typeof value === "number") {
      if (type === "mastery" || type === "confidence" || type === "coverage") {
        return (
          <span className={cn("font-body font-bold text-3xl tabular-nums tracking-tight", valueColor)}>
            {(value * 100).toFixed(0)}%
          </span>
        );
      }
      return (
        <span className={cn("font-body font-bold text-3xl tabular-nums tracking-tight", valueColor)}>
          {value}
        </span>
      );
    }

    return (
      <span className={cn("font-body font-bold text-3xl tabular-nums tracking-tight", valueColor)}>
        {value}
      </span>
    );
  };

  // Clean sublabel: replace "Target: 80%" with "Role target: 80%"
  const cleanSublabel = sublabel?.replace("Target: 80%", "Role target: 80%");

  return (
    <div
      className={cn(
        "relative rounded-xl border border-slate-200 bg-white p-5 transition-all duration-200 shadow-sm hover:shadow-md flex flex-col justify-between min-h-[140px]",
        className
      )}
    >
      {/* Top Header: Eyebrow Label + Status Chip */}
      <div className="flex items-center justify-between gap-2 mb-3">
        <div className="flex items-center gap-1.5">
          <span className={cn("w-2 h-2 rounded-full shrink-0", statusIndicatorColor)} />
          <span className="text-[11px] font-medium uppercase tracking-wider text-slate-400">
            {label}
          </span>
        </div>

        {isUnassessed ? (
          <StatusChip status="unassessed" size="sm">
            No evidence
          </StatusChip>
        ) : confidence ? (
          <StatusChip
            status={confidence === "High" ? "high" : confidence === "Medium" ? "med" : "low"}
            size="sm"
          >
            Conf: {confidence}
          </StatusChip>
        ) : null}
      </div>

      {/* Main Metric Figure (Inter font with tabular-nums) */}
      <div className="my-1 flex items-baseline">
        {renderFormattedValue()}
      </div>

      {/* Subtitle / Benchmark */}
      <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-sans">
        <span className="truncate">{cleanSublabel || "Baseline benchmark"}</span>
      </div>
    </div>
  );
});
