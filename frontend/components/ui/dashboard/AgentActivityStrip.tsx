"use client";

import React from "react";
import { AgentActivity } from "@/lib/api/types";
import { CheckCircle2, CircleDashed, Clock, Cpu, Stethoscope, Lightbulb, Activity } from "lucide-react";
import { cn } from "@/lib/cn";

interface AgentActivityStripProps {
  activities: AgentActivity[];
  className?: string;
}

export function AgentActivityStrip({
  activities,
  className,
}: AgentActivityStripProps) {
  const getAgentIcon = (agent: AgentActivity["agent"]) => {
    switch (agent) {
      case "Diagnostic":
        return <Stethoscope className="w-4 h-4 text-blue-600" />;
      case "Competency Engine":
        return <Cpu className="w-4 h-4 text-indigo-600" />;
      case "Intervention":
        return <Lightbulb className="w-4 h-4 text-amber-600" />;
      case "Monitoring":
        return <Activity className="w-4 h-4 text-teal-600" />;
      default:
        return <Activity className="w-4 h-4 text-slate-500" />;
    }
  };

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-5 shadow-sm",
        className
      )}
    >
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h4 className="font-heading text-xl tracking-wide text-slate-900">
            Multi-Agent Audit Trail & System Activity
          </h4>
          <span className="text-xs font-mono text-slate-400">
            [3 Specialized Agents + Orchestrator]
          </span>
        </div>
        <span className="text-[11px] font-mono text-slate-500">
          State Synchronized
        </span>
      </div>

      {/* Horizontal Step Timeline */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {activities.map((item, idx) => {
          const isCompleted = item.status === "completed";
          const isPending = item.status === "pending";

          return (
            <div
              key={item.id}
              className={cn(
                "relative rounded-lg p-3.5 border transition-all flex flex-col justify-between",
                isCompleted
                  ? "bg-slate-50/70 border-slate-200"
                  : isPending
                  ? "bg-slate-50/30 border-dashed border-slate-200 text-slate-400"
                  : "bg-blue-50/40 border-blue-200 text-blue-900"
              )}
            >
              {/* Header: Agent + Status */}
              <div>
                <div className="flex items-center justify-between gap-1 mb-1.5">
                  <div className="flex items-center gap-1.5">
                    {getAgentIcon(item.agent)}
                    <span className="font-mono text-xs font-semibold text-slate-800">
                      {item.agent}
                    </span>
                  </div>
                  {isCompleted ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-teal-600 shrink-0" />
                  ) : (
                    <Clock className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                  )}
                </div>

                {/* Action summary */}
                <p className="text-xs text-slate-600 font-sans leading-relaxed mt-1">
                  {item.action}
                </p>
              </div>

              {/* Timestamp footer */}
              <div className="mt-3 pt-2 border-t border-slate-200/50 flex items-center justify-between text-[10px] font-mono text-slate-400">
                <span>Step 0{idx + 1}</span>
                <span>{item.timestamp}</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
