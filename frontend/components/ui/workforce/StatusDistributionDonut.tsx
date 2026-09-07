"use client";

import React, { useEffect, useState } from "react";
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { CompetencyAnalytics } from "@/lib/api/types";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface StatusDistributionDonutProps {
  competencies: CompetencyAnalytics[];
  className?: string;
}

export const StatusDistributionDonut = React.memo(
  function StatusDistributionDonut({
    competencies,
    className,
  }: StatusDistributionDonutProps) {
    const [isMounted, setIsMounted] = useState(false);
    const shouldReduceMotion = useReducedMotion();

    useEffect(() => {
      setIsMounted(true);
    }, []);

    // Aggregate counts across all competencies
    const totals = competencies.reduce(
      (acc, c) => {
        acc.assessed += c.status_distribution.ASSESSED || 0;
        acc.unassessed += c.status_distribution.UNASSESSED || 0;
        acc.conflicting += c.status_distribution.CONFLICTING_EVIDENCE || 0;
        return acc;
      },
      { assessed: 0, unassessed: 0, conflicting: 0 }
    );

    const totalCount = totals.assessed + totals.unassessed + totals.conflicting;

    const data = [
      { name: "Assessed", value: totals.assessed, color: "#2563EB" },
      { name: "Unassessed", value: totals.unassessed, color: "#CBD5E1" },
      { name: "Conflicting", value: totals.conflicting, color: "#F59E0B" },
    ].filter((item) => item.value > 0);

    if (!isMounted) {
      return (
        <div className="w-full h-[340px] bg-slate-50/50 rounded-xl flex items-center justify-center border border-slate-200 animate-pulse">
          <span className="text-xs text-slate-400">Loading distribution chart...</span>
        </div>
      );
    }

    return (
      <div
        className={`bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[360px] ${className}`}
      >
        <div className="flex items-center justify-between mb-2">
          <div>
            <h3 className="font-heading text-xl text-slate-900">
              Evaluation Status Distribution
            </h3>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              Breakdown of assessed vs unassessed learner competencies
            </p>
          </div>
        </div>

        {/* Donut Chart with Centered Metric */}
        <div className="w-full h-[220px] relative flex items-center justify-center">
          <ResponsiveContainer width="100%" height="100%" debounce={50}>
            <PieChart>
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const item = payload[0];
                    const count = item.value as number;
                    const pct = totalCount > 0 ? Math.round((count / totalCount) * 100) : 0;
                    return (
                      <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700 font-sans">
                        <div className="font-semibold text-blue-300 mb-1">
                          {item.name}
                        </div>
                        <div className="flex justify-between gap-4">
                          <span className="text-slate-400">Count:</span>
                          <span className="font-bold text-white">
                            {count} ({pct}%)
                          </span>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={85}
                paddingAngle={3}
                dataKey="value"
                animationDuration={shouldReduceMotion ? 0 : 600}
                animationEasing="ease-out"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
            </PieChart>
          </ResponsiveContainer>

          {/* Centered Total Label inside Donut Ring */}
          <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none">
            <span className="font-heading text-2xl text-slate-900 leading-none">
              {totalCount}
            </span>
            <span className="text-[10px] text-slate-400 font-medium uppercase mt-0.5">
              Total Evals
            </span>
          </div>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-blue-600 inline-block" />
            <span className="text-slate-700 font-medium">Assessed</span>
            <span className="text-slate-400">({totals.assessed})</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-slate-300 inline-block" />
            <span className="text-slate-700 font-medium">Unassessed</span>
            <span className="text-slate-400">({totals.unassessed})</span>
          </div>
          {totals.conflicting > 0 && (
            <div className="flex items-center gap-2">
              <span className="w-3 h-3 rounded-full bg-amber-500 inline-block" />
              <span className="text-slate-700 font-medium">Conflicting</span>
              <span className="text-slate-400">({totals.conflicting})</span>
            </div>
          )}
        </div>
      </div>
    );
  }
);

StatusDistributionDonut.displayName = "StatusDistributionDonut";
