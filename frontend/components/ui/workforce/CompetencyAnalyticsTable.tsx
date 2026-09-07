"use client";

import React, { useState, useMemo } from "react";
import { CompetencyAnalytics } from "@/lib/api/types";
import { ArrowUpDown, ArrowUp, ArrowDown } from "lucide-react";
import { cn } from "@/lib/cn";

interface CompetencyAnalyticsTableProps {
  competencies: CompetencyAnalytics[];
  className?: string;
}

type SortField =
  | "competency_name"
  | "role_name"
  | "learner_count"
  | "assessed_count"
  | "average_mastery"
  | "average_confidence"
  | "average_coverage"
  | "total_evidence";

export function CompetencyAnalyticsTable({
  competencies,
  className,
}: CompetencyAnalyticsTableProps) {
  const [sortField, setSortField] = useState<SortField>("average_mastery");
  const [sortAsc, setSortAsc] = useState(false);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const sortedCompetencies = useMemo(() => {
    return [...competencies].sort((a, b) => {
      let valA = a[sortField];
      let valB = b[sortField];

      if (typeof valA === "string" && typeof valB === "string") {
        return sortAsc
          ? valA.localeCompare(valB)
          : valB.localeCompare(valA);
      }

      const numA = (valA as number) ?? 0;
      const numB = (valB as number) ?? 0;
      return sortAsc ? numA - numB : numB - numA;
    });
  }, [competencies, sortField, sortAsc]);

  const renderSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 text-slate-400" />;
    }
    return sortAsc ? (
      <ArrowUp className="w-3 h-3 text-blue-600" />
    ) : (
      <ArrowDown className="w-3 h-3 text-blue-600" />
    );
  };

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 shadow-xs",
        className
      )}
    >
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-2 mb-4">
        <div>
          <h3 className="font-heading text-xl sm:text-2xl text-slate-900">
            Cadre Competency Analytics
          </h3>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Role curriculum benchmarks, learner participation, and calibration metrics
          </p>
        </div>
        <span className="text-xs text-slate-400">
          {competencies.length} registered competencies
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 text-[11px] uppercase tracking-wider bg-slate-50/60 font-semibold">
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("competency_name")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Competency</span>
                  {renderSortIcon("competency_name")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("role_name")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Role</span>
                  {renderSortIcon("role_name")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("learner_count")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Learners</span>
                  {renderSortIcon("learner_count")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("assessed_count")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Assessed</span>
                  {renderSortIcon("assessed_count")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("average_mastery")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Avg Mastery</span>
                  {renderSortIcon("average_mastery")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("average_confidence")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Avg Conf</span>
                  {renderSortIcon("average_confidence")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none"
                onClick={() => handleSort("average_coverage")}
              >
                <div className="flex items-center gap-1.5">
                  <span>Avg Cov</span>
                  {renderSortIcon("average_coverage")}
                </div>
              </th>
              <th
                className="py-3 px-4 cursor-pointer select-none text-right"
                onClick={() => handleSort("total_evidence")}
              >
                <div className="flex items-center justify-end gap-1.5">
                  <span>Evidence</span>
                  {renderSortIcon("total_evidence")}
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {sortedCompetencies.map((comp) => {
              const masteryPct = Math.round(comp.average_mastery * 100);
              return (
                <tr
                  key={comp.competency_id}
                  className="hover:bg-slate-50/80 transition"
                >
                  <td className="py-3 px-4 font-semibold text-slate-900">
                    {comp.competency_name}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {comp.role_name}
                  </td>
                  <td className="py-3 px-4 font-medium text-slate-900">
                    {comp.learner_count}
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {comp.assessed_count} of {comp.learner_count}
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 w-8">
                        {masteryPct}%
                      </span>
                      <div className="w-16 sm:w-24 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full",
                            masteryPct >= 70
                              ? "bg-teal-600"
                              : masteryPct >= 50
                              ? "bg-blue-600"
                              : "bg-amber-500"
                          )}
                          style={{ width: `${masteryPct}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-teal-50 text-teal-700 border border-teal-200">
                      {Math.round(comp.average_confidence * 100)}%
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-600">
                    {Math.round(comp.average_coverage * 100)}%
                  </td>
                  <td className="py-3 px-4 text-right font-medium text-slate-900">
                    {comp.total_evidence} items
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
