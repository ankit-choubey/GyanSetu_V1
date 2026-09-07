"use client";

import React, { useEffect, useState } from "react";
import {
  Radar,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from "recharts";
import { motion } from "framer-motion";
import { RadarDataPoint } from "@/lib/api/types";
import { useReducedMotion } from "@/hooks/useReducedMotion";
import { HelpCircle } from "lucide-react";

interface CompetencyRadarProps {
  data: RadarDataPoint[];
  className?: string;
  isAllUnassessed?: boolean;
}

export const CompetencyRadar = React.memo(function CompetencyRadar({
  data,
  className,
  isAllUnassessed = false,
}: CompetencyRadarProps) {
  const [isMounted, setIsMounted] = useState(false);
  const shouldReduceMotion = useReducedMotion();

  useEffect(() => {
    setIsMounted(true);
  }, []);

  if (!isMounted) {
    return (
      <div className="w-full h-[380px] bg-slate-50/50 rounded-xl flex items-center justify-center border border-slate-200 animate-pulse">
        <span className="text-xs text-slate-400">Loading radar chart...</span>
      </div>
    );
  }

  return (
    <div className={`relative bg-white rounded-xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between ${className}`}>
      {/* Card Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-2">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="font-heading text-xl sm:text-2xl tracking-normal text-slate-900">
              Competency Overview
            </h3>
            {isAllUnassessed && (
              <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] bg-slate-100 text-slate-600 border border-slate-200">
                <HelpCircle className="w-3 h-3 text-slate-400" />
                Awaiting Baseline
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Current measured competency state overlaid against benchmark (80%)
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-1.5">
            <span className="w-3 h-3 rounded-full bg-blue-500/20 border-2 border-blue-600 inline-block" />
            <span className="text-slate-700 font-medium">Measured State</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-3.5 h-0.5 border-t-2 border-dashed border-slate-400 inline-block" />
            <span className="text-slate-500">Benchmark (80%)</span>
          </div>
        </div>
      </div>

      {/* Recharts Polar Chart Container */}
      <motion.div
        className="w-full h-[300px] relative"
        initial={shouldReduceMotion ? false : { opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: "easeOut" }}
      >
        <ResponsiveContainer width="100%" height="100%" debounce={50}>
          <RadarChart cx="50%" cy="50%" outerRadius="75%" data={data}>
            <PolarGrid stroke="#E2E8F0" strokeDasharray="3 3" />
            <PolarAngleAxis
              dataKey="axis"
              tick={{ fill: "#475569", fontSize: 12 }}
            />
            <PolarRadiusAxis
              angle={90}
              domain={[0, 100]}
              tick={{ fill: "#94A3B8", fontSize: 10 }}
              stroke="#CBD5E1"
            />

            {/* Benchmark Polygon */}
            <Radar
              name="Benchmark"
              dataKey="target"
              stroke="#94A3B8"
              strokeDasharray="4 4"
              strokeWidth={1.5}
              fill="transparent"
            />

            {/* Current Officer Polygon */}
            <Radar
              name="Measured State"
              dataKey="current"
              stroke="#2563EB"
              strokeWidth={2}
              fill="#3B82F6"
              fillOpacity={isAllUnassessed ? 0.05 : 0.22}
            />

            <Tooltip
              content={({ active, payload }) => {
                if (active && payload && payload.length) {
                  const dataPoint = payload[0].payload;
                  return (
                    <div className="bg-slate-900 text-white rounded-lg p-3 text-xs shadow-xl border border-slate-700 font-sans">
                      <div className="font-semibold text-blue-300 mb-1">
                        {dataPoint.axis}
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Current Measured:</span>
                        <span className="font-bold text-white">
                          {dataPoint.isUnassessed ? "Unassessed" : `${dataPoint.current}%`}
                        </span>
                      </div>
                      <div className="flex justify-between gap-4 py-0.5">
                        <span className="text-slate-400">Role Benchmark:</span>
                        <span className="font-bold text-slate-300">
                          {dataPoint.target}%
                        </span>
                      </div>
                      <div className="mt-1 pt-1 border-t border-slate-800 text-[10px] text-slate-400">
                        {dataPoint.isUnassessed
                          ? "Take assessment to establish baseline"
                          : `Delta: ${dataPoint.target - dataPoint.current}%`}
                      </div>
                    </div>
                  );
                }
                return null;
              }}
            />
          </RadarChart>
        </ResponsiveContainer>
      </motion.div>

      {/* Screen Reader Accessible Summary */}
      <div className="sr-only">
        <h4>Competency Profile Summary Table</h4>
        <table>
          <thead>
            <tr>
              <th>Competency</th>
              <th>Current Score</th>
              <th>Benchmark</th>
            </tr>
          </thead>
          <tbody>
            {data.map((point) => (
              <tr key={point.axis}>
                <td>{point.axis}</td>
                <td>{point.isUnassessed ? "Unassessed" : `${point.current}%`}</td>
                <td>{point.target}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer info */}
      <div className="mt-2 pt-3 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500">
        <span>Evidence Source: Assessments & Practice</span>
        <span className="text-blue-600 font-medium">
          {isAllUnassessed ? "Baseline Required" : "Primary Attention: Lowest Mastery Axis"}
        </span>
      </div>
    </div>
  );
});

CompetencyRadar.displayName = "CompetencyRadar";
