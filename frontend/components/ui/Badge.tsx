import React from "react";
import { cn } from "@/lib/cn";

export interface BadgeProps {
  children: React.ReactNode;
  icon?: React.ReactNode;
  variant?: "blue" | "gray" | "coral" | "teal";
  className?: string;
}

export function Badge({
  children,
  icon,
  variant = "blue",
  className,
}: BadgeProps) {
  const variantStyles = {
    blue: "bg-[#EFF6FF] text-[#2563EB] border-[#DBEAFE]",
    gray: "bg-[#F1F5F9] text-[#475569] border-[#E2E8F0]",
    coral: "bg-[#FFF1F2] text-[#FB7185] border-[#FFE4E6]",
    teal: "bg-[#F0FDFA] text-[#0D9488] border-[#CCFBF1]",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 px-3 py-1 text-[11px] md:text-xs font-semibold uppercase tracking-[0.08em] rounded-full border",
        variantStyles[variant],
        className
      )}
    >
      {icon && <span className="inline-block shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
}
