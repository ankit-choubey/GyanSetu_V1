"use client";

import React from "react";
import { ListChecks, Clock, CheckCircle2 } from "lucide-react";
import { TaskSummary } from "@/lib/api/types";
import { cn } from "@/lib/cn";

interface TaskStatCardsProps {
  summary: TaskSummary;
  className?: string;
}

export function TaskStatCards({ summary, className }: TaskStatCardsProps) {
  return (
    <div className={cn("grid grid-cols-1 sm:grid-cols-3 gap-4", className)}>
      {/* Active Tasks */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Active Tasks
          </span>
          <Clock className="w-4 h-4 text-blue-600" />
        </div>
        <div>
          <div className="font-body font-bold text-3xl tabular-nums tracking-tight text-slate-900 mt-1">
            {summary.active}
          </div>
          <p className="text-xs text-slate-500 mt-1">In progress assignments</p>
        </div>
      </div>

      {/* Completed Tasks */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Completed Tasks
          </span>
          <CheckCircle2 className="w-4 h-4 text-teal-600" />
        </div>
        <div>
          <div className="font-body font-bold text-3xl tabular-nums tracking-tight text-slate-900 mt-1">
            {summary.completed}
          </div>
          <p className="text-xs text-slate-500 mt-1">Verified interventions</p>
        </div>
      </div>

      {/* Total Tasks */}
      <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-sm flex flex-col justify-between min-h-[120px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider">
            Total Assigned
          </span>
          <ListChecks className="w-4 h-4 text-slate-500" />
        </div>
        <div>
          <div className="font-body font-bold text-3xl tabular-nums tracking-tight text-slate-900 mt-1">
            {summary.total}
          </div>
          <p className="text-xs text-slate-500 mt-1">Curriculum practical work</p>
        </div>
      </div>
    </div>
  );
}
