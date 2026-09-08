"use client";

import React, { useState, useEffect } from "react";
import tasksData from "@/lib/mock/tasks-mock.json";
import { TasksResponse } from "@/lib/api/types";
import { client } from "@/lib/api/client";
import { TaskStatCards } from "@/components/ui/tasks/TaskStatCards";
import { TaskProgressChart } from "@/components/ui/tasks/TaskProgressChart";
import { TaskBreakdownCard } from "@/components/ui/tasks/TaskBreakdownCard";
import { TaskListTable } from "@/components/ui/tasks/TaskListTable";

export default function TasksPage() {
  const [data, setData] = useState<TasksResponse>(tasksData as TasksResponse);
  const [loading, setLoading] = useState(true);
  const [isLiveSync, setIsLiveSync] = useState(false);

  useEffect(() => {
    let isSubscribed = true;
    client
      .get<TasksResponse>("/api/practical/learner-tasks")
      .then((res) => {
        if (isSubscribed && res && res.tasks && res.tasks.length > 0) {
          setData(res);
          setIsLiveSync(true);
        }
      })
      .catch((err) => {
        console.warn("Could not fetch live practical tasks, using cached view:", err);
      })
      .finally(() => {
        if (isSubscribed) setLoading(false);
      });

    return () => {
      isSubscribed = false;
    };
  }, []);

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
              Tasks
            </h2>
            <span
              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded text-xs font-semibold uppercase tracking-wider border ${
                isLiveSync
                  ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                  : "bg-slate-100 text-slate-600 border-slate-200"
              }`}
            >
              <span
                className={`w-1.5 h-1.5 rounded-full ${
                  isLiveSync ? "bg-emerald-500 animate-pulse" : "bg-slate-400"
                }`}
              />
              {isLiveSync ? "Live Practical Sync" : "Curriculum View (Demonstration)"}
            </span>
          </div>
          <p className="text-sm text-slate-500 font-sans mt-1">
            Practical tasks, drills, and curriculum assignments
          </p>
        </div>
      </div>

      {/* ROW 1: STAT CARDS */}
      <TaskStatCards summary={data.summary} />

      {/* ROW 2: PROGRESS CHART (COL 7) + BREAKDOWN (COL 5) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <TaskProgressChart tasks={data.tasks} className="h-full" />
        </div>
        <div className="lg:col-span-5 flex flex-col">
          <TaskBreakdownCard
            tasks={data.tasks}
            summary={data.summary}
            className="h-full"
          />
        </div>
      </section>

      {/* ROW 3: TASK LIST TABLE */}
      <section aria-labelledby="task-list-heading">
        <h2 id="task-list-heading" className="sr-only">
          Task List Table
        </h2>
        <TaskListTable tasks={data.tasks} />
      </section>
    </div>
  );
}
