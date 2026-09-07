"use client";

import React from "react";
import { motion } from "framer-motion";
import { UploadCloud, Database } from "lucide-react";
import { IngestionHub } from "@/components/ui/dashboard/IngestionHub";

export default function IngestionPage() {
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.1 }
    }
  };

  const itemVariants = {
    hidden: { y: 15, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { duration: 0.25, ease: "easeOut" }
    }
  };

  return (
    <motion.div 
      className="space-y-6 w-full"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* HEADER SECTION */}
      <motion.div 
        variants={itemVariants} 
        className="bg-white border border-slate-200 rounded-xl p-6 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4"
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="p-1.5 rounded-lg bg-blue-50 text-blue-700 border border-blue-100">
              <UploadCloud className="w-5 h-5" />
            </span>
            <h1 className="font-heading text-2xl text-slate-900 tracking-tight">
              Data & Knowledge Ingestion Hub
            </h1>
          </div>
          <p className="text-sm text-slate-500 font-sans max-w-3xl">
            Ingest custom courseware, official manuals, video lectures, and presentations or select targeted modules from the curriculum to generate structured multi-tier assessments.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 shrink-0 self-start md:self-center bg-slate-50 px-3 py-2 rounded-lg border border-slate-200">
          <Database className="w-4 h-4 text-slate-400" />
          <span>Status: Ready for Ingestion</span>
        </div>
      </motion.div>

      {/* FULL-WIDTH INGESTION HUB */}
      <motion.div variants={itemVariants} className="w-full">
        <IngestionHub />
      </motion.div>
    </motion.div>
  );
}
