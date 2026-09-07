"use client";

import React, { useEffect, useState } from "react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { CompetencyAnalytics } from "@/lib/api/types";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface CompetencyComparisonChartProps {
  competencies: CompetencyAnalytics[];
  className?: string;
}

export const CompetencyComparisonChart = React.memo(
  function CompetencyComparisonChart({
    competencies,
    className,
  }: CompetencyComparisonChartProps) {
    const [isMounted, setIsMounted] = useState(false);
    const shouldReduceMotion = useReducedMotion();

    useEffect(() => {
      setIsMounted(true);
    }, []);

    const data = competencies.map((c) => ({
      name:
        c.competency_name.length > 20
          ? `${c.competency_name.slice(0, 18)}...`
          : c.competency_name,
      fullName: c.competency_name,
      Mastery: Math.round(c.average_mastery * 100),
      Confidence: Math.round(c.average_confidence * 100),
      Coverage: Math.round(c.average_coverage * 100),
    }));

    if (!isMounted) {
      return (
        <div className="w-full h-[360px] bg-slate-50/50 rounded-xl flex items-center justify-center border border-slate-200 animate-pulse">
          <span className="text-xs text-slate-400">Loading comparison chart...</span>
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
              Competency Metrics Comparison
            </h3>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              Comparative view of average mastery, belief confidence, and coverage
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">0–100%</span>
        </div>

        <div className="w-full h-[260px] relative">
          <ResponsiveContainer width="100%" height="100%" debounce={50}>
            <BarChart
              layout="vertical"
              data={data}
              margin={{ top: 10, right: 25, left: 10, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
              <XAxis
                type="number"
                domain={[0, 100]}
                unit="%"
                tick={{ fontSize: 11, fill: "#64748B" }}
              />
              <YAxis
                type="category"
                dataKey="name"
                width={130}
                tick={{ fontSize: 11, fill: "#334155" }}
              />
              <Tooltip
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const row = payload[0].payload;
                    return (
                      <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700 font-sans">
                        <div className="font-semibold text-blue-300 mb-1.5">
                          {row.fullName}
                        </div>
                        <div className="space-y-1">
                          <div className="flex justify-between gap-4">
                            <span className="text-blue-400">Avg Mastery:</span>
                            <span className="font-bold">{row.Mastery}%</span>
                          </div>
                          <div className="flex justify-between gap-4">
                            <span className="text-teal-400">Avg Confidence:</span>
                            <span className="font-bold">{row.Confidence}%</span>
                          </div>
                          <div className="flex justify-between gap-4">
                            <span className="text-amber-400">Avg Coverage:</span>
                            <span className="font-bold">{row.Coverage}%</span>
                          </div>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Bar
                dataKey="Mastery"
                fill="#2563EB"
                radius={[0, 4, 4, 0]}
                animationDuration={shouldReduceMotion ? 0 : 500}
              />
              <Bar
                dataKey="Confidence"
                fill="#0D9488"
                radius={[0, 4, 4, 0]}
                animationDuration={shouldReduceMotion ? 0 : 500}
              />
              <Bar
                dataKey="Coverage"
                fill="#F59E0B"
                radius={[0, 4, 4, 0]}
                animationDuration={shouldReduceMotion ? 0 : 500}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="flex items-center justify-center gap-6 pt-3 border-t border-slate-100 text-xs">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-blue-600 inline-block" />
            <span className="text-slate-700 font-medium">Mastery</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-teal-600 inline-block" />
            <span className="text-slate-700 font-medium">Confidence</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-sm bg-amber-500 inline-block" />
            <span className="text-slate-700 font-medium">Coverage</span>
          </div>
        </div>
      </div>
    );
  }
);

CompetencyComparisonChart.displayName = "CompetencyComparisonChart";
