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
  Cell,
} from "recharts";
import { BackendCompetency } from "@/lib/api/types";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface CoverageBarChartProps {
  competencies: BackendCompetency[];
  className?: string;
}

export const CoverageBarChart = React.memo(function CoverageBarChart({
  competencies,
  className,
}: CoverageBarChartProps) {
  const [isMounted, setIsMounted] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const data = competencies.map((c) => ({
    name:
      c.competency_name.length > 25
        ? `${c.competency_name.slice(0, 22)}...`
        : c.competency_name,
    fullName: c.competency_name,
    coverage: Math.round(c.coverage * 100),
    mastery: c.mastery !== null ? Math.round(c.mastery * 100) : null,
    status: c.status,
  }));

  if (!isMounted) {
    return (
      <div className="w-full h-[220px] bg-slate-50/50 rounded-xl flex items-center justify-center border border-slate-200 animate-pulse">
        <span className="text-xs text-slate-400">Loading coverage chart...</span>
      </div>
    );
  }

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[260px] ${className}`}
    >
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="font-heading text-xl text-slate-900">
            Competency Syllabus Coverage
          </h3>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Percentage of subskill syllabus breadth evaluated for each competency
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">0–100%</span>
      </div>

      <div className="w-full h-[180px] relative">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={data}
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
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
              width={140}
              tick={{ fontSize: 11, fill: "#334155" }}
            />
            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const row = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700 font-sans">
                      <div className="font-semibold text-blue-300 mb-1">
                        {row.fullName}
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Coverage:</span>
                        <span className="font-bold text-white">{row.coverage}%</span>
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Status:</span>
                        <span className="capitalize text-slate-300">
                          {row.status.replace("_", " ")}
                        </span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar
              dataKey="coverage"
              radius={[0, 6, 6, 0]}
              animationDuration={shouldReduceMotion ? 0 : 500}
              animationEasing="ease-out"
            >
              {data.map((entry, idx) => (
                <Cell
                  key={`cell-${idx}`}
                  fill={
                    entry.status === "ASSESSED"
                      ? "#2563EB"
                      : entry.status === "CONFLICTING_EVIDENCE"
                      ? "#F59E0B"
                      : "#CBD5E1"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      {/* Legend */}
      <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-100">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block" />
            Assessed
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-slate-300 inline-block" />
            Unassessed (0% coverage)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            Conflicting Evidence
          </span>
        </div>
      </div>
    </div>
  );
});

CoverageBarChart.displayName = "CoverageBarChart";
