"use client";

import React from "react";
import { AlertOctagon, RotateCw } from "lucide-react";
import { cn } from "@/lib/cn";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Failed to Retrieve Competency State",
  message = "Could not synchronize belief state from the competency engine. Please check API connectivity or refresh.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <div
      className={cn(
        "rounded-xl border border-rose-200 bg-rose-50/60 p-8 text-center flex flex-col items-center justify-center max-w-xl mx-auto my-6",
        className
      )}
    >
      <div className="w-12 h-12 rounded-xl bg-rose-100 flex items-center justify-center text-rose-600 mb-3">
        <AlertOctagon className="w-6 h-6" />
      </div>

      <h3 className="font-heading text-2xl text-rose-950 mb-1">
        {title}
      </h3>

      <p className="text-xs text-rose-800 font-sans max-w-md mb-5 leading-relaxed">
        {message}
      </p>

      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-medium bg-rose-600 hover:bg-rose-700 text-white transition shadow-sm"
        >
          <RotateCw className="w-3.5 h-3.5" />
          <span>Retry Synchronizing</span>
        </button>
      )}
    </div>
  );
}
