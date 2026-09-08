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

  useEffect(() => {
    let isSubscribed = true;
    client
      .get<TasksResponse>("/api/practical/learner-tasks")
      .then((res) => {
        if (isSubscribed && res && res.tasks && res.tasks.length > 0) {
          setData(res);
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
      <div>
        <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
          Tasks
        </h2>
        <p className="text-sm text-slate-500 font-sans mt-1">
          Practical tasks, drills, and curriculum assignments
        </p>
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
