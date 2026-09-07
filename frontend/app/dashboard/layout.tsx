"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  ClipboardCheck,
  ListChecks,
  Users2,
  GitFork,
  ArrowLeft,
  Menu,
  X,
  Lock,
  LogOut,
  UploadCloud,
  ChevronsLeft,
  ChevronsRight,
} from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { StatusChip } from "@/components/ui/dashboard/primitives";
import { DashboardProvider, useDashboard } from "@/components/ui/dashboard/DashboardContext";
import { cn } from "@/lib/cn";

function DashboardShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [isCollapsed, setIsCollapsed] = useState(false);
  const { persona, setPersona, userName, roleName } = useDashboard();
  const { isAuthenticated, isLoading: isAuthLoading, user, logout } = useAuth();

  useEffect(() => {
    if (user) {
      if (user.role === "admin" && persona !== "admin") {
        setPersona("admin");
      }
    }
  }, [user, persona, setPersona]);

  if (isAuthLoading) {
    return (
      <div className="min-h-screen bg-[#F8FAFC] flex flex-col items-center justify-center p-6 text-slate-600">
        <div className="w-8 h-8 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mb-4" />
        <p className="text-xs font-semibold uppercase tracking-wider text-slate-400">Verifying session...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#E6F0FA] flex items-center justify-center p-4 relative overflow-hidden">
        {/* Background Atmosphere */}
        <div className="absolute inset-0 z-0 select-none pointer-events-none">
          <img
            src="/images/auth_sky_bg.jpg"
            alt="Security Background"
            className="w-full h-full object-cover"
          />
        </div>
        <div className="absolute inset-0 bg-gradient-to-t from-white/30 via-transparent to-blue-900/5" />

        <div className="relative z-10 bg-white rounded-[28px] p-8 sm:p-9 max-w-md w-full shadow-[0_25px_60px_-15px_rgba(59,130,246,0.18),0_10px_30px_-5px_rgba(0,0,0,0.06)] border border-slate-100 text-center">
          <div className="w-14 h-14 bg-amber-50 border border-amber-200 text-amber-600 rounded-2xl flex items-center justify-center mx-auto mb-5 shadow-xs">
            <Lock className="w-7 h-7" />
          </div>
          <h2 className="font-heading text-2xl text-slate-900 mb-2 tracking-tight">
            Authentication Required
          </h2>
          <p className="text-xs sm:text-sm text-slate-500 mb-6 leading-relaxed">
            You must be signed in with your official government credentials to access the GyanSetu Competency & Workforce Intelligence Platform.
          </p>
          <div className="flex flex-col gap-3">
            <Link
              href={`/login?redirect=${encodeURIComponent(pathname || "/dashboard")}&notice=required`}
              className="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-semibold text-xs rounded-xl transition shadow-md hover:shadow-lg text-center"
            >
              Sign In to Continue
            </Link>
            <Link
              href="/signup"
              className="w-full py-2.5 px-4 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold text-xs rounded-xl transition border border-slate-200 text-center"
            >
              Register New Official Profile
            </Link>
          </div>
          <div className="mt-6 pt-5 border-t border-slate-100">
            <Link href="/" className="text-xs font-medium text-slate-400 hover:text-slate-700 transition">
              ← Return to Home Page
            </Link>
          </div>
        </div>
      </div>
    );
  }


  const navItems = [
    {
      name: "Dashboard",
      href: "/dashboard",
      icon: LayoutDashboard,
      active: pathname === "/dashboard",
    },
    {
      name: "Data Ingestion",
      href: "/dashboard/ingestion",
      icon: UploadCloud,
      active: pathname?.startsWith("/dashboard/ingestion"),
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

  const getPageInfo = () => {
    if (pathname === "/dashboard") {
      return { title: "Dashboard", subtitle: "Competency diagnostic overview & learning progress" };
    }
    if (pathname?.startsWith("/dashboard/ingestion")) {
      return { title: "Data Ingestion", subtitle: "Multi-modal knowledge extraction & syllabus mapping" };
    }
    if (pathname?.startsWith("/dashboard/assessments")) {
      return { title: "Assessments", subtitle: "Adaptive multi-tier diagnostic evaluations" };
    }
    if (pathname?.startsWith("/dashboard/tasks")) {
      return { title: "Practical Tasks", subtitle: "Workplace assignments & evidence records" };
    }
    if (pathname?.startsWith("/dashboard/workforce")) {
      return { title: "Workforce Analytics", subtitle: "Cadre readiness, competency distribution & gaps" };
    }
    if (pathname?.startsWith("/dashboard/map")) {
      return { title: "Competency Map", subtitle: "Hierarchical capability framework & ontology" };
    }
    return { title: "GyanSetu", subtitle: "Competency Development Platform" };
  };

  const pageInfo = getPageInfo();

  return (
    <div className="min-h-screen bg-[#F8FAFC] flex text-[#0F172A] font-body antialiased">
      {/* Mobile Sidebar Overlay */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-xs lg:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* LEFT SIDEBAR */}
      <aside
        className={cn(
          "fixed top-0 bottom-0 left-0 z-50 bg-white border-r border-slate-200 flex flex-col justify-between transition-all duration-300",
          mobileMenuOpen ? "translate-x-0 w-60" : "-translate-x-full lg:translate-x-0",
          isCollapsed && !mobileMenuOpen ? "w-20" : "w-60"
        )}
      >
        <div>
          {/* Brand Header */}
          <div className={cn("px-4 border-b border-slate-200 flex items-center h-[60px]", isCollapsed ? "justify-center" : "justify-between")}>
            <Link href="/" className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-2.5")}>
              <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center text-white font-heading text-lg font-bold shadow-xs shrink-0">
                GS
              </div>
              {!isCollapsed && (
                <div>
                  <span className="font-heading text-lg tracking-wide text-slate-900 block leading-tight">
                    GYANSETU
                  </span>
                </div>
              )}
            </Link>
            {!isCollapsed ? (
              <div className="flex items-center">
                <button
                  type="button"
                  onClick={() => setIsCollapsed(true)}
                  className="hidden lg:flex text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition"
                  title="Collapse Sidebar"
                >
                  <ChevronsLeft className="w-4 h-4" />
                </button>
                <button
                  type="button"
                  className="lg:hidden text-slate-500 hover:text-slate-800 p-1"
                  onClick={() => setMobileMenuOpen(false)}
                  aria-label="Close sidebar"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            ) : (
              <button
                type="button"
                onClick={() => setIsCollapsed(false)}
                className="hidden lg:flex text-slate-400 hover:text-slate-700 p-1.5 rounded-lg hover:bg-slate-100 transition mt-1"
                title="Expand Sidebar"
              >
                <ChevronsRight className="w-4 h-4" />
              </button>
            )}
          </div>

          {/* Navigation Links */}
          <div className="p-3 space-y-1">
            <div className={cn("px-3 py-1.5 text-[11px] font-medium text-slate-400 uppercase tracking-wider", isCollapsed ? "text-center" : "")}>
              {!isCollapsed ? "Navigation" : "Nav"}
            </div>
            {navItems.map((item) => {
              const Icon = item.icon;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setMobileMenuOpen(false)}
                  title={isCollapsed ? item.name : undefined}
                  className={cn(
                    "flex items-center px-3.5 py-2.5 rounded-xl text-sm font-medium transition relative",
                    isCollapsed ? "justify-center" : "justify-between",
                    item.active
                      ? "bg-blue-50 text-blue-700 font-semibold border-l-[3px] border-blue-600 pl-[11px]"
                      : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                  )}
                >
                  <div className={cn("flex items-center", isCollapsed ? "justify-center" : "gap-3")}>
                    <Icon
                      className={cn(
                        "w-4.5 h-4.5 shrink-0",
                        item.active ? "text-blue-600" : "text-slate-400"
                      )}
                    />
                    {!isCollapsed && <span>{item.name}</span>}
                  </div>
                  {!isCollapsed && item.badge && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 border border-slate-200">
                      {item.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3.5 border-t border-slate-200 bg-slate-50/50 space-y-1.5">
          {/* Toggle Sidebar Button */}
          <button
            type="button"
            onClick={() => setIsCollapsed(!isCollapsed)}
            className={cn("w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-sm font-medium text-slate-500 hover:text-slate-700 hover:bg-slate-100 transition", isCollapsed ? "justify-center" : "")}
            title={isCollapsed ? "Expand Sidebar" : undefined}
          >
            {isCollapsed ? <ChevronsRight className="w-4 h-4 shrink-0" /> : <ChevronsLeft className="w-4 h-4 shrink-0" />}
            {!isCollapsed && <span>Collapse Sidebar</span>}
          </button>
          
          <Link
            href="/"
            className={cn("flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-sm font-medium text-slate-600 hover:text-blue-600 hover:bg-slate-100 transition", isCollapsed ? "justify-center" : "")}
            title={isCollapsed ? "Back to Home" : undefined}
          >
            <ArrowLeft className="w-4 h-4 shrink-0" />
            {!isCollapsed && <span>Back to Home</span>}
          </Link>
          <button
            type="button"
            onClick={() => {
              logout();
              router.push("/login");
            }}
            className={cn("w-full flex items-center gap-2.5 px-3.5 py-2 rounded-xl text-sm font-medium text-rose-600 hover:text-rose-700 hover:bg-rose-50 transition", isCollapsed ? "justify-center" : "text-left")}
            title={isCollapsed ? "Sign Out" : undefined}
          >
            <LogOut className="w-4 h-4 shrink-0" />
            {!isCollapsed && <span>Sign Out</span>}
          </button>
        </div>
      </aside>

      {/* MAIN VIEWPORT CONTAINER */}
      <div className={cn("flex-1 flex flex-col min-w-0 transition-all duration-300", isCollapsed ? "lg:pl-20" : "lg:pl-60")}>
        {/* TOP BAR */}
        <header className="sticky top-0 z-30 bg-white/95 backdrop-blur-xs border-b border-slate-200 px-4 sm:px-8 h-[68px] flex items-center justify-between gap-4">
          <div className="flex items-center gap-3.5">
            <button
              type="button"
              className="lg:hidden text-slate-600 hover:text-slate-900 p-1.5"
              onClick={() => setMobileMenuOpen(true)}
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>

            <div>
              <div className="flex items-center gap-2.5">
                <h1 className="font-heading text-xl sm:text-2xl tracking-wide text-slate-900">
                  {pageInfo.title}
                </h1>
                <span className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                  Live Synced
                </span>
              </div>
              <p className="text-sm text-slate-600 hidden sm:block font-sans">
                {pageInfo.subtitle}
              </p>
            </div>
          </div>

          {/* Persona Switcher & User Avatar */}
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2.5">
              <span className="text-xs text-slate-500 font-medium hidden md:inline font-sans">Officer Profile:</span>
              <div className="flex items-center bg-slate-100 p-1 rounded-xl border border-slate-200 text-xs sm:text-sm">
                <button
                  type="button"
                  onClick={() => setPersona("jso")}
                  className={cn(
                    "px-2.5 sm:px-3 py-1.5 rounded-lg transition text-xs sm:text-sm font-semibold",
                    persona === "jso"
                      ? "bg-white text-slate-900 shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  )}
                >
                  Sample Learner
                </button>
                <button
                  type="button"
                  onClick={() => setPersona("new")}
                  className={cn(
                    "px-2.5 sm:px-3 py-1.5 rounded-lg transition text-xs sm:text-sm font-semibold",
                    persona === "new"
                      ? "bg-white text-slate-900 shadow-xs"
                      : "text-slate-600 hover:text-slate-900"
                  )}
                >
                  New Officer
                </button>
              </div>
            </div>

            <div className="w-px h-6 bg-slate-200 hidden sm:block" />

            {/* User Avatar */}
            <div 
              className="flex items-center gap-2.5 p-1 rounded-lg"
              title={`${user?.name || userName} (${user?.role || "Learner"})`}
            >
              <div className="w-8 h-8 rounded-full bg-blue-50 border border-blue-200 text-blue-700 flex items-center justify-center text-xs font-bold shrink-0">
                {initials}
              </div>
              <div className="text-left hidden xl:block">
                <div className="text-xs font-semibold text-slate-900 leading-tight truncate max-w-[120px]">
                  {user?.name || userName}
                </div>
                <div className="text-[11px] text-slate-500 leading-tight truncate max-w-[120px]">
                  {user?.role === "admin" ? "Administrator" : "Officer"}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Page Content Viewport */}
        <main className="flex-1 p-4 sm:p-8 w-full">
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
