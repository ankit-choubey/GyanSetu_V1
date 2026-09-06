"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Stethoscope,
  FileSpreadsheet,
  Users2,
  GitFork,
  ArrowLeft,
  Menu,
  X,
  Bell,
  User,
  ExternalLink,
  Sparkles,
} from "lucide-react";
import { SandboxBadge } from "@/components/ui/dashboard/SandboxBadge";
import { DashboardProvider, useDashboard } from "@/components/ui/dashboard/DashboardContext";
import { cn } from "@/lib/cn";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { persona, setPersona } = useDashboard();

  const navItems = [
    {
      name: "Learner Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      active: pathname === "/dashboard",
      badge: "Hero Screen",
    },
    {
      name: "Adaptive Diagnostics",
      href: "#",
      icon: Stethoscope,
      active: false,
      badge: "Phase 2",
    },
    {
      name: "Practical Tasks & FOD",
      href: "#",
      icon: FileSpreadsheet,
      active: false,
      badge: "Phase 2",
    },
    {
      name: "Workforce Intelligence",
      href: "#",
      icon: Users2,
      active: false,
      badge: "Phase 3",
    },
    {
      name: "Competency Ontology",
      href: "#",
      icon: GitFork,
      active: false,
      badge: "Phase 3",
    },
  ];

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex text-[#0F172A] font-body antialiased">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* LEFT SIDEBAR */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 w-64 bg-white border-r border-slate-200 flex flex-col justify-between transition-transform duration-300 lg:translate-x-0",
          mobileMenuOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div>
          {/* Brand Header */}
          <div className="p-5 border-b border-slate-200 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2.5">
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-heading text-lg font-bold shadow-sm">
                GS
              </div>
              <div>
                <span className="font-heading text-xl tracking-wider text-slate-900 block leading-tight">
                  GYANSETU
                </span>
                <span className="font-mono text-[9px] text-slate-500 uppercase tracking-wider block">
                  MoSPI · Official Statistics
                </span>
              </div>
            </Link>
            <button
              type="button"
              className="lg:hidden text-slate-500 hover:text-slate-800"
              onClick={() => setMobileMenuOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
          </div>

          {/* Navigation Links */}
          <div className="p-3 space-y-1">
            <div className="px-3 py-2 text-[10px] font-mono text-slate-400 uppercase tracking-wider">
              Workforce Navigation
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  className={cn(
                    "flex items-center justify-between px-3 py-2.5 rounded-lg text-xs font-medium transition",
                    item.active
                      ? "bg-blue-50 text-blue-700 font-semibold shadow-xs"
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
                        "text-[9px] font-mono px-1.5 py-0.5 rounded",
                        item.active
                          ? "bg-blue-200/60 text-blue-800"
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

        {/* Sidebar Footer: Cadre Model & Return to Landing */}
        <div className="p-4 border-t border-slate-200 bg-slate-50/50 space-y-3">
          <div className="bg-white p-2.5 rounded-lg border border-slate-200 text-xs">
            <div className="font-mono text-[10px] text-slate-400 uppercase">
              Competency Policy
            </div>
            <div className="font-medium text-slate-700 text-[11px] mt-0.5">
              SSS JSO Competency Model v2.4
            </div>
            <div className="text-[10px] text-slate-500 mt-0.5">
              Aligned with iGOT & NSSTA
            </div>
          </div>

          <Link
            href="/"
            className="flex items-center gap-2 text-xs font-mono text-slate-600 hover:text-blue-600 transition"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Return to Public Portal</span>
          </Link>
        </div>
      </aside>

      {/* MAIN VIEWPORT CONTAINER */}
      <div className="flex-1 lg:pl-64 flex flex-col min-w-0">
        {/* TOP BAR */}
        <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200 px-4 sm:px-8 py-3 flex items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              className="lg:hidden text-slate-600 hover:text-slate-900"
              onClick={() => setMobileMenuOpen(true)}
            >
              <Menu className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2">
                <h1 className="font-heading text-lg sm:text-xl tracking-wide text-slate-900">
                  {persona === "jso" ? "Officer Ramesh Kumar, JSO" : "Officer Priya Sharma, JSO"}
                </h1>
                <SandboxBadge />
              </div>
              <p className="text-[11px] font-mono text-slate-500 hidden sm:block">
                Subordinate Statistical Service (SSS) ·{" "}
                {persona === "jso"
                  ? "MoSPI Regional Office (Bhopal)"
                  : "NSSTA Induction Campus"}
              </p>
            </div>
          </div>

          {/* Persona Switcher & Badges (Hackathon Demo Tool) */}
          <div className="flex items-center gap-3">
            {/* Interactive Persona Switcher */}
            <div className="flex items-center bg-slate-100 p-1 rounded-lg border border-slate-200 text-xs font-mono">
              <button
                type="button"
                onClick={() => setPersona("jso")}
                className={cn(
                  "px-2.5 py-1 rounded transition text-[11px]",
                  persona === "jso"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
                title="Active JSO with measured sampling deficit"
              >
                JSO (Sampling Deficit)
              </button>
              <button
                type="button"
                onClick={() => setPersona("new")}
                className={cn(
                  "px-2.5 py-1 rounded transition text-[11px]",
                  persona === "new"
                    ? "bg-white text-blue-700 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
                title="Newly inducted officer with unassessed baseline"
              >
                New Officer (Unassessed)
              </button>
            </div>

            {/* Profile Avatar */}
            <div className="w-8 h-8 rounded-full bg-blue-100 border border-blue-200 text-blue-700 flex items-center justify-center font-mono text-xs font-bold">
              {persona === "jso" ? "RK" : "PS"}
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
