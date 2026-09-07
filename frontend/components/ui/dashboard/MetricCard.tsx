"use client";

import React from "react";
import { cn } from "@/lib/cn";
import { ShieldAlert, ShieldCheck, HelpCircle, TrendingUp } from "lucide-react";

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

  // Determine styling according to the 4 states:
  // - High (>= 0.7): teal
  // - Med (0.4-0.7): amber
  // - Low (< 0.4): coral
  // - null: neutral gray
  let statusColor = "border-slate-200 bg-white text-slate-900";
  let badgeColor = "bg-slate-100 text-slate-700 border-slate-200";

  if (isUnassessed) {
    statusColor = "border-slate-200 bg-slate-50/70 text-slate-500";
    badgeColor = "bg-slate-200/80 text-slate-600 border-slate-300";
  } else if (typeof value === "number") {
    if (type === "mastery") {
      if (value >= 0.7) {
        statusColor = "border-teal-200 bg-teal-50/30 text-teal-900";
        badgeColor = "bg-teal-100 text-teal-800 border-teal-200";
      } else if (value >= 0.4) {
        statusColor = "border-amber-200 bg-amber-50/30 text-amber-900";
        badgeColor = "bg-amber-100 text-amber-800 border-amber-200";
      } else {
        statusColor = "border-rose-200 bg-rose-50/30 text-rose-900";
        badgeColor = "bg-rose-100 text-rose-800 border-rose-200";
      }
    }
  }

  // Value rendering helper
  const renderFormattedValue = () => {
    if (isUnassessed) {
      return (
        <div className="flex items-center gap-1.5 text-slate-500">
          <HelpCircle className="w-6 h-6 text-slate-400" />
          <span className="font-heading text-3xl sm:text-4xl tracking-wide uppercase">
            Unassessed
          </span>
        </div>
      );
    }

    if (displayValue) {
      return (
        <span className="font-heading text-4xl sm:text-5xl tracking-tight">
          {displayValue}
        </span>
      );
    }

    if (typeof value === "number") {
      if (type === "mastery" || type === "confidence") {
        return (
          <span className="font-heading text-4xl sm:text-5xl tracking-tight">
            {(value * 100).toFixed(0)}%
          </span>
        );
      }
      if (type === "coverage") {
        return (
          <span className="font-heading text-4xl sm:text-5xl tracking-tight">
            {(value * 100).toFixed(0)}%
          </span>
        );
      }
      return (
        <span className="font-heading text-4xl sm:text-5xl tracking-tight">
          {value}
        </span>
      );
    }

    return (
      <span className="font-heading text-4xl sm:text-5xl tracking-tight">
        {value}
      </span>
    );
  };

  return (
    <div
      className={cn(
        "relative rounded-xl border p-5 transition-all duration-200 shadow-sm hover:shadow-md flex flex-col justify-between min-h-[140px]",
        statusColor,
        className
      )}
    >
      {/* Top Header: Label + Confidence / Status Chip */}
      <div className="flex items-center justify-between gap-2 mb-2">
        <span className="text-xs font-mono uppercase tracking-wider text-slate-500 font-medium">
          {label}
        </span>

        {isUnassessed ? (
          <span className="inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono border bg-slate-100 text-slate-600 border-slate-200">
            No Evidence
          </span>
        ) : confidence ? (
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-mono border font-medium",
              confidence === "High"
                ? "bg-teal-50 text-teal-700 border-teal-200"
                : confidence === "Medium"
                ? "bg-blue-50 text-blue-700 border-blue-200"
                : "bg-amber-50 text-amber-700 border-amber-200"
            )}
            title={`Estimation Confidence: ${confidenceScore ? (confidenceScore * 100).toFixed(0) + "%" : confidence}`}
          >
            {confidence === "High" ? (
              <ShieldCheck className="w-3 h-3 text-teal-600" />
            ) : (
              <ShieldAlert className="w-3 h-3 text-amber-600" />
            )}
            Conf: {confidence}
          </span>
        ) : null}
      </div>

      {/* Main Metric Value */}
      <div className="my-1 flex items-baseline gap-2">
        {renderFormattedValue()}
      </div>

      {/* Sublabel / Context */}
      <div className="mt-2 text-xs text-slate-500 font-sans flex items-center justify-between">
        <span>{sublabel || (isUnassessed ? "Baseline required" : "Measured state")}</span>
        {!isUnassessed && typeof value === "number" && type === "mastery" && (
          <span className="text-[11px] font-mono text-slate-400">
            Target: 80%
          </span>
        )}
      </div>
    </div>
  );
});

MetricCard.displayName = "MetricCard";
