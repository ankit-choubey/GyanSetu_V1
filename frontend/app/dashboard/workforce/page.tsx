"use client";

import React, { useState, useMemo } from "react";
import { motion } from "framer-motion";
import workforceData from "@/lib/mock/workforce-mock.json";
import { AdminAnalyticsResponse } from "@/lib/api/types";
import { WorkforceStatCards } from "@/components/ui/workforce/WorkforceStatCards";
import { StatusDistributionDonut } from "@/components/ui/workforce/StatusDistributionDonut";
import { CompetencyComparisonChart } from "@/components/ui/workforce/CompetencyComparisonChart";
import { CompetencyAnalyticsTable } from "@/components/ui/workforce/CompetencyAnalyticsTable";
import { SandboxBadge } from "@/components/ui/dashboard/SandboxBadge";
import { ShieldCheck } from "lucide-react";

export default function WorkforcePage() {
  const [data] = useState<AdminAnalyticsResponse>(
    workforceData as AdminAnalyticsResponse
  );

  const stats = useMemo(() => {
    const competencies = data.competencies || [];
    const totalLearners = competencies.length > 0 ? competencies[0].learner_count : 0;
    const avgMastery =
      competencies.length > 0
        ? competencies.reduce((sum, c) => sum + c.average_mastery, 0) /
          competencies.length
        : 0;
    const assessedCount = competencies.reduce((sum, c) => sum + c.assessed_count, 0);
    const totalEvaluations = competencies.reduce((sum, c) => sum + c.learner_count, 0);
    const totalEvidence = competencies.reduce((sum, c) => sum + c.total_evidence, 0);

    return {
      totalLearners,
      avgMastery,
      assessedCount,
      totalEvaluations,
      totalEvidence,
    };
  }, [data]);

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: { staggerChildren: 0.05 },
    },
  };

  const itemVariants = {
    hidden: { y: 20, opacity: 0 },
    visible: {
      y: 0,
      opacity: 1,
      transition: { type: "spring", stiffness: 400, damping: 30 },
    },
  };

  return (
    <motion.div 
      className="space-y-8 pb-12 w-full"
      variants={containerVariants}
      initial="hidden"
      animate="visible"
    >
      {/* Header */}
      <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
              Workforce Overview
            </h2>
            <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-semibold bg-indigo-50 text-indigo-700 border border-indigo-200 uppercase tracking-wider">
              <ShieldCheck className="w-3 h-3 text-indigo-600" />
              Admin View
            </span>
            <SandboxBadge label="DEMO DATA" />
          </div>
          <p className="text-sm text-slate-500 font-sans">
            Aggregate competency calibration and syllabus progress across cadre officers
          </p>
        </div>
      </motion.div>

      {/* ROW 1: STAT CARDS */}
      <motion.div variants={itemVariants}>
        <WorkforceStatCards
          totalLearners={stats.totalLearners}
          avgMastery={stats.avgMastery}
          assessedCount={stats.assessedCount}
          totalEvaluations={stats.totalEvaluations}
          totalEvidence={stats.totalEvidence}
        />
      </motion.div>

      {/* ROW 2: CHARTS (DONUT COL 5 + COMPARISON COL 7) */}
      <motion.section variants={itemVariants} className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-5 flex flex-col">
          <StatusDistributionDonut
            competencies={data.competencies}
            className="h-full"
          />
        </div>
        <div className="lg:col-span-7 flex flex-col">
          <CompetencyComparisonChart
            competencies={data.competencies}
            className="h-full"
          />
        </div>
      </motion.section>

      {/* ROW 3: COMPETENCY ANALYTICS TABLE */}
      <motion.section variants={itemVariants} aria-labelledby="analytics-table-heading">
        <h2 id="analytics-table-heading" className="sr-only">
          Competency Analytics Table
        </h2>
        <CompetencyAnalyticsTable competencies={data.competencies} />
      </motion.section>
    </motion.div>
  );
}
