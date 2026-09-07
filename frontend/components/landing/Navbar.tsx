"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight, LogOut, User } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { useScrollDirection } from "@/hooks/useScrollDirection";
import { useReducedMotion } from "@/hooks/useReducedMotion";

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { scrollDirection, isAtTop } = useScrollDirection();
  const shouldReduceMotion = useReducedMotion();
  const { isAuthenticated, user, logout } = useAuth();

  const isHidden = !isAtTop && scrollDirection === "down";

  const dashboardTarget = user?.role === "admin" ? "/dashboard/workforce" : "/dashboard";

  const navLinks = [
    { label: "Features", href: "#features" },
    { label: "How It Works", href: "#how-it-works" },
    { label: "Technology", href: "#technology" },
    { label: "About", href: "#problem" },
  ];

  return (
    <>
      <motion.header
        initial={shouldReduceMotion ? false : { y: -64, opacity: 0 }}
        animate={{
          y: isHidden ? -64 : 0,
          opacity: 1,
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed top-0 left-0 right-0 h-16 z-50 bg-white/90 backdrop-blur-md border-b border-[#E2E8F0] transition-colors duration-200"
      >
        <div className="max-w-[1280px] h-full mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <Link
            href="/"
            className="font-heading text-2xl tracking-[0.02em] text-[#3B82F6] hover:opacity-90 transition-opacity select-none"
          >
            GYANSETU
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8">
            <Link
              href={dashboardTarget}
              className="group relative font-body text-[15px] font-medium text-[#475569] hover:text-[#0F172A] transition-colors py-1"
            >
              Dashboard
              <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#3B82F6] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
            </Link>
            {navLinks.map((link) => (
              <Link
                key={link.label}
                href={link.href}
                className="group relative font-body text-[15px] font-medium text-[#475569] hover:text-[#0F172A] transition-colors py-1"
              >
                {link.label}
                <span className="absolute bottom-0 left-0 w-full h-[2px] bg-[#3B82F6] scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
              </Link>
            ))}
          </nav>

          {/* Right Action Buttons */}
          <div className="hidden md:flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-50 border border-slate-200 text-xs">
                  <div className="w-5 h-5 rounded-full bg-blue-600 text-white flex items-center justify-center text-[10px] font-bold">
                    {user?.name?.[0] || "U"}
                  </div>
                  <span className="font-semibold text-slate-800 max-w-[110px] truncate">
                    {user?.name}
                  </span>
                  <span className="text-[10px] uppercase font-bold text-blue-600 bg-blue-50 px-1 rounded">
                    {user?.role}
                  </span>
                </div>

                <Link
                  href={dashboardTarget}
                  className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
                >
                  <span>Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>

                <button
                  type="button"
                  onClick={logout}
                  className="p-2 text-slate-400 hover:text-rose-600 transition-colors"
                  title="Sign Out"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  href="/login"
                  className="px-3.5 py-2 text-xs font-semibold text-slate-700 hover:text-blue-600 hover:bg-slate-50 rounded-lg transition"
                >
                  Sign In
                </Link>
                <Link
                  href={dashboardTarget}
                  className="inline-flex items-center gap-1.5 px-4 py-2 rounded-lg text-xs font-semibold bg-[#0F172A] hover:bg-[#1E293B] text-white transition shadow-xs"
                >
                  <span>Launch Dashboard</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Icon */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileMenuOpen(true)}
              className="p-2 text-[#475569] hover:text-[#0F172A] transition-colors"
              aria-label="Open mobile menu"
            >
              <Menu className="w-6 h-6" />
            </button>
          </div>
        </div>
      </motion.header>

      {/* Mobile Drawer Overlay */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-60 bg-black/40 backdrop-blur-xs md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          >
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="absolute top-0 right-0 bottom-0 w-[290px] bg-white border-l border-[#E2E8F0] p-6 flex flex-col justify-between shadow-2xl"
              onClick={(e) => e.stopPropagation()}
            >
              <div>
                <div className="flex items-center justify-between pb-6 border-b border-[#E2E8F0]">
                  <span className="font-heading text-2xl text-[#3B82F6]">
                    GYANSETU
                  </span>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-2 text-[#475569] hover:text-[#0F172A]"
                    aria-label="Close mobile menu"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <nav className="flex flex-col gap-4 mt-8">
                  <Link
                    href={dashboardTarget}
                    onClick={() => setMobileMenuOpen(false)}
                    className="font-body text-base font-semibold text-[#0F172A] hover:text-[#3B82F6] transition-colors py-1 flex items-center justify-between"
                  >
                    Dashboard
                    <ArrowRight className="w-4 h-4 text-[#94A3B8]" />
                  </Link>
                  {navLinks.map((link) => (
                    <Link
                      key={link.label}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="font-body text-base font-medium text-[#475569] hover:text-[#3B82F6] transition-colors py-1 flex items-center justify-between"
                    >
                      {link.label}
                      <ArrowRight className="w-4 h-4 text-[#94A3B8]" />
                    </Link>
                  ))}
                </nav>
              </div>

              <div className="flex flex-col gap-3 pt-6 border-t border-[#E2E8F0]">
                {isAuthenticated ? (
                  <>
                    <div className="text-xs text-slate-500 mb-1">
                      Logged in as <span className="font-semibold text-slate-800">{user?.name}</span> ({user?.role})
                    </div>
                    <Link
                      href={dashboardTarget}
                      onClick={() => setMobileMenuOpen(false)}
                      className="w-full text-center py-2.5 font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition"
                    >
                      Open Dashboard
                    </Link>
                    <button
                      type="button"
                      onClick={() => {
                        logout();
                        setMobileMenuOpen(false);
                      }}
                      className="w-full text-center py-2 font-medium text-rose-600 hover:bg-rose-50 rounded-lg text-sm transition border border-rose-200"
                    >
                      Sign Out
                    </button>
                  </>
                ) : (
                  <>
                    <Link
                      href="/login"
                      onClick={() => setMobileMenuOpen(false)}
                      className="w-full text-center py-2.5 font-semibold text-slate-800 hover:bg-slate-100 rounded-lg text-sm transition border border-slate-200"
                    >
                      Sign In
                    </Link>
                    <Link
                      href={dashboardTarget}
                      onClick={() => setMobileMenuOpen(false)}
                      className="w-full text-center py-2.5 font-medium bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm transition"
                    >
                      Launch Dashboard
                    </Link>
                  </>
                )}
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}

