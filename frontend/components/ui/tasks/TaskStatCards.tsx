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
    <div className={cn("grid grid-cols-1 sm:grid-cols-3 gap-5", className)}>
      {/* Active Tasks */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Active Tasks
          </span>
          <Clock className="w-5 h-5 text-blue-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {summary.active}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">In progress assignments</p>
        </div>
      </div>

      {/* Completed Tasks */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Completed Tasks
          </span>
          <CheckCircle2 className="w-5 h-5 text-teal-600" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {summary.completed}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Verified interventions</p>
        </div>
      </div>

      {/* Total Tasks */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between min-h-[145px]">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider font-sans">
            Total Assigned
          </span>
          <ListChecks className="w-5 h-5 text-slate-500" />
        </div>
        <div>
          <div className="font-body font-extrabold text-3xl sm:text-4xl tabular-nums tracking-tight text-slate-900 mt-2">
            {summary.total}
          </div>
          <p className="text-sm text-slate-600 mt-1.5 font-sans">Curriculum practical work</p>
        </div>
      </div>
    </div>
  );
}
