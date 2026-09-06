"use client";

import React, { useState } from "react";
import Link from "next/link";
import { motion, AnimatePresence } from "framer-motion";
import { Menu, X, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useScrollDirection } from "@/hooks/useScrollDirection";
import { useReducedMotion } from "@/hooks/useReducedMotion";

const NAV_LINKS = [
  { label: "Features", href: "#features" },
  { label: "How It Works", href: "#how-it-works" },
  { label: "Technology", href: "#technology" },
  { label: "About", href: "#problem" },
];

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { scrollDirection, isAtTop } = useScrollDirection();
  const shouldReduceMotion = useReducedMotion();

  const isHidden = !isAtTop && scrollDirection === "down";

  return (
    <>
      <motion.header
        initial={shouldReduceMotion ? false : { y: -64, opacity: 0 }}
        animate={{
          y: isHidden ? -64 : 0,
          opacity: 1,
        }}
        transition={{ duration: 0.3, ease: "easeInOut" }}
        className="fixed top-0 left-0 right-0 h-16 z-50 bg-white/80 backdrop-blur-md border-b border-[#E2E8F0] transition-colors duration-200"
      >
        <div className="max-w-[1280px] h-full mx-auto px-6 flex items-center justify-between">
          {/* Logo */}
          <Link
            href="#"
            className="font-heading text-2xl tracking-[0.02em] text-[#3B82F6] hover:opacity-90 transition-opacity select-none"
          >
            GYANSETU
          </Link>

          {/* Desktop Nav Links */}
          <nav className="hidden md:flex items-center gap-8">
            {NAV_LINKS.map((link) => (
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
          <div className="hidden md:flex items-center gap-6">
            <Link
              href="#login"
              className="font-body text-[15px] font-medium text-[#475569] hover:text-[#0F172A] transition-colors"
            >
              Login
            </Link>
            <Button
              variant="primary"
              size="sm"
              onClick={() => {
                const el = document.getElementById("features");
                el?.scrollIntoView({ behavior: "smooth" });
              }}
            >
              Get Started
            </Button>
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
            className="fixed inset-0 z-60 bg-black/40 backdrop-blur-sm md:hidden"
            onClick={() => setMobileMenuOpen(false)}
          >
            <motion.div
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 25, stiffness: 200 }}
              className="absolute top-0 right-0 bottom-0 w-[280px] bg-white border-l border-[#E2E8F0] p-6 flex flex-col justify-between shadow-2xl"
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
                  {NAV_LINKS.map((link) => (
                    <Link
                      key={link.label}
                      href={link.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className="font-body text-lg font-medium text-[#475569] hover:text-[#3B82F6] transition-colors py-1 flex items-center justify-between"
                    >
                      {link.label}
                      <ArrowRight className="w-4 h-4 text-[#94A3B8]" />
                    </Link>
                  ))}
                </nav>
              </div>

              <div className="flex flex-col gap-3 pt-6 border-t border-[#E2E8F0]">
                <Link
                  href="#login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="w-full text-center py-2.5 font-medium text-[#475569] hover:text-[#0F172A] text-sm"
                >
                  Login
                </Link>
                <Button
                  variant="primary"
                  size="sm"
                  className="w-full justify-center"
                  onClick={() => {
                    setMobileMenuOpen(false);
                    const el = document.getElementById("features");
                    el?.scrollIntoView({ behavior: "smooth" });
                  }}
                >
                  Get Started
                </Button>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
