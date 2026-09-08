"use client";

import React, { useState, useEffect, useMemo } from "react";
import Link from "next/link";
import {
  FileSpreadsheet,
  Download,
  Search,
  CheckCircle2,
  AlertCircle,
  Clock,
  ShieldCheck,
  TrendingUp,
  User,
  Building,
  GraduationCap,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Award,
  Bot,
} from "lucide-react";
import { TestLedgerItem } from "@/lib/api/types";
import { fetchLiveLedger } from "@/lib/api/ledger";
import { generateTestReportDocx } from "@/lib/docx/reportGenerator";
import { cn } from "@/lib/cn";

export default function ReportLedgerPage() {
  const [items, setItems] = useState<TestLedgerItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [tierFilter, setTierFilter] = useState<string>("all");
  const [statusFilter, setStatusFilter] = useState<string>("all");
  const [downloadingId, setDownloadingId] = useState<string | null>(null);

  const loadLedger = async () => {
    setIsLoading(true);
    try {
      const data = await fetchLiveLedger();
      setItems(data);
    } catch (e) {
      console.warn("Could not load ledger:", e);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadLedger();

    const handleLedgerUpdate = (e: Event) => {
      const customEvent = e as CustomEvent<TestLedgerItem>;
      if (customEvent.detail) {
        setItems((prev) => [customEvent.detail, ...prev]);
      } else {
        loadLedger();
      }
    };

    window.addEventListener("gyansetu:ledger_updated", handleLedgerUpdate);
    return () => {
      window.removeEventListener("gyansetu:ledger_updated", handleLedgerUpdate);
    };
  }, []);

  const handleDownloadDocx = async (item: TestLedgerItem, e: React.MouseEvent) => {
    e.stopPropagation();
    setDownloadingId(item.report_id);
    try {
      await generateTestReportDocx(item);
    } catch (err) {
      console.error("Failed downloading DOCX:", err);
      alert("Failed to generate DOCX report. Please check console.");
    } finally {
      setDownloadingId(null);
    }
  };

  const filteredItems = useMemo(() => {
    return items.filter((item) => {
      const matchesSearch =
        searchQuery === "" ||
        item.report_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.full_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.competency_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.department.toLowerCase().includes(searchQuery.toLowerCase()) ||
        item.role_name.toLowerCase().includes(searchQuery.toLowerCase());

      const matchesTier =
        tierFilter === "all" ||
        item.tier.toLowerCase().includes(tierFilter.toLowerCase());

      const matchesStatus =
        statusFilter === "all" ||
        (statusFilter === "passed" && item.result_status === "PASSED") ||
        (statusFilter === "failed" && item.result_status !== "PASSED");

      return matchesSearch && matchesTier && matchesStatus;
    });
  }, [items, searchQuery, tierFilter, statusFilter]);

  const summaryStats = useMemo(() => {
    const total = items.length;
    const passed = items.filter((i) => i.result_status === "PASSED").length;
    const avgScore = total > 0 ? Math.round(items.reduce((s, i) => s + i.score, 0) / total) : 0;
    const avgMastery =
      total > 0
        ? (items.reduce((s, i) => s + (i.mastery ?? 0.8), 0) / total * 100).toFixed(0)
        : "80";

    return { total, passed, avgScore, avgMastery };
  }, [items]);

  return (
    <div className="space-y-6 pb-12 w-full">
      {/* HEADER BANNER */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-7 shadow-xs flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
              Test Report Ledger
            </h2>
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-[11px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 uppercase tracking-wider">
              <ShieldCheck className="w-3 h-3 text-emerald-600" />
              Live MoSPI Ledger
            </span>
          </div>
          <p className="text-sm text-slate-500 font-sans">
            Chronological audit log of all completed assessments, Bayesian KPI indices, and official downloadable Word reports.
          </p>
        </div>

        <div className="flex items-center gap-2.5 shrink-0 flex-wrap">
          {items.length > 0 && (
            <Link
              href={`/dashboard/ledger/${items[0].numeric_id}`}
              className="inline-flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-xs font-semibold text-indigo-700 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition shadow-2xs"
              title="Open latest report with OmniDimension AI Coach and DOCX export"
            >
              <Sparkles className="w-3.5 h-3.5 text-indigo-600" />
              <span>Latest Report & AI Coach</span>
            </Link>
          )}
          <button
            onClick={loadLedger}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 transition"
            title="Refresh Ledger"
          >
            <RefreshCw className={cn("w-3.5 h-3.5", isLoading && "animate-spin text-blue-600")} />
            <span>Sync Ledger</span>
          </button>
          <Link
            href="/dashboard/assessments"
            className="inline-flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-700 text-white transition shadow-xs"
          >
            <GraduationCap className="w-4 h-4" />
            <span>Take Assessment</span>
          </Link>
        </div>
      </div>

      {/* STAT CARDS */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Total Reports</span>
            <FileSpreadsheet className="w-4 h-4 text-blue-600" />
          </div>
          <div className="font-heading text-3xl font-bold text-slate-900">
            {summaryStats.total}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Recorded in official ledger</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Passed Assessments</span>
            <Award className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="font-heading text-3xl font-bold text-emerald-600">
            {summaryStats.passed}
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Score ≥ 70% qualification</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Average Test Score</span>
            <TrendingUp className="w-4 h-4 text-indigo-600" />
          </div>
          <div className="font-heading text-3xl font-bold text-slate-900">
            {summaryStats.avgScore}%
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Across all evaluated attempts</p>
        </div>

        <div className="bg-white p-5 rounded-xl border border-slate-200 shadow-xs">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium uppercase tracking-wider">Avg Competency Mastery</span>
            <Sparkles className="w-4 h-4 text-amber-500" />
          </div>
          <div className="font-heading text-3xl font-bold text-slate-900">
            {summaryStats.avgMastery}%
          </div>
          <p className="text-[11px] text-slate-500 mt-1">Bayesian IRT calibrated index</p>
        </div>
      </div>

      {/* SEARCH & FILTERS */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-xs flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative w-full md:w-80">
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search report #, officer, competency, department..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-xs sm:text-sm text-slate-900 placeholder:text-slate-400 focus:bg-white focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-500 transition"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto overflow-x-auto">
          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {[
              { id: "all", label: "All Tiers" },
              { id: "tier 1", label: "Tier 1" },
              { id: "tier 2", label: "Tier 2" },
              { id: "tier 3", label: "Tier 3" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setTierFilter(tab.id)}
                className={cn(
                  "px-2.5 py-1 text-xs font-medium rounded-md transition",
                  tierFilter === tab.id
                    ? "bg-white text-slate-900 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg">
            {[
              { id: "all", label: "All Status" },
              { id: "passed", label: "Passed" },
              { id: "failed", label: "Retry" },
            ].map((tab) => (
              <button
                key={tab.id}
                onClick={() => setStatusFilter(tab.id)}
                className={cn(
                  "px-2.5 py-1 text-xs font-medium rounded-md transition",
                  statusFilter === tab.id
                    ? "bg-white text-slate-900 font-semibold shadow-xs"
                    : "text-slate-600 hover:text-slate-900"
                )}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* REPORT LEDGER TABLE */}
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse text-xs sm:text-sm font-sans">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-600 font-semibold uppercase text-[11px] tracking-wider">
                <th className="py-3.5 px-4">Report ID</th>
                <th className="py-3.5 px-4">Officer Profile</th>
                <th className="py-3.5 px-4">Competency Module</th>
                <th className="py-3.5 px-4">Tier / Level</th>
                <th className="py-3.5 px-4 text-center">Score</th>
                <th className="py-3.5 px-4">KPI Mastery</th>
                <th className="py-3.5 px-4">Status</th>
                <th className="py-3.5 px-4 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {filteredItems.length === 0 ? (
                <tr>
                  <td colSpan={8} className="py-12 text-center text-slate-500">
                    <FileSpreadsheet className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                    <p className="font-medium text-slate-700">No test reports found</p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      Complete an assessment or ingestion task to generate real-time reports.
                    </p>
                  </td>
                </tr>
              ) : (
                filteredItems.map((item) => (
                  <tr
                    key={item.report_id}
                    className="hover:bg-slate-50/80 transition-colors group cursor-pointer"
                    onClick={() => {
                      window.location.href = `/dashboard/ledger/${item.numeric_id}`;
                    }}
                  >
                    <td className="py-4 px-4 whitespace-nowrap">
                      <div className="font-heading font-bold text-slate-900">
                        {item.report_id}
                      </div>
                      <div className="flex items-center gap-1 text-[11px] text-slate-400 mt-0.5">
                        <Clock className="w-3 h-3" />
                        <span>{item.timestamp}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      <div className="font-semibold text-slate-800 flex items-center gap-1.5">
                        <User className="w-3.5 h-3.5 text-slate-400" />
                        {item.full_name}
                      </div>
                      <div className="text-[11px] text-slate-500 flex items-center gap-1 mt-0.5">
                        <Building className="w-3 h-3 text-slate-400" />
                        <span>{item.role_name} • {item.department}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4">
                      <div className="font-medium text-slate-800 line-clamp-1 max-w-xs">
                        {item.competency_name}
                      </div>
                      <div className="text-[11px] text-slate-400 mt-0.5">
                        Reliability: <span className="text-slate-600 font-mono">{item.reliability_status}</span>
                      </div>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      <span className="inline-flex items-center px-2.5 py-1 rounded-md text-xs font-semibold bg-slate-100 text-slate-700 border border-slate-200">
                        {item.tier}
                      </span>
                    </td>

                    <td className="py-4 px-4 text-center whitespace-nowrap">
                      <div className={cn(
                        "font-heading font-bold text-base",
                        item.score >= 70 ? "text-emerald-600" : "text-rose-600"
                      )}>
                        {item.score}%
                      </div>
                      <div className="text-[11px] text-slate-400 font-mono">
                        {item.correct_count} / {item.total_questions}
                      </div>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      <div className="flex items-center gap-1.5">
                        <span className="font-medium text-slate-800">
                          {item.mastery !== null ? `${(item.mastery * 100).toFixed(0)}%` : "N/A"}
                        </span>
                        <span className="text-[11px] text-slate-400 font-sans">
                          ({(item.confidence * 100).toFixed(0)}% cert)
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-400">
                        Coverage: {(item.coverage * 100).toFixed(0)}%
                      </div>
                    </td>

                    <td className="py-4 px-4 whitespace-nowrap">
                      {item.result_status === "PASSED" ? (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                          Passed
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                          <AlertCircle className="w-3.5 h-3.5 text-rose-600" />
                          Retry
                        </span>
                      )}
                    </td>

                    <td className="py-4 px-4 text-right whitespace-nowrap">
                      <div className="flex items-center justify-end gap-2" onClick={(e) => e.stopPropagation()}>
                        <Link
                          href={`/dashboard/ledger/${item.numeric_id}`}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-indigo-700 hover:text-indigo-900 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 transition shadow-2xs"
                          title="View Full Report, OmniDimension Chatbot & DOCX"
                        >
                          <Bot className="w-3.5 h-3.5 text-indigo-600" />
                          <span>Inspect & Chat</span>
                          <ArrowRight className="w-3 h-3 text-indigo-400" />
                        </Link>
                        <button
                          type="button"
                          onClick={(e) => handleDownloadDocx(item, e)}
                          disabled={downloadingId === item.report_id}
                          className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-white bg-blue-600 hover:bg-blue-700 transition shadow-xs disabled:opacity-50"
                          title="Download Official MoSPI DOCX Report"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>{downloadingId === item.report_id ? "Exporting..." : "DOCX"}</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
