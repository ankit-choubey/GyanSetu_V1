"use client";

import React from "react";
import { TaskItem, TaskSummary } from "@/lib/api/types";
import { CheckCircle2, Clock, Layers } from "lucide-react";
import { cn } from "@/lib/cn";

interface TaskBreakdownCardProps {
  tasks: TaskItem[];
  summary: TaskSummary;
  className?: string;
}

export const TaskBreakdownCard = React.memo(function TaskBreakdownCard({
  tasks,
  summary,
  className,
}: TaskBreakdownCardProps) {
  const completedPct =
    summary.total > 0 ? Math.round((summary.completed / summary.total) * 100) : 0;
  const activePct =
    summary.total > 0 ? Math.round((summary.active / summary.total) * 100) : 0;

  const practiceCount = tasks.filter((t) => t.type === "PRACTICE").length;
  const trainingCount = tasks.filter((t) => t.type === "TRAINING").length;

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[340px]",
        className
      )}
    >
      <div>
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-heading text-xl text-slate-900">Workload Breakdown</h3>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              Status distribution & curriculum intervention types
            </p>
          </div>
          <Layers className="w-4 h-4 text-slate-400" />
        </div>

        {/* Stacked Progress Bar */}
        <div className="mb-6">
          <div className="flex justify-between text-xs text-slate-600 mb-2 font-medium">
            <span>Overall Task Completion</span>
            <span>{completedPct}%</span>
          </div>
          <div className="w-full h-3 bg-slate-100 rounded-full overflow-hidden flex">
            <div
              className="bg-teal-600 h-full transition-all duration-500"
              style={{ width: `${completedPct}%` }}
              title={`Completed: ${summary.completed}`}
            />
            <div
              className="bg-blue-600 h-full transition-all duration-500"
              style={{ width: `${activePct}%` }}
              title={`Active: ${summary.active}`}
            />
          </div>
        </div>

        {/* Stats Pairs */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
              <Clock className="w-3.5 h-3.5 text-blue-600" />
              <span>In Progress</span>
            </div>
            <span className="font-body font-bold text-2xl tabular-nums text-slate-900 block">
              {summary.active}
            </span>
          </div>

          <div className="bg-slate-50 p-3.5 rounded-lg border border-slate-100">
            <div className="flex items-center gap-1.5 text-xs text-slate-500 mb-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-teal-600" />
              <span>Completed</span>
            </div>
            <span className="font-body font-bold text-2xl tabular-nums text-slate-900 block">
              {summary.completed}
            </span>
          </div>
        </div>

        {/* Intervention Types */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
            Intervention Modalities
          </span>
          <div className="flex items-center justify-between text-xs py-1.5 border-b border-slate-100">
            <span className="text-slate-600">Practice Drills & Scenarios</span>
            <span className="font-semibold text-slate-900">{practiceCount}</span>
          </div>
          <div className="flex items-center justify-between text-xs py-1.5">
            <span className="text-slate-600">Training Modules</span>
            <span className="font-semibold text-slate-900">{trainingCount}</span>
          </div>
        </div>
      </div>

      <div className="pt-3 border-t border-slate-100 text-[11px] text-slate-400">
        Prioritized according to diagnosed competency gaps
      </div>
    </div>
  );
});

TaskBreakdownCard.displayName = "TaskBreakdownCard";
