"use client";

import React, { useState } from "react";
import { TaskItem } from "@/lib/api/types";
import { Eye, CheckCircle2, Clock, Circle, X } from "lucide-react";
import { cn } from "@/lib/cn";

interface TaskListTableProps {
  tasks: TaskItem[];
  className?: string;
}

export function TaskListTable({ tasks, className }: TaskListTableProps) {
  const [selectedTask, setSelectedTask] = useState<TaskItem | null>(null);

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
            Assigned Practical Tasks
          </h3>
          <p className="text-xs text-slate-500 font-sans mt-0.5">
            Hands-on exercises and workplace problem-solving drills
          </p>
        </div>
        <span className="text-xs text-slate-400 font-medium">
          {tasks.length} total assignments
        </span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left text-xs border-collapse">
          <thead>
            <tr className="border-b border-slate-200 text-slate-500 text-[11px] uppercase tracking-wider bg-slate-50/60 font-semibold">
              <th className="py-3 px-4">Task Title</th>
              <th className="py-3 px-4">Type</th>
              <th className="py-3 px-4">Target Competency</th>
              <th className="py-3 px-4">Priority</th>
              <th className="py-3 px-4">Progress</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {tasks.map((task) => {
              const isCompleted = task.status === "completed";
              return (
                <tr
                  key={task.id}
                  className="hover:bg-slate-50/80 transition"
                >
                  <td className="py-3 px-4">
                    <div className="font-semibold text-slate-900 text-xs">
                      {task.title}
                    </div>
                    <div className="text-[11px] text-slate-400 mt-0.5 truncate max-w-xs">
                      Due: {new Date(task.due_date).toLocaleDateString()}
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span className="px-2 py-0.5 rounded text-[11px] font-medium bg-indigo-50 text-indigo-700 border border-indigo-200">
                      {task.type}
                    </span>
                  </td>
                  <td className="py-3 px-4 text-slate-700 font-medium">
                    {task.competency_name}
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={cn(
                        "px-2 py-0.5 rounded text-[11px] font-medium border",
                        task.priority === 1
                          ? "bg-rose-50 text-rose-700 border-rose-200"
                          : task.priority === 2
                          ? "bg-amber-50 text-amber-700 border-amber-200"
                          : "bg-slate-50 text-slate-600 border-slate-200"
                      )}
                    >
                      P{task.priority}
                    </span>
                  </td>
                  <td className="py-3 px-4">
                    <div className="flex items-center gap-2">
                      <span className="font-semibold text-slate-900 text-xs w-8">
                        {task.progress_pct}%
                      </span>
                      <div className="w-20 sm:w-28 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all duration-500",
                            isCompleted
                              ? "bg-teal-600"
                              : task.progress_pct >= 50
                              ? "bg-blue-600"
                              : "bg-amber-500"
                          )}
                          style={{ width: `${task.progress_pct}%` }}
                        />
                      </div>
                    </div>
                  </td>
                  <td className="py-3 px-4">
                    <span
                      className={cn(
                        "inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium border",
                        task.status === "completed"
                          ? "bg-teal-50 text-teal-800 border-teal-200"
                          : task.status === "active"
                          ? "bg-blue-50 text-blue-800 border-blue-200"
                          : "bg-slate-100 text-slate-600 border-slate-200"
                      )}
                    >
                      {task.status === "completed" ? (
                        <CheckCircle2 className="w-3 h-3 text-teal-600" />
                      ) : task.status === "active" ? (
                        <Clock className="w-3 h-3 text-blue-600" />
                      ) : (
                        <Circle className="w-3 h-3 text-slate-400" />
                      )}
                      <span className="capitalize">{task.status.replace("_", " ")}</span>
                    </span>
                  </td>
                  <td className="py-3 px-4 text-right">
                    <button
                      type="button"
                      onClick={() => setSelectedTask(task)}
                      className="p-1.5 rounded-lg text-slate-500 hover:text-blue-600 hover:bg-blue-50 transition"
                      title="View Task Details"
                      aria-label="View task details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Task Detail Modal */}
      {selectedTask && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-xl max-w-lg w-full border border-slate-200 shadow-xl p-6 relative">
            <button
              type="button"
              onClick={() => setSelectedTask(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 p-1"
            >
              <X className="w-5 h-5" />
            </button>

            <div className="flex items-center gap-2 mb-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase tracking-wider">
                {selectedTask.type}
              </span>
              <span className="px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-50 text-blue-700 border border-blue-200">
                Priority {selectedTask.priority}
              </span>
            </div>

            <h4 className="font-heading text-xl text-slate-900 mb-1">
              {selectedTask.title}
            </h4>
            <p className="text-xs text-slate-500 mb-4">
              Target Competency: {selectedTask.competency_name}
            </p>

            <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 text-xs text-slate-700 leading-relaxed mb-4">
              {selectedTask.description}
            </div>

            <div className="space-y-2 text-xs mb-6">
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Status:</span>
                <span className="font-semibold text-slate-900 capitalize">
                  {selectedTask.status}
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Current Progress:</span>
                <span className="font-semibold text-slate-900">
                  {selectedTask.progress_pct}%
                </span>
              </div>
              <div className="flex justify-between py-1.5 border-b border-slate-100">
                <span className="text-slate-500">Submission Due Date:</span>
                <span className="font-semibold text-slate-900">
                  {new Date(selectedTask.due_date).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={() => setSelectedTask(null)}
                className="px-4 py-2 text-xs font-medium bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg transition"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
