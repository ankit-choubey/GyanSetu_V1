"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardCheck,
  ListChecks,
  Users2,
  GitFork,
  ArrowLeft,
  Menu,
  X,
} from "lucide-react";
import { SandboxBadge } from "@/components/ui/dashboard/SandboxBadge";
import { DashboardProvider, useDashboard } from "@/components/ui/dashboard/DashboardContext";
import { cn } from "@/lib/cn";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { persona, setPersona, userName, roleName } = useDashboard();

  const navItems = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      active: pathname === "/dashboard",
    },
    {
      name: "Assessments",
      href: "/dashboard/assessments",
      icon: ClipboardCheck,
      active: pathname?.startsWith("/dashboard/assessments"),
    },
    {
      name: "Tasks",
      href: "/dashboard/tasks",
      icon: ListChecks,
      active: pathname?.startsWith("/dashboard/tasks"),
    },
    {
      name: "Workforce",
      href: "/dashboard/workforce",
      icon: Users2,
      active: pathname?.startsWith("/dashboard/workforce"),
      badge: "Admin",
    },
    {
      name: "Competency Map",
      href: "/dashboard/map",
      icon: GitFork,
      active: pathname?.startsWith("/dashboard/map"),
    },
  ];

  const initials = userName
    .split(" ")
    .map((n) => n[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex text-[#0F172A] font-body antialiased">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* LEFT SIDEBAR (Fixed w-60) */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-60 bg-white border-r border-slate-200 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div>
          {/* Brand Header */}
          <div className="p-4 border-b border-slate-200 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-heading text-lg font-bold shadow-xs">
                GS
              </div>
              <div>
                <span className="font-heading text-lg tracking-wide text-slate-900 block leading-tight">
                  GYANSETU
                </span>
              </div>
            </Link>
            <button
              type="button"
              className="lg:hidden text-slate-500 hover:text-slate-800 p-1"
              onClick={() => setMobileMenuOpen(false)}
              aria-label="Close sidebar"
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <div className="p-3 space-y-1">
            <div className="px-3 py-1.5 text-[10px] font-semibold text-slate-400 uppercase tracking-wider">
              Navigation
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  className={cn(
                    "flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition relative",
                    item.active
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-[3px] border-blue-600 pl-[9px]"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <div className="flex items-center gap-2.5">
                    <Icon
                      className={cn(
                        "w-4 h-4",
                        item.active ? "text-blue-600" : "text-slate-400"
                      )}
                    />
                    <span>{item.name}</span>
                  </div>
                  {item.badge && (
                    <span
                      className={cn(
                        "text-[9px] font-medium px-1.5 py-0.5 rounded",
                        item.active
                          ? "bg-blue-200/70 text-blue-800"
                          : "bg-slate-100 text-slate-500"
                      )}
                    >
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Sidebar Footer: Clean Return to Home */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50">
          <Link
            href="/"
            className="flex items-center gap-2 text-xs font-medium text-slate-600 hover:text-blue-600 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Back to Home</span>
          </Link>
        </div>
      </aside>

      {/* MAIN VIEWPORT CONTAINER */}
      <div className="flex-1 lg:pl-60 flex flex-col min-w-0">
        {/* TOP BAR */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-xs border-b border-slate-200 px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="lg:hidden text-slate-600 hover:text-slate-900 p-1"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-heading text-lg sm:text-xl tracking-normal text-slate-900">
                  {userName}
                </h1>
                <SandboxBadge label="DEMO DATA" />
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">
                {roleName}
              </p>
            </div>
          </div>

          {/* Persona Switcher (Demo Tool) */}
          <div className="flex items-center gap-3">
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs">
              <button
                type="button"
                onClick={() => setPersona("jso")}
                className={cn(
                  "px-2.5 py-1 rounded transition text-xs",
                  persona === "jso"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
              >
                Sample Learner
              </button>
              <button
                type="button"
                onClick={() => setPersona("new")}
                className={cn(
                  "px-2.5 py-1 rounded transition text-xs",
                  persona === "new"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
              >
                New Learner
              </button>
            </div>

            {/* User Avatar */}
            <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">
              {initials}
            </div>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 p-4 sm:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <DashboardProvider>
      <DashboardShell>{children}</DashboardShell>
    </DashboardProvider>
  );
}
