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
import { TaskItem } from "@/lib/api/types";
import { useReducedMotion } from "@/hooks/useReducedMotion";

interface TaskProgressChartProps {
  tasks: TaskItem[];
  className?: string;
}

export const TaskProgressChart = React.memo(function TaskProgressChart({
  tasks,
  className,
}: TaskProgressChartProps) {
  const [isMounted, setIsMounted] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  const chartData = tasks.map((t) => ({
    name: t.title.length > 25 ? `${t.title.slice(0, 22)}...` : t.title,
    fullName: t.title,
    progress: t.progress_pct,
    competency: t.competency_name,
    status: t.status,
  }));

  if (!isMounted) {
    return (
      <div className="w-full h-[320px] bg-slate-50/50 rounded-xl flex items-center justify-center border border-slate-200 animate-pulse">
        <span className="text-xs text-slate-400">Loading task progress...</span>
      </div>
    );
  }

  return (
    <div
      className={`bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[340px] ${className}`}
    >
      <div className="flex items-center justify-between mb-4">
        <div>
          <h3 className="font-heading text-xl text-slate-900">Task Completion Progress</h3>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Real-time completion percentage across active & completed assignments
          </p>
        </div>
        <span className="text-xs font-mono text-slate-400">0–100%</span>
      </div>

      <div className="w-full h-[250px] relative">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            layout="vertical"
            data={chartData}
            margin={{ top: 5, right: 30, left: 10, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
            <XAxis
              type="number"
              domain={[0, 100]}
              tick={{ fontSize: 11, fill: "#64748B" }}
              unit="%"
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
                  const data = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700 font-sans">
                      <div className="font-semibold text-blue-300 mb-1">
                        {data.fullName}
                      </div>
                      <div className="text-slate-300 mb-1">
                        Target: {data.competency}
                      </div>
                      <div className="flex justify-between gap-4 pt-1 border-t border-slate-800">
                        <span className="text-slate-400">Completion:</span>
                        <span className="font-bold text-white">{data.progress}%</span>
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
            <Bar
              dataKey="progress"
              radius={[0, 6, 6, 0]}
              animationDuration={shouldReduceMotion ? 0 : 600}
              animationEasing="ease-out"
            >
              {chartData.map((entry, idx) => (
                <Cell
                  key={`cell-${idx}`}
                  fill={
                    entry.progress === 100
                      ? "#0D9488"
                      : entry.progress >= 50
                      ? "#2563EB"
                      : "#F59E0B"
                  }
                />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="flex items-center justify-between text-xs text-slate-500 pt-3 border-t border-slate-100">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-teal-600 inline-block" />
            Completed (100%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-blue-600 inline-block" />
            In Progress (≥50%)
          </span>
          <span className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block" />
            Started (&lt;50%)
          </span>
        </div>
      </div>
    </div>
  );
});

TaskProgressChart.displayName = "TaskProgressChart";
