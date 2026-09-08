"use client";

import React, { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Sparkles, Bot, ShieldCheck, RefreshCw, MessageSquare } from "lucide-react";
import Script from "next/script";

interface AskGeminiChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
  initialPrompt?: string | null;
}

export function AskGeminiChatDrawer({
  isOpen,
  onClose,
  initialPrompt,
}: AskGeminiChatDrawerProps) {
  const [reloadKey, setReloadKey] = useState(0);

  // Close on Escape key press
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isOpen) {
        onClose();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, onClose]);

  // When closed, reset reload key so any active processes stop completely
  const handleClose = () => {
    onClose();
    setReloadKey((prev) => prev + 1);
  };

  return (
    <>
      {/* Suppress default OmniDimension floating audio/call pills and bubbles */}
      <style jsx global>{`
        #chat-helper-button-container,
        #omni-minimized-pill,
        #chat-iframe-container {
          display: none !important;
          visibility: hidden !important;
          pointer-events: none !important;
        }
      `}</style>

      {/* Script Tag as required */}
      <Script
        id="omnidimension-web-widget"
        src="https://omnidim.io/web_widget.js?secret_key=2d39775642b445f9974532e7e04acd6e"
        strategy="afterInteractive"
      />

      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={handleClose}
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50"
              aria-hidden="true"
            />

            {/* Right-Side Vertical Slide-Over Panel (Like "Ask Gemini") */}
            <motion.aside
              initial={{ x: "100%" }}
              animate={{ x: 0 }}
              exit={{ x: "100%" }}
              transition={{ type: "spring", damping: 28, stiffness: 280 }}
              className="fixed top-0 right-0 bottom-0 z-50 w-full sm:w-[440px] md:w-[480px] lg:w-[500px] h-full bg-white shadow-2xl border-l border-slate-200 flex flex-col overflow-hidden"
              role="dialog"
              aria-label="Ask GyanSetu AI Assistant"
            >
              {/* Header */}
              <div className="px-5 py-4 bg-gradient-to-r from-slate-900 via-indigo-950 to-blue-950 text-white flex items-center justify-between shrink-0 border-b border-indigo-900/50 shadow-sm">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-500 to-indigo-500 flex items-center justify-center text-white shadow-sm ring-2 ring-white/20">
                    <Sparkles className="w-4.5 h-4.5" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <h2 className="font-heading text-base font-bold tracking-tight text-white flex items-center gap-1.5">
                        <span>Ask GyanSetu AI</span>
                      </h2>
                      <span className="inline-flex items-center gap-1 px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 uppercase tracking-wider">
                        <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                        Online
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-300 font-sans mt-0.5 flex items-center gap-1">
                      <ShieldCheck className="w-3 h-3 text-indigo-300" />
                      Cadre Remediation & Statistical Advisory
                    </p>
                  </div>
                </div>

                {/* Close & Action Buttons */}
                <div className="flex items-center gap-1.5">
                  <button
                    type="button"
                    onClick={() => setReloadKey((prev) => prev + 1)}
                    className="p-1.5 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition"
                    title="Reset Session"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                  </button>

                  <button
                    type="button"
                    onClick={handleClose}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold bg-white/10 hover:bg-white/20 text-white transition border border-white/10"
                    title="Close Assistant"
                  >
                    <X className="w-4 h-4" />
                    <span>Close</span>
                  </button>
                </div>
              </div>

              {/* Sub-header: Quick Inquiries */}
              <div className="px-4 py-2.5 bg-slate-50 border-b border-slate-200 text-xs text-slate-600 flex items-center gap-2 overflow-x-auto no-scrollbar shrink-0">
                <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider shrink-0">
                  Quick Topics:
                </span>
                {[
                  "Neyman Allocation",
                  "Why was my score low?",
                  "CPI Outlier Trimming",
                  "NSSTA Practical Drills",
                ].map((chip, idx) => (
                  <span
                    key={idx}
                    className="text-[11px] font-medium bg-white text-slate-700 px-2.5 py-1 rounded-md border border-slate-200 shadow-2xs whitespace-nowrap cursor-default"
                  >
                    {chip}
                  </span>
                ))}
              </div>

              {/* Chatbot Frame (Text Only, No Audio Calls) */}
              <div className="flex-1 w-full h-full relative bg-slate-50">
                {/* 
                  We explicitly set allow="clipboard-write; clipboard-read" 
                  without "microphone *" or "autoplay *" to block audio calls.
                */}
                <iframe
                  key={reloadKey}
                  src="https://www.omnidim.io/chat-widget?secret=2d39775642b445f9974532e7e04acd6e"
                  title="GyanSetu AI Chat Assistant"
                  className="w-full h-full border-0"
                  allow="clipboard-write; clipboard-read"
                  sandbox="allow-scripts allow-same-origin allow-forms allow-popups"
                />
              </div>

              {/* Footer Note */}
              <div className="px-4 py-2 bg-white border-t border-slate-200 text-[11px] text-slate-400 text-center shrink-0 flex items-center justify-between">
                <span>Grounded with MoSPI Statistical Standards</span>
                <span className="font-mono text-[10px] text-slate-400">v2.4 Live</span>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
