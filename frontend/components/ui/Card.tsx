import React from "react";
import { cn } from "@/lib/cn";

export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  hoverEffect?: boolean;
}

export function Card({
  children,
  className,
  hoverEffect = true,
  ...props
}: CardProps) {
  return (
    <div
      className={cn(
        "bg-white rounded-[16px] border border-[#E2E8F0] p-6 md:p-8 transition-all duration-300",
        hoverEffect && "hover:-translate-y-1 hover:border-[#DBEAFE] hover:shadow-[0_8px_30px_rgba(0,0,0,0.06)]",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
