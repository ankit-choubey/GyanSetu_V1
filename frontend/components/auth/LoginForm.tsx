"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock, AlertCircle } from "lucide-react";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import Link from "next/link";
import { ForgotPasswordModal } from "./ForgotPasswordModal";
import { UserPlus, ArrowRight } from "lucide-react";
import { cn } from "@/lib/cn";

export function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const { setPersona } = useDashboard();
  
  const redirectTarget = searchParams.get("redirect");
  const isNotice = searchParams.get("notice") === "required" || !!redirectTarget;

  const [role, setRole] = useState<"learner" | "admin">("learner");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [userNotFound, setUserNotFound] = useState(false);
  const [isForgotPasswordOpen, setIsForgotPasswordOpen] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setErrorMessage(null);
    setUserNotFound(false);

    try {
      const user = await login(email.trim(), password);

      try {
        setPersona(user.role === "admin" ? "admin" : "jso");
      } catch {
        // Dashboard context may not be mounted outside dashboard
      }

      if (redirectTarget && (user.role === "admin" || !redirectTarget.includes("workforce"))) {
        router.push(redirectTarget);
      } else if (user.role === "admin") {
        router.push("/dashboard/workforce");
      } else {
        router.push("/dashboard");
      }
    } catch (err: any) {
      const detail = err?.data?.detail || err.message || "Failed to sign in.";
      if (detail.includes("USER_NOT_FOUND")) {
        setUserNotFound(true);
      } else if (detail.includes("INVALID_PASSWORD")) {
        setErrorMessage("Incorrect password. Please verify your password or use forgot password below.");
      } else {
        setErrorMessage(detail);
      }
    } finally {
      setIsLoading(false);
    }
  };


  return (
    <div className="w-full">
      {/* Redirection Alert Banner */}
      {isNotice && (
        <div className="mb-5 p-3.5 rounded-xl bg-amber-50 border border-amber-200/80 flex items-start gap-2.5 text-xs text-amber-900 leading-relaxed shadow-xs">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
          <div>
            <span className="font-semibold block mb-0.5">Sign In Required</span>
            Please sign in to access your GyanSetu Competency Dashboard.
          </div>
        </div>
      )}

      {/* User Not Found Prompt Banner */}
      {userNotFound && (
        <div className="mb-5 p-4 rounded-xl bg-amber-50 border border-amber-200 flex flex-col gap-2.5 text-xs text-amber-900 shadow-xs">
          <div className="flex items-start gap-2">
            <AlertCircle className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold block text-slate-900 mb-0.5">No Account Found</span>
              This email is not registered in our database. Create a new official account to access your personal dashboard.
            </div>
          </div>
          <Link
            href={`/signup?email=${encodeURIComponent(email)}`}
            className="inline-flex items-center justify-center gap-1.5 px-3 py-2 rounded-lg bg-blue-600 hover:bg-blue-700 text-white font-semibold transition"
          >
            <UserPlus className="w-3.5 h-3.5" />
            <span>Create Account with this Email</span>
          </Link>
        </div>
      )}

      {/* General Error Banner */}
      {errorMessage && (
        <div className="mb-5 p-3.5 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-2.5 text-xs text-rose-800 shadow-xs">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0 mt-0.5" />
          <span>{errorMessage}</span>
        </div>
      )}

      {/* Role Toggle */}
      <div className="flex p-1 bg-slate-100 rounded-lg mb-6">
        <button
          type="button"
          onClick={() => setRole("learner")}
          className={cn(
            "flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200",
            role === "learner" 
              ? "bg-white text-slate-900 shadow-sm" 
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
          )}
        >
          Learner
        </button>
        <button
          type="button"
          onClick={() => setRole("admin")}
          className={cn(
            "flex-1 py-2 text-sm font-medium rounded-md transition-all duration-200",
            role === "admin" 
              ? "bg-white text-slate-900 shadow-sm" 
              : "text-slate-500 hover:text-slate-700 hover:bg-slate-200/50"
          )}
        >
          Administrator
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Email Field */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 block">
            Email address
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Mail className="w-4 h-4" />
            </div>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 text-slate-900 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white outline-none transition-all duration-200 sm:text-sm"
              placeholder={role === "admin" ? "admin@gov.in" : "officer@gov.in"}
            />
          </div>
        </div>

        {/* Password Field */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 block">
            Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 text-slate-900 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white outline-none transition-all duration-200 sm:text-sm"
              placeholder="••••••••"
            />
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute inset-y-0 right-0 pr-3 flex items-center text-slate-400 hover:text-slate-600 focus:outline-none"
            >
              {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
            </button>
          </div>
        </div>

        {/* Forgot Password & Options */}
        <div className="flex items-center justify-between pt-1 pb-4">
          <label className="flex items-center gap-2 cursor-pointer group">
            <input 
              type="checkbox" 
              className="w-4 h-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500/30 transition-colors"
            />
            <span className="text-sm text-slate-500 group-hover:text-slate-700 transition-colors">
              Remember me
            </span>
          </label>
          <button
            type="button"
            onClick={() => setIsForgotPasswordOpen(true)}
            className="text-sm font-medium text-blue-600 hover:text-blue-700 transition-colors"
          >
            Forgot password?
          </button>
        </div>

        {/* Submit Button with Micro-interactions */}
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={isLoading}
          className={cn(
            "w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center",
            isLoading && "opacity-80 cursor-not-allowed"
          )}
        >
          {isLoading ? (
            <motion.div 
              animate={{ rotate: 360 }}
              transition={{ repeat: Infinity, duration: 1, ease: "linear" }}
              className="w-5 h-5 border-2 border-white/20 border-t-white rounded-full"
            />
          ) : (
            "Sign In"
          )}
        </motion.button>
      </form>

      {/* Switch to Signup */}
      <div className="mt-8 pt-6 border-t border-slate-100 text-center">
        <p className="text-sm text-slate-500">
          Don't have an account?{" "}
          <Link href="/signup" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
            Sign up
          </Link>
        </p>
      </div>

      <ForgotPasswordModal
        isOpen={isForgotPasswordOpen}
        onClose={() => setIsForgotPasswordOpen(false)}
        initialEmail={email}
      />
    </div>
  );
}
