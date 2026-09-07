"use client";

import React from "react";
import { motion } from "framer-motion";
import Link from "next/link";
import Image from "next/image";
import { ArrowLeft } from "lucide-react";

export function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen w-full relative flex items-center justify-center overflow-hidden bg-[#E6F0FA]">
      {/* Pristine Ethereal Sky & Cloud Background */}
      <div className="absolute inset-0 z-0 select-none pointer-events-none">
        <Image
          src="/images/auth_sky_bg.jpg"
          alt="GyanSetu Official Statistical Intelligence"
          fill
          priority
          className="object-cover object-center"
        />
        {/* Gentle daytime atmospheric gradient */}
        <div className="absolute inset-0 bg-gradient-to-t from-white/20 via-transparent to-blue-900/5" />
      </div>

      {/* Back to Home Link */}
      <Link 
        href="/"
        className="absolute top-6 left-6 z-20 flex items-center gap-2 text-xs sm:text-sm font-semibold text-slate-700 hover:text-slate-900 bg-white/80 hover:bg-white px-4 py-2 rounded-full border border-white shadow-[0_2px_8px_rgba(0,0,0,0.06)] backdrop-blur-md transition-all duration-200"
      >
        <ArrowLeft className="w-4 h-4" />
        Back to Home
      </Link>

      {/* Centered Auth Card */}
      <div className="z-10 w-full max-w-md px-4 relative my-8">

        {/* 3D Elevated Solid White Card (matching reference style) */}
        <motion.div
          initial={{ opacity: 0, y: 20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          transition={{ duration: 0.5, ease: "easeOut" }}
          className="bg-white rounded-[28px] p-8 sm:p-9 shadow-[0_25px_60px_-15px_rgba(59,130,246,0.18),0_10px_30px_-5px_rgba(0,0,0,0.06),0_0_0_1px_rgba(255,255,255,0.9)] border border-slate-100/80"
        >
          {/* Logo / Brand Header */}
          <div className="flex flex-col items-center justify-center mb-7">
            <div className="w-13 h-13 rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 flex items-center justify-center text-white font-heading text-2xl font-bold shadow-lg shadow-blue-500/25 mb-4 border border-white/20">
              GS
            </div>
            <h1 className="font-heading text-2xl sm:text-[26px] tracking-tight text-slate-900">
              Welcome to GyanSetu
            </h1>
            <p className="text-xs sm:text-sm text-slate-500 mt-1 text-center px-2">
              Empowering India&apos;s Official Statistical Workforce
            </p>
          </div>

          {children}

        </motion.div>
        
        {/* Footer */}
        <div className="mt-7 text-center text-xs text-slate-600 font-medium drop-shadow-[0_1px_2px_rgba(255,255,255,0.8)]">
          <p>© {new Date().getFullYear()} Ministry of Statistics and Programme Implementation</p>
          <p className="mt-1 text-[11px] text-slate-500">Government of India • Authorized Access Only</p>
        </div>
      </div>
    </div>
  );
}

