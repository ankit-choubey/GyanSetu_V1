"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { Eye, EyeOff, Mail, Lock, User } from "lucide-react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import Link from "next/link";
import { cn } from "@/lib/cn";

export function SignupForm() {
  const router = useRouter();
  const { login } = useAuth();
  const { setPersona } = useDashboard();
  
  const [role, setRole] = useState<"learner" | "admin">("learner");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (password !== confirmPassword) {
      alert("Passwords do not match");
      return;
    }

    setIsLoading(true);

    setTimeout(() => {
      login(role, email, name);
      try {
        setPersona(role === "admin" ? "admin" : "new"); 
      } catch {
        // Outside dashboard
      }
      if (role === "admin") {
        router.push("/dashboard/workforce");
      } else {
        router.push("/dashboard");
      }
    }, 600);
  };


  return (
    <div className="w-full">
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
        {/* Name Field */}
        <div className="space-y-1.5">
          <label className="text-sm font-medium text-slate-700 block">
            Full Name
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <User className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="w-full pl-10 pr-4 py-2.5 bg-slate-50 border border-slate-200 text-slate-900 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white outline-none transition-all duration-200 sm:text-sm"
              placeholder="John Doe"
            />
          </div>
        </div>

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
        
        {/* Confirm Password Field */}
        <div className="space-y-1.5 pb-2">
          <label className="text-sm font-medium text-slate-700 block">
            Confirm Password
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-slate-400">
              <Lock className="w-4 h-4" />
            </div>
            <input
              type={showPassword ? "text" : "password"}
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              className="w-full pl-10 pr-10 py-2.5 bg-slate-50 border border-slate-200 text-slate-900 rounded-lg focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 focus:bg-white outline-none transition-all duration-200 sm:text-sm"
              placeholder="••••••••"
            />
          </div>
        </div>

        {/* Submit Button with Micro-interactions */}
        <motion.button
          whileHover={{ scale: 1.01 }}
          whileTap={{ scale: 0.98 }}
          type="submit"
          disabled={isLoading}
          className={cn(
            "w-full py-2.5 px-4 bg-slate-900 hover:bg-slate-800 text-white font-medium rounded-lg shadow-md hover:shadow-lg transition-all duration-200 flex items-center justify-center mt-2",
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
            "Create Account"
          )}
        </motion.button>
      </form>

      {/* Switch to Login */}
      <div className="mt-6 pt-5 border-t border-slate-100 text-center">
        <p className="text-sm text-slate-500">
          Already have an account?{" "}
          <Link href="/login" className="font-medium text-blue-600 hover:text-blue-700 transition-colors">
            Sign in
          </Link>
        </p>
      </div>
    </div>
  );
}
