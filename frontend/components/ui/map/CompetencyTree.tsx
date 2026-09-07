"use client";

import React, { useState } from "react";
import { BackendCompetency } from "@/lib/api/types";
import {
  Folder,
  FolderOpen,
  ChevronDown,
  ChevronRight,
  GitFork,
  HelpCircle,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";
import { cn } from "@/lib/cn";

interface CompetencyTreeProps {
  roleName: string;
  competencies: BackendCompetency[];
  selectedId: number | null;
  onSelect: (competency: BackendCompetency) => void;
  className?: string;
}

export const CompetencyTree = React.memo(function CompetencyTree({
  roleName,
  competencies,
  selectedId,
  onSelect,
  className,
}: CompetencyTreeProps) {
  const [isRoleExpanded, setIsRoleExpanded] = useState(true);

  return (
    <div
      className={cn(
        "bg-white rounded-xl border border-slate-200 p-6 shadow-xs flex flex-col justify-between min-h-[400px]",
        className
      )}
    >
      <div>
        {/* Tree Header */}
        <div className="flex items-center justify-between mb-4">
          <div>
            <h3 className="font-heading text-xl text-slate-900">
              Role Competency Hierarchy
            </h3>
            <p className="text-xs text-slate-500 font-sans mt-0.5">
              Interactive tree structure of role competencies and calibrated mastery
            </p>
          </div>
          <span className="text-xs font-mono text-slate-400">
            {competencies.length} Nodes
          </span>
        </div>

        {/* Tree Node Container */}
        <div className="space-y-2 select-none">
          {/* Root Node: Role */}
          <div
            onClick={() => setIsRoleExpanded(!isRoleExpanded)}
            className="flex items-center gap-2 p-3 rounded-xl bg-slate-50 border border-slate-200 hover:bg-slate-100/70 cursor-pointer transition"
          >
            <button
              type="button"
              className="text-slate-400 hover:text-slate-600 p-0.5"
              aria-label="Toggle role branch"
            >
              {isRoleExpanded ? (
                <ChevronDown className="w-4 h-4" />
              ) : (
                <ChevronRight className="w-4 h-4" />
              )}
            </button>
            {isRoleExpanded ? (
              <FolderOpen className="w-4 h-4 text-blue-600 shrink-0" />
            ) : (
              <Folder className="w-4 h-4 text-blue-600 shrink-0" />
            )}
            <span className="font-semibold text-xs text-slate-900 tracking-wide">
              {roleName}
            </span>
            <span className="text-[10px] bg-blue-100 text-blue-800 px-2 py-0.5 rounded-full ml-auto font-medium">
              Role Root
            </span>
          </div>

          {/* Children: Competencies */}
          {isRoleExpanded && (
            <div className="pl-6 space-y-2 border-l-2 border-slate-100 ml-4 mt-2">
              {competencies.map((comp) => {
                const isSelected = selectedId === comp.competency_id;
                const isUnassessed = comp.mastery === null;
                const masteryPct = isUnassessed ? null : Math.round(comp.mastery! * 100);

                return (
                  <div
                    key={comp.competency_id}
                    onClick={() => onSelect(comp)}
                    className={cn(
                      "flex items-center justify-between p-3 rounded-xl border cursor-pointer transition-all",
                      isSelected
                        ? "bg-blue-50/80 border-blue-600 shadow-xs ring-1 ring-blue-600/20"
                        : "bg-white border-slate-200 hover:border-blue-300 hover:bg-slate-50/60"
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <GitFork
                        className={cn(
                          "w-4 h-4 shrink-0 transition",
                          isSelected ? "text-blue-600" : "text-slate-400"
                        )}
                      />
                      <div>
                        <div
                          className={cn(
                            "text-xs font-semibold transition",
                            isSelected ? "text-blue-900 font-bold" : "text-slate-900"
                          )}
                        >
                          {comp.competency_name}
                        </div>
                        <div className="text-[11px] text-slate-400">
                          ID: #{comp.competency_id} · {comp.evidence_count} evidence records
                        </div>
                      </div>
                    </div>

                    {/* Node Badges */}
                    <div className="flex items-center gap-2">
                      <span
                        className={cn(
                          "px-2.5 py-1 rounded text-[11px] font-semibold border",
                          isUnassessed
                            ? "bg-slate-100 text-slate-600 border-slate-200"
                            : masteryPct! >= 70
                            ? "bg-teal-50 text-teal-800 border-teal-200"
                            : masteryPct! >= 40
                            ? "bg-amber-50 text-amber-800 border-amber-200"
                            : "bg-rose-50 text-rose-800 border-rose-200"
                        )}
                      >
                        {isUnassessed ? "Unassessed" : `${masteryPct}%`}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      <div className="pt-4 border-t border-slate-100 text-[11px] text-slate-400">
        Click any node to view granular subskill calibration in the right panel
      </div>
    </div>
  );
});

CompetencyTree.displayName = "CompetencyTree";
