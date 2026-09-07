import React from "react";
import { cn } from "@/lib/cn";

/**
 * 1. Card: Standardized surface primitive
 * Clean white surface, 1px slate-200 border, 12px radius, resting shadow-sm
 */
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  hover?: boolean;
}

export function Card({ className, hover = false, children, ...props }: CardProps) {
  return (
    <div
      className={cn(
        "bg-white border border-slate-200 rounded-xl",
        hover ? "shadow-sm hover:shadow-md transition-shadow duration-200" : "shadow-sm",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}

/**
 * 2. StatCell: Borderless metric cell for inside cards
 * Eyebrow label + bold tabular-nums value + optional sublabel
 */
export interface StatCellProps {
  label: string;
  value: React.ReactNode;
  sublabel?: string;
  status?: "high" | "med" | "low" | "unassessed" | "neutral";
  className?: string;
}

export function StatCell({ label, value, sublabel, status = "neutral", className }: StatCellProps) {
  const valueColor =
    status === "high"
      ? "text-teal-600"
      : status === "med"
      ? "text-amber-600"
      : status === "low"
      ? "text-rose-600"
      : status === "unassessed"
      ? "text-slate-400"
      : "text-slate-900";

  return (
    <div className={cn("flex flex-col", className)}>
      <span className="text-xs font-semibold uppercase tracking-wider text-slate-500 mb-1.5 font-sans">
        {label}
      </span>
      <div className={cn("font-body font-bold text-2xl sm:text-3xl tabular-nums tracking-tight leading-none", valueColor)}>
        {value}
      </div>
      {sublabel && (
        <span className="text-sm text-slate-600 mt-1.5 font-sans">
          {sublabel}
        </span>
      )}
    </div>
  );
}

/**
 * 3. StatusChip: Semantic state pills (color = state only)
 * High (teal), Med (amber), Low (rose), Unassessed (slate), Info (blue)
 */
export interface StatusChipProps {
  status: "high" | "med" | "low" | "unassessed" | "info";
  size?: "sm" | "md";
  className?: string;
  children: React.ReactNode;
}

export function StatusChip({ status, size = "md", className, children }: StatusChipProps) {
  const statusStyles = {
    high: "bg-teal-50 text-teal-700 border-teal-200",
    med: "bg-amber-50 text-amber-700 border-amber-200",
    low: "bg-rose-50 text-rose-700 border-rose-200",
    unassessed: "bg-slate-100 text-slate-600 border-slate-200",
    info: "bg-blue-50 text-blue-700 border-blue-200",
  }[status];

  const sizeStyles = size === "sm" ? "text-xs px-2.5 py-0.5" : "text-xs sm:text-sm px-3 py-1 font-medium";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded-full border shrink-0",
        statusStyles,
        sizeStyles,
        className
      )}
    >
      {children}
    </span>
  );
}

/**
 * 4. IconTile: Neutral 36x36 icon container (1 per card header max)
 */
export interface IconTileProps {
  icon: React.ElementType;
  tone?: "neutral" | "brand";
  className?: string;
}

export function IconTile({ icon: Icon, tone = "neutral", className }: IconTileProps) {
  return (
    <div
      className={cn(
        "w-9 h-9 rounded-xl flex items-center justify-center shrink-0",
        tone === "brand" ? "bg-blue-50 text-blue-600 border border-blue-100" : "bg-slate-100 text-slate-600",
        className
      )}
    >
      <Icon className="w-5 h-5" />
    </div>
  );
}

/**
 * 5. SectionHeader: Clean title + subtitle + optional action
 * Replaces numbered-circle AI tutorial look
 */
export interface SectionHeaderProps {
  eyebrow?: string;
  title: string;
  subtitle?: string;
  action?: React.ReactNode;
  className?: string;
}

export function SectionHeader({ eyebrow, title, subtitle, action, className }: SectionHeaderProps) {
  return (
    <div className={cn("flex flex-col sm:flex-row sm:items-center justify-between gap-3", className)}>
      <div>
        {eyebrow && (
          <span className="text-xs font-bold uppercase tracking-wider text-blue-600 block mb-1">
            {eyebrow}
          </span>
        )}
        <h2 className="font-heading text-xl sm:text-2xl text-slate-900 tracking-wide leading-tight">
          {title}
        </h2>
        {subtitle && (
          <p className="text-sm text-slate-600 font-sans mt-1 leading-relaxed">
            {subtitle}
          </p>
        )}
      </div>
      {action && <div className="shrink-0">{action}</div>}
    </div>
  );
}

/**
 * 6. Divider: 1px hairline divider between sections inside cards
 */
export function Divider({ className }: { className?: string }) {
  return <div className={cn("border-t border-slate-100 my-4", className)} />;
}
