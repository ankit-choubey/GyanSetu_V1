"use client";

import React from "react";
import { cn } from "@/lib/cn";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "dark";
  size?: "sm" | "lg";
  children: React.ReactNode;
}

export function Button({
  variant = "primary",
  size = "sm",
  className,
  children,
  ...props
}: ButtonProps) {
  const baseStyles =
    "inline-flex items-center justify-center font-body font-semibold rounded-full transition-all duration-200 cursor-pointer active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed select-none";

  const sizeStyles = {
    sm: "h-10 px-6 text-sm tracking-wide",
    lg: "h-12 px-8 text-base tracking-wide",
  };

  const variantStyles = {
    primary:
      "text-white shadow-md hover:scale-[1.03] hover:shadow-[0_4px_20px_rgba(59,130,246,0.35)]",
    secondary:
      "bg-white text-[#0F172A] border border-[#E2E8F0] hover:bg-[#F8FAFC] hover:border-[#CBD5E1] hover:scale-[1.02]",
    dark:
      "bg-white text-[#1E3A5F] shadow-lg hover:scale-[1.05] hover:shadow-[0_0_40px_rgba(255,255,255,0.6)]",
  };

  const dynamicBackground =
    variant === "primary" ? { background: "var(--gradient-cta)" } : undefined;

  return (
    <button
      className={cn(baseStyles, sizeStyles[size], variantStyles[variant], className)}
      style={dynamicBackground}
      {...props}
    >
      {children}
    </button>
  );
}
