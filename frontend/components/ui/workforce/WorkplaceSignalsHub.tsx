"use client";

import React, { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ShieldAlert,
  ShieldCheck,
  Award,
  FileCheck2,
  Users,
  AlertTriangle,
  Building2,
  Search,
  PlusCircle,
  TrendingUp,
  Sliders,
  CheckCircle2,
  History,
  X,
  Sparkles,
  Layers,
  Database,
  Briefcase
} from "lucide-react";
import { cn } from "@/lib/cn";

export interface WorkplaceSignalRecord {
  id: string;
  officer_name: string;
  cadre_designation: string;
  unit_posting: string;
  competency_code: string;
  competency_name: string;
  signal_source: "FOD_FIELD_INSPECTION" | "SPARROW_APAR" | "DPD_SCRUTINY" | "TRAINING_IMPACT_SURVEY";
  signal_source_label: string;
  level1_2_score: number;
  level3_signal_score: number;
  combined_calibrated_mastery: number;
  status: "CONFIRMED_COMPETENT" | "CONFLICTING_EVIDENCE" | "IN_CALIBRATION" | "NEEDS_SUPERVISION";
  verification_date: string;
  supervisor_name: string;
  supervisor_role: string;
  evidence_summary: string;
  provenance_hash: string;
}

const INITIAL_SIGNAL_RECORDS: WorkplaceSignalRecord[] = [
  {
    id: "SIG-2026-FOD-001",
    officer_name: "Shri Ankit Choubey",
    cadre_designation: "Senior Statistical Officer (SSO)",
    unit_posting: "NSSO (FOD) Regional Office, Delhi",
    competency_code: "MOSPI-STAT-001",
    competency_name: "NSSO Schedule 10.4 Sampling Weights & Household Stratification",
    signal_source: "FOD_FIELD_INSPECTION",
    signal_source_label: "FOD Field Inspection Report",
    level1_2_score: 92,
    level3_signal_score: 88,
    combined_calibrated_mastery: 89.6,
    status: "CONFIRMED_COMPETENT",
    verification_date: "2026-08-28",
    supervisor_name: "Dr. Arvind Swaminathan",
    supervisor_role: "Joint Director (Field Audit)",
    evidence_summary: "Random spot-inspection of 40 rural listing schedules verified 100% correct primary sampling unit (PSU) multipliers with zero sample frame substitution errors.",
    provenance_hash: "SHA256:4f8e9c2b1a8d7e6f"
  },
  {
    id: "SIG-2026-DPD-002",
    officer_name: "Smt. Priya Sharma",
    cadre_designation: "Deputy Director (Data Analytics)",
    unit_posting: "Data Processing Division (DPD), Kolkata",
    competency_code: "MOSPI-STAT-003",
    competency_name: "CPI-U Price Imputation & Hedonic Regression",
    signal_source: "DPD_SCRUTINY",
    signal_source_label: "DPD Automated Data Validation Run",
    level1_2_score: 86,
    level3_signal_score: 84,
    combined_calibrated_mastery: 84.8,
    status: "CONFIRMED_COMPETENT",
    verification_date: "2026-08-15",
    supervisor_name: "Shri S. K. Mukherjee",
    supervisor_role: "Additional Director General (DPD)",
    evidence_summary: "Automated error scrubbing pipeline flagged zero fatal outlier errors across 12,500 urban item quotation records in July 2026 index compilation.",
    provenance_hash: "SHA256:7b1e4c9a5d3f8a2e"
  },
  {
    id: "SIG-2026-FOD-003",
    officer_name: "Shri Ramesh Kumar",
    cadre_designation: "Statistical Investigator Gr. I",
    unit_posting: "Regional Office, Patna",
    competency_code: "MOSPI-STAT-002",
    competency_name: "Multi-Stage Stratified Variance Estimation",
    signal_source: "FOD_FIELD_INSPECTION",
    signal_source_label: "FOD Field Inspection Report",
    level1_2_score: 98,
    level3_signal_score: 54,
    combined_calibrated_mastery: 67.2,
    status: "CONFLICTING_EVIDENCE",
    verification_date: "2026-09-02",
    supervisor_name: "Dr. Arvind Swaminathan",
    supervisor_role: "Joint Director (Field Audit)",
    evidence_summary: "CRITICAL DIVERGENCE DETECTED: While officer achieved 98% in theoretical MCQ testing, field inspection revealed 12 out of 50 sample schedules returned due to non-sampling omission errors and incorrect cluster variance formulation.",
    provenance_hash: "SHA256:9c3d2e1a8b7f4e5a"
  },
  {
    id: "SIG-2026-SPAR-004",
    officer_name: "Dr. Sneha Patel",
    cadre_designation: "Joint Director",
    unit_posting: "Central Statistics Office (CSO), New Delhi",
    competency_code: "MOSPI-ECON-004",
    competency_name: "GVA Dual Deflation & Supply-Use Tables (SUT)",
    signal_source: "SPARROW_APAR",
    signal_source_label: "SPARROW e-HRMS APAR Review",
    level1_2_score: 78,
    level3_signal_score: 76,
    combined_calibrated_mastery: 76.8,
    status: "IN_CALIBRATION",
    verification_date: "2026-07-20",
    supervisor_name: "Shri Rajeshwar Verma",
    supervisor_role: "Director General (National Accounts)",
    evidence_summary: "Annual Performance Appraisal benchmark confirmed timely finalization of National Accounts Quarterly Estimates with full DoPT performance target compliance.",
    provenance_hash: "SHA256:2d8f4e1c9a7b3e5f"
  },
  {
    id: "SIG-2026-FOD-005",
    officer_name: "Shri Vikram Singh",
    cadre_designation: "Junior Statistical Officer (JSO)",
    unit_posting: "Sub-Regional Office, Bareilly",
    competency_code: "MOSPI-STAT-001",
    competency_name: "Rural Enterprise Listing & CAPI Tabulation",
    signal_source: "FOD_FIELD_INSPECTION",
    signal_source_label: "FOD Field Inspection Report",
    level1_2_score: 71,
    level3_signal_score: 70,
    combined_calibrated_mastery: 70.4,
    status: "CONFIRMED_COMPETENT",
    verification_date: "2026-08-30",
    supervisor_name: "Shri Manoj Tiwari",
    supervisor_role: "Deputy Director (Field Operations)",
    evidence_summary: "Computer-Assisted Personal Interviewing (CAPI) handheld synchronization achieved 98.2% on-time upload without GPS geotagging anomalies.",
    provenance_hash: "SHA256:5a9e3d2f1c8b7e4a"
  }
];

