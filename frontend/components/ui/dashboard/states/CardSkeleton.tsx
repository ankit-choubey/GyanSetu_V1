"use client";

import React from "react";
import { cn } from "@/lib/cn";

interface CardSkeletonProps {
  className?: string;
  height?: string;
}

export function CardSkeleton({
  className,
  height = "h-40",
}: CardSkeletonProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-slate-200 bg-white p-5 animate-pulse flex flex-col justify-between",
        height,
        className
      )}
    >
      <div className="flex justify-between items-center mb-4">
        <div className="h-4 w-28 bg-slate-200 rounded" />
        <div className="h-4 w-16 bg-slate-200 rounded-full" />
      </div>
      <div className="h-9 w-36 bg-slate-200 rounded my-2" />
      <div className="h-3 w-44 bg-slate-200 rounded" />
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
        {[...Array(5)].map((_, i) => (
          <CardSkeleton key={i} height="h-36" />
        ))}
      </div>

      {/* Row 2: Radar + Gap */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        <div className="lg:col-span-7">
          <CardSkeleton height="h-[380px]" />
        </div>
        <div className="lg:col-span-5">
          <CardSkeleton height="h-[380px]" />
        </div>
      </div>

      {/* Row 3: NBA */}
      <CardSkeleton height="h-64" />

      {/* Row 4: Agent Activity */}
      <CardSkeleton height="h-40" />
    </div>
  );
}