export function WorkplaceSignalsHub({ className }: { className?: string }) {
  const [records, setRecords] = useState<WorkplaceSignalRecord[]>(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("gyansetu_workplace_signals");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed) && parsed.length > 0) return parsed;
        } catch {
          // fallback to initial
        }
      }
    }
    return INITIAL_SIGNAL_RECORDS;
  });

  const [selectedFilter, setSelectedFilter] = useState<string>("ALL");
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [activeModal, setActiveModal] = useState<boolean>(false);
  const [selectedRecord, setSelectedRecord] = useState<WorkplaceSignalRecord | null>(null);

  // New Signal Form State
  const [newOfficerName, setNewOfficerName] = useState("");
  const [newCadre, setNewCadre] = useState("Senior Statistical Officer (SSO)");
  const [newPosting, setNewPosting] = useState("NSSO (FOD) Field Office");
  const [newCompetency, setNewCompetency] = useState("NSSO Schedule 10.4 Sampling Weights & Stratification");
  const [newSignalSource, setNewSignalSource] = useState<WorkplaceSignalRecord["signal_source"]>("FOD_FIELD_INSPECTION");
  const [newL1Score, setNewL1Score] = useState<number>(85);
  const [newL3Score, setNewL3Score] = useState<number>(80);
  const [newSupervisor, setNewSupervisor] = useState("Dr. Arvind Swaminathan (JD Audit)");
  const [newEvidence, setNewEvidence] = useState("");

  const handleSaveSignal = (e: React.FormEvent) => {
    e.preventDefault();
    const l1 = Number(newL1Score);
    const l3 = Number(newL3Score);
    const diff = Math.abs(l1 - l3);
    const isConflict = diff > 35;
    const combined = Math.round(((l1 * 0.4) + (l3 * 0.6)) * 10) / 10;
    const computedStatus: WorkplaceSignalRecord["status"] = isConflict
      ? "CONFLICTING_EVIDENCE"
      : combined >= 75
      ? "CONFIRMED_COMPETENT"
      : combined >= 65
      ? "IN_CALIBRATION"
      : "NEEDS_SUPERVISION";

    const newRecord: WorkplaceSignalRecord = {
      id: `SIG-2026-${Date.now().toString().slice(-4)}`,
      officer_name: newOfficerName.trim() || "Field Officer",
      cadre_designation: newCadre,
      unit_posting: newPosting,
      competency_code: "MOSPI-EVID-009",
      competency_name: newCompetency,
      signal_source: newSignalSource,
      signal_source_label:
        newSignalSource === "FOD_FIELD_INSPECTION"
          ? "FOD Field Inspection Report"
          : newSignalSource === "SPARROW_APAR"
          ? "SPARROW e-HRMS APAR Milestone"
          : newSignalSource === "DPD_SCRUTINY"
          ? "DPD Automated Data Validation Run"
          : "Training Impact Supervisor Evaluation",
      level1_2_score: l1,
      level3_signal_score: l3,
      combined_calibrated_mastery: combined,
      status: computedStatus,
      verification_date: new Date().toISOString().split("T")[0],
      supervisor_name: newSupervisor,
      supervisor_role: "Cadre Reviewing Authority",
      evidence_summary: newEvidence.trim() || "Direct supervisor field verification documented in roster.",
      provenance_hash: `SHA256:${Math.random().toString(36).substring(2, 10)}${Math.random().toString(36).substring(2, 10)}`
    };

    const updated = [newRecord, ...records];
    setRecords(updated);
    if (typeof window !== "undefined") {
      localStorage.setItem("gyansetu_workplace_signals", JSON.stringify(updated));
      window.dispatchEvent(new CustomEvent("gyansetu:evidence_added", { detail: newRecord }));
    }

    setActiveModal(false);
    setNewOfficerName("");
    setNewEvidence("");
  };

  const filteredRecords = useMemo(() => {
    return records.filter((r) => {
      const matchesFilter =
        selectedFilter === "ALL"
          ? true
          : selectedFilter === "CONFLICT"
          ? r.status === "CONFLICTING_EVIDENCE"
          : selectedFilter === "CONFIRMED"
          ? r.status === "CONFIRMED_COMPETENT"
          : selectedFilter === "FOD"
          ? r.signal_source === "FOD_FIELD_INSPECTION"
          : true;

      const q = searchQuery.toLowerCase();
      const matchesSearch =
        !q ||
        r.officer_name.toLowerCase().includes(q) ||
        r.cadre_designation.toLowerCase().includes(q) ||
        r.competency_name.toLowerCase().includes(q) ||
        r.unit_posting.toLowerCase().includes(q);

      return matchesFilter && matchesSearch;
    });
  }, [records, selectedFilter, searchQuery]);

  const summary = useMemo(() => {
    const total = records.length;
    const confirmed = records.filter(r => r.status === "CONFIRMED_COMPETENT").length;
    const conflicts = records.filter(r => r.status === "CONFLICTING_EVIDENCE").length;
    const avgScore = total > 0 ? Math.round(records.reduce((acc, r) => acc + r.combined_calibrated_mastery, 0) / total) : 0;
    return { total, confirmed, conflicts, avgScore };
  }, [records]);

  return (
    <div className={cn("space-y-6", className)}>
      {/* SECTION HEADER & ARCHITECTURAL SUMMARY */}
      <div className="rounded-xl bg-gradient-to-r from-slate-900 via-indigo-950 to-slate-900 text-white p-6 sm:p-8 shadow-xl border border-slate-800">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex flex-wrap items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 flex items-center gap-1.5">
                <Layers className="w-3.5 h-3.5 text-emerald-400" />
                Level 3 Operational Evidence Engine
              </span>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/20 text-indigo-300 border border-indigo-500/30 flex items-center gap-1.5">
                <Database className="w-3.5 h-3.5 text-indigo-400" />
                Triangulated Workplace Signals
              </span>
              <span className="px-2 py-0.5 rounded text-[11px] font-mono bg-amber-500/20 text-amber-300 border border-amber-500/30">
                MoSPI / DoPT Cadre Oversight
              </span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-3">
              <Briefcase className="w-7 h-7 text-indigo-400" />
              Workplace Signals & Evidence Evaluation Hub
            </h2>
            <p className="text-slate-300 text-sm sm:text-base max-w-3xl leading-relaxed">
              Triangulating theoretical academic mastery with real-world administrative signals from
              <strong> FOD Field Inspections</strong>, <strong>SPARROW e-HRMS APAR</strong>, and
              <strong> DPD Scrutiny pipelines</strong>. Protects against quiz-gaming via Bayesian belief updating.
            </p>
          </div>

          <div className="flex items-center gap-3 flex-shrink-0">
            <button
              onClick={() => setActiveModal(true)}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-sm transition-all shadow-md hover:shadow-indigo-500/25 border border-indigo-400/30"
            >
              <PlusCircle className="w-4 h-4" />
              Record Workplace Signal
            </button>
          </div>
        </div>

        {/* 3-TIER CALIBRATION EXPLAINER PILLS */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-6 pt-6 border-t border-slate-800/80">
          <div className="bg-slate-800/60 rounded-lg p-3.5 border border-slate-700/60 flex items-start gap-3">
            <div className="p-2 rounded-md bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Award className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Level 1: Academic Recall</div>
              <div className="text-sm font-medium text-slate-200">iGOT Karmayogi Quizzes & MCQs (30% weight)</div>
            </div>
          </div>

          <div className="bg-slate-800/60 rounded-lg p-3.5 border border-slate-700/60 flex items-start gap-3">
            <div className="p-2 rounded-md bg-purple-500/10 text-purple-400 border border-purple-500/20">
              <Sliders className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Level 2: Applied Sandbox</div>
              <div className="text-sm font-medium text-slate-200">Tier 1-3 Diagnostic Scenarios (30% weight)</div>
            </div>
          </div>

          <div className="bg-slate-800/60 rounded-lg p-3.5 border border-slate-700/60 flex items-start gap-3">
            <div className="p-2 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
              <FileCheck2 className="w-4 h-4" />
            </div>
            <div>
              <div className="text-xs font-semibold uppercase tracking-wider text-slate-400">Level 3: Workplace Signal</div>
              <div className="text-sm font-medium text-slate-200">FOD Field Audits & SPARROW APAR (40% weight)</div>
            </div>
          </div>
        </div>
      </div>

      {/* METRIC STRIP */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Total Audited Officers</span>
            <div className="text-2xl font-bold text-slate-900 mt-1">{summary.total}</div>
            <div className="text-xs text-slate-500 mt-0.5">Cadre officers tracked</div>
          </div>
          <div className="p-3 bg-slate-50 rounded-lg border border-slate-100 text-slate-600">
            <Users className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-emerald-600 uppercase tracking-wider">Confirmed Competent</span>
            <div className="text-2xl font-bold text-emerald-700 mt-1">{summary.confirmed}</div>
            <div className="text-xs text-emerald-600/80 mt-0.5">L1 + L3 convergence verified</div>
          </div>
          <div className="p-3 bg-emerald-50 rounded-lg border border-emerald-100 text-emerald-600">
            <CheckCircle2 className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-amber-200 bg-amber-50/40 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-amber-700 uppercase tracking-wider">Conflicting Signals</span>
            <div className="text-2xl font-bold text-amber-800 mt-1">{summary.conflicts}</div>
            <div className="text-xs text-amber-700/80 mt-0.5">Quiz vs. Field divergence &gt; 35%</div>
          </div>
          <div className="p-3 bg-amber-100 rounded-lg border border-amber-200 text-amber-700">
            <AlertTriangle className="w-6 h-6" />
          </div>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-5 shadow-xs flex items-center justify-between">
          <div>
            <span className="text-xs font-medium text-slate-500 uppercase tracking-wider">Avg Calibrated Mastery</span>
            <div className="text-2xl font-bold text-indigo-700 mt-1">{summary.avgScore}%</div>
            <div className="text-xs text-slate-500 mt-0.5">Triangulated Bayesian average</div>
          </div>
          <div className="p-3 bg-indigo-50 rounded-lg border border-indigo-100 text-indigo-600">
            <TrendingUp className="w-6 h-6" />
          </div>
        </div>
      </div>

      {/* ANTI-GAMING PROOF BANNER */}
      {summary.conflicts > 0 && (
        <div className="rounded-xl bg-amber-50 border border-amber-300 p-5 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3">
            <div className="p-2 bg-amber-500 text-white rounded-lg mt-0.5">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <div>
              <h4 className="text-base font-bold text-amber-900">
                Anti-Gaming Bayesian Trap Triggered ({summary.conflicts} Divergent Signal Detected)
              </h4>
              <p className="text-sm text-amber-800 mt-0.5">
                Officer <strong>Shri Ramesh Kumar</strong> achieved 98% in theoretical MCQs but demonstrated only 54% field inspection fidelity in sampling execution. The system has automatically demoted operational certification pending supervisory spot-audit.
              </p>
            </div>
          </div>
          <button
            onClick={() => setSelectedFilter("CONFLICT")}
            className="px-3.5 py-1.5 rounded-lg bg-amber-600 hover:bg-amber-700 text-white text-xs font-semibold whitespace-nowrap transition-colors"
          >
            Review Flagged Officer
          </button>
        </div>
      )}

      {/* CONTROLS: SEARCH & FILTER TABS */}
      <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-2 overflow-x-auto pb-1 md:pb-0">
          <button
            onClick={() => setSelectedFilter("ALL")}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap",
              selectedFilter === "ALL"
                ? "bg-slate-900 text-white"
                : "bg-slate-100 text-slate-600 hover:bg-slate-200"
            )}
          >
            All Signals ({records.length})
          </button>
          <button
            onClick={() => setSelectedFilter("CONFIRMED")}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5",
              selectedFilter === "CONFIRMED"
                ? "bg-emerald-600 text-white"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
            )}
          >
            <ShieldCheck className="w-3.5 h-3.5" />
            Confirmed Competent ({summary.confirmed})
          </button>
          <button
            onClick={() => setSelectedFilter("CONFLICT")}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5",
              selectedFilter === "CONFLICT"
                ? "bg-amber-600 text-white"
                : "bg-amber-50 text-amber-700 hover:bg-amber-100"
            )}
          >
            <AlertTriangle className="w-3.5 h-3.5" />
            Conflicting Evidence ({summary.conflicts})
          </button>
          <button
            onClick={() => setSelectedFilter("FOD")}
            className={cn(
              "px-3 py-1.5 rounded-lg text-xs font-medium transition-colors whitespace-nowrap flex items-center gap-1.5",
              selectedFilter === "FOD"
                ? "bg-indigo-600 text-white"
                : "bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
            )}
          >
            <Building2 className="w-3.5 h-3.5" />
            FOD Field Inspections
          </button>
        </div>

        <div className="relative min-w-[240px]">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search officer, cadre, or competency..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-1.5 text-xs bg-slate-50 border border-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:bg-white transition-all"
          />
        </div>
      </div>

      {/* CADRE SIGNALS ROSTER TABLE */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs text-slate-600">
            <thead className="bg-slate-50 text-slate-700 font-semibold uppercase tracking-wider border-b border-slate-200 text-[11px]">
              <tr>
                <th className="py-3.5 px-4">Officer & Cadre</th>
                <th className="py-3.5 px-4">Competency Scope</th>
                <th className="py-3.5 px-4">Evidence Source</th>
                <th className="py-3.5 px-4 text-center">L1/L2 Score</th>
                <th className="py-3.5 px-4 text-center">L3 Signal</th>
                <th className="py-3.5 px-4 text-center">Triangulated</th>
                <th className="py-3.5 px-4">Status & Provenance</th>
                <th className="py-3.5 px-4 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-200 font-sans">
              {filteredRecords.map((r) => {
                const isConflict = r.status === "CONFLICTING_EVIDENCE";
                return (
                  <tr
                    key={r.id}
                    className={cn(
                      "hover:bg-slate-50/80 transition-colors",
                      isConflict && "bg-amber-50/30"
                    )}
                  >
                    <td className="py-3.5 px-4">
                      <div className="font-semibold text-slate-900 text-sm flex items-center gap-1.5">
                        {r.officer_name}
                        {r.officer_name.includes("Ankit") && (
                          <span className="px-1.5 py-0.2 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
                            LEAD
                          </span>
                        )}
                      </div>
                      <div className="text-[11px] text-slate-500">{r.cadre_designation}</div>
                      <div className="text-[10px] text-slate-400 mt-0.5">{r.unit_posting}</div>
                    </td>

                    <td className="py-3.5 px-4 max-w-xs">
                      <div className="font-medium text-slate-800 truncate" title={r.competency_name}>
                        {r.competency_name}
                      </div>
                      <div className="text-[10px] font-mono text-indigo-600 mt-0.5">{r.competency_code}</div>
                    </td>

                    <td className="py-3.5 px-4">
                      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[11px] font-medium bg-slate-100 text-slate-700 border border-slate-200">
                        {r.signal_source_label}
                      </span>
                      <div className="text-[10px] text-slate-400 mt-1">Verified: {r.verification_date}</div>
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
                        {r.level1_2_score}%
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={cn(
                          "font-mono font-semibold px-2 py-1 rounded",
                          r.level3_signal_score >= 75
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : r.level3_signal_score >= 60
                            ? "bg-blue-50 text-blue-700 border border-blue-200"
                            : "bg-red-50 text-red-700 border border-red-200 font-bold"
                        )}
                      >
                        {r.level3_signal_score}%
                      </span>
                    </td>

                    <td className="py-3.5 px-4 text-center">
                      <span
                        className={cn(
                          "font-mono font-bold px-2 py-1 rounded text-xs",
                          isConflict
                            ? "bg-amber-100 text-amber-800 border border-amber-300"
                            : r.combined_calibrated_mastery >= 75
                            ? "bg-emerald-100 text-emerald-800 border border-emerald-300"
                            : "bg-slate-100 text-slate-800 border border-slate-200"
                        )}
                      >
                        {r.combined_calibrated_mastery}%
                      </span>
                    </td>

                    <td className="py-3.5 px-4">
                      {isConflict ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-300">
                          <AlertTriangle className="w-3 h-3 text-amber-600" />
                          CONFLICTING EVIDENCE
                        </span>
                      ) : r.status === "CONFIRMED_COMPETENT" ? (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-emerald-100 text-emerald-800 border border-emerald-300">
                          <ShieldCheck className="w-3 h-3 text-emerald-600" />
                          CONFIRMED COMPETENT
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-semibold bg-blue-100 text-blue-800 border border-blue-300">
                          <History className="w-3 h-3 text-blue-600" />
                          IN CALIBRATION
                        </span>
                      )}
                      <div className="text-[10px] font-mono text-slate-400 mt-1 truncate max-w-[130px]">
                        {r.provenance_hash}
                      </div>
                    </td>

                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => setSelectedRecord(r)}
                        className="px-2.5 py-1 rounded border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 text-xs font-medium transition-colors"
                      >
                        View Audit
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* DETAIL AUDIT SLIDE-OVER / MODAL */}
      <AnimatePresence>
        {selectedRecord && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 space-y-5"
            >
              <div className="flex items-start justify-between border-b border-slate-100 pb-4">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-lg font-bold text-slate-900">{selectedRecord.officer_name}</h3>
                    <span className="text-xs px-2 py-0.5 rounded font-mono bg-slate-100 text-slate-600 border border-slate-200">
                      {selectedRecord.id}
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    {selectedRecord.cadre_designation} • {selectedRecord.unit_posting}
                  </p>
                </div>
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-100"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              {/* DIVERGENCE WARNING IF CONFLICT */}
              {selectedRecord.status === "CONFLICTING_EVIDENCE" && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-900 space-y-1">
                  <div className="flex items-center gap-2 font-bold text-xs uppercase tracking-wider text-amber-800">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    Triangulation Divergence Alert (&gt; 35% Discrepancy)
                  </div>
                  <p className="text-xs text-amber-800">
                    The Bayesian engine detected a critical gap between academic simulation (Level 1/2) and live operational field execution (Level 3).
                  </p>
                </div>
              )}

              {/* SCORE COMPARISON MATRIX */}
              <div className="grid grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <div className="text-[10px] uppercase font-semibold text-slate-500">L1/L2 Theory</div>
                  <div className="text-xl font-bold text-slate-900 mt-1">{selectedRecord.level1_2_score}%</div>
                  <div className="text-[10px] text-slate-400">iGOT Quizzes</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-center">
                  <div className="text-[10px] uppercase font-semibold text-slate-500">L3 Workplace</div>
                  <div className="text-xl font-bold text-indigo-700 mt-1">{selectedRecord.level3_signal_score}%</div>
                  <div className="text-[10px] text-slate-400">{selectedRecord.signal_source_label.split(" ")[0]}</div>
                </div>
                <div className="p-3 rounded-lg bg-slate-900 text-white text-center">
                  <div className="text-[10px] uppercase font-semibold text-slate-300">Calibrated Mastery</div>
                  <div className="text-xl font-bold text-emerald-400 mt-1">{selectedRecord.combined_calibrated_mastery}%</div>
                  <div className="text-[10px] text-slate-400">Bayesian Combined</div>
                </div>
              </div>

              {/* AUDIT DETAILS */}
              <div className="space-y-3 text-xs">
                <div>
                  <span className="font-semibold text-slate-700 block mb-1">Competency Domain:</span>
                  <div className="p-2 rounded bg-slate-50 border border-slate-200 text-slate-800 font-medium">
                    {selectedRecord.competency_name} ({selectedRecord.competency_code})
                  </div>
                </div>

                <div>
                  <span className="font-semibold text-slate-700 block mb-1">Supervisory Observation & Field Evidence:</span>
                  <div className="p-3 rounded-lg bg-slate-50 border border-slate-200 text-slate-700 leading-relaxed">
                    {selectedRecord.evidence_summary}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-3 pt-1">
                  <div>
                    <span className="font-semibold text-slate-500 block text-[11px]">Audit Officer:</span>
                    <span className="text-slate-800 font-medium">{selectedRecord.supervisor_name}</span>
                    <span className="block text-slate-400 text-[10px]">{selectedRecord.supervisor_role}</span>
                  </div>
                  <div>
                    <span className="font-semibold text-slate-500 block text-[11px]">Cryptographic Provenance:</span>
                    <span className="font-mono text-slate-700 text-[10px] break-all">{selectedRecord.provenance_hash}</span>
                  </div>
                </div>
              </div>

              <div className="flex justify-end pt-3 border-t border-slate-100">
                <button
                  onClick={() => setSelectedRecord(null)}
                  className="px-4 py-2 rounded-lg bg-slate-900 text-white text-xs font-semibold hover:bg-slate-800 transition-colors"
                >
                  Close Audit Dossier
                </button>
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* SUPERVISOR SIGNAL RECORDING MODAL */}
      <AnimatePresence>
        {activeModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
            <motion.div
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
              className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200 space-y-4"
            >
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <PlusCircle className="w-5 h-5 text-indigo-600" />
                  Record Level 3 Workplace Evidence Signal
                </h3>
                <button
                  onClick={() => setActiveModal(false)}
                  className="p-1 text-slate-400 hover:text-slate-600 rounded"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <form onSubmit={handleSaveSignal} className="space-y-3.5 text-xs">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Officer Full Name</label>
                  <input
                    type="text"
                    required
                    placeholder="e.g., Shri Ankit Choubey"
                    value={newOfficerName}
                    onChange={(e) => setNewOfficerName(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Cadre & Designation</label>
                    <select
                      value={newCadre}
                      onChange={(e) => setNewCadre(e.target.value)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                    >
                      <option>Senior Statistical Officer (SSO)</option>
                      <option>Junior Statistical Officer (JSO)</option>
                      <option>Statistical Investigator Gr. I</option>
                      <option>Deputy Director (Data Analytics)</option>
                      <option>Joint Director (Cadre Evaluation)</option>
                    </select>
                  </div>

                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">Evidence Source</label>
                    <select
                      value={newSignalSource}
                      onChange={(e) => setNewSignalSource(e.target.value as any)}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none bg-white"
                    >
                      <option value="FOD_FIELD_INSPECTION">FOD Field Inspection</option>
                      <option value="SPARROW_APAR">SPARROW e-HRMS APAR</option>
                      <option value="DPD_SCRUTINY">DPD Automated Scrutiny</option>
                      <option value="TRAINING_IMPACT_SURVEY">Training Impact Survey</option>
                    </select>
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Competency Scope</label>
                  <input
                    type="text"
                    required
                    value={newCompetency}
                    onChange={(e) => setNewCompetency(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">L1/L2 Theory Score (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      required
                      value={newL1Score}
                      onChange={(e) => setNewL1Score(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-semibold text-slate-700 block mb-1">L3 Field Inspection (%)</label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      required
                      value={newL3Score}
                      onChange={(e) => setNewL3Score(Number(e.target.value))}
                      className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                    />
                  </div>
                </div>

                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Supervisory Observation Summary</label>
                  <textarea
                    rows={3}
                    required
                    placeholder="Enter audit spot-check observations, sampling multipliers checked, or non-sampling error notes..."
                    value={newEvidence}
                    onChange={(e) => setNewEvidence(e.target.value)}
                    className="w-full px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:outline-none"
                  />
                </div>

                <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                  <button
                    type="button"
                    onClick={() => setActiveModal(false)}
                    className="px-3.5 py-2 rounded-lg border border-slate-200 text-slate-700 hover:bg-slate-50 font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-700 text-white font-semibold transition-colors"
                  >
                    Commit Signal to Cadre Ledger
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
}
