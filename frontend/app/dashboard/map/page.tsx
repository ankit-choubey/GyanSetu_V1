"use client";

import React, { useState, useMemo, useEffect } from "react";
import { useDashboard } from "@/components/ui/dashboard/DashboardContext";
import {
  getCompetencyState,
  getCompetencyStateSync,
  deriveKPISummary,
} from "@/lib/api/competency";
import { DashboardResponse, BackendCompetency } from "@/lib/api/types";
import { MapStatCards } from "@/components/ui/map/MapStatCards";
import { CompetencyTree } from "@/components/ui/map/CompetencyTree";
import { NodeDetailPanel } from "@/components/ui/map/NodeDetailPanel";
import { CoverageBarChart } from "@/components/ui/map/CoverageBarChart";
import { DashboardSkeleton } from "@/components/ui/dashboard/states/CardSkeleton";
import { ErrorState } from "@/components/ui/dashboard/states/ErrorState";

export default function CompetencyMapPage() {
  const { persona } = useDashboard();
  const [data, setData] = useState<DashboardResponse>(() =>
    getCompetencyStateSync(persona)
  );
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedCompetency, setSelectedCompetency] = useState<BackendCompetency | null>(
    () => (data.competencies && data.competencies.length > 0 ? data.competencies[0] : null)
  );

  useEffect(() => {
    let isSubscribed = true;
    const isMock = process.env.NEXT_PUBLIC_USE_MOCK !== "false";

    if (isMock) {
      const state = getCompetencyStateSync(persona);
      setData(state);
      if (state.competencies.length > 0) {
        setSelectedCompetency(state.competencies[0]);
      }
      setIsLoading(false);
      return;
    }

    setIsLoading(true);
    setError(null);

    getCompetencyState(persona)
      .then((res) => {
        if (isSubscribed) {
          setData(res);
          if (res.competencies.length > 0) {
            setSelectedCompetency(res.competencies[0]);
          }
          setIsLoading(false);
        }
      })
      .catch((err) => {
        if (isSubscribed) {
          setError(err.message || "Failed to load competency map.");
          setIsLoading(false);
        }
      });

    return () => {
      isSubscribed = false;
    };
  }, [persona]);

  const kpiSummary = useMemo(() => deriveKPISummary(data), [data]);

  if (isLoading) {
    return <DashboardSkeleton />;
  }

  if (error || !data) {
    return (
      <ErrorState
        title="Could not load competency map"
        message={error || "Unexpected error"}
        onRetry={() => {
          setIsLoading(true);
          getCompetencyState(persona)
            .then(setData)
            .catch((e) => setError(e.message))
            .finally(() => setIsLoading(false));
        }}
      />
    );
  }

  return (
    <div className="space-y-8 pb-12">
      {/* Header */}
      <div>
        <h2 className="font-heading text-2xl sm:text-3xl text-slate-900 tracking-normal">
          Competency Map
        </h2>
        <p className="text-sm text-slate-500 font-sans mt-1">
          Role curriculum structure, subskill hierarchy, and tested syllabus coverage
        </p>
      </div>

      {/* ROW 1: STAT CARDS */}
      <MapStatCards
        totalCount={kpiSummary.total_count}
        assessedCount={kpiSummary.assessed_count}
        avgCoverage={kpiSummary.coverage_avg}
      />

      {/* ROW 2: TREE HIERARCHY (COL 7) + SELECTED DETAIL (COL 5) */}
      <section className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-stretch">
        <div className="lg:col-span-7 flex flex-col">
          <CompetencyTree
            roleName={data.role_name}
            competencies={data.competencies}
            selectedId={selectedCompetency?.competency_id ?? null}
            onSelect={setSelectedCompetency}
            className="h-full"
          />
        </div>
        <div className="lg:col-span-5 flex flex-col">
          <NodeDetailPanel
            competency={selectedCompetency}
            className="h-full"
          />
        </div>
      </section>

      {/* ROW 3: COVERAGE BAR CHART */}
      <section aria-labelledby="coverage-chart-heading">
        <h2 id="coverage-chart-heading" className="sr-only">
          Coverage Bar Chart
        </h2>
        <CoverageBarChart competencies={data.competencies} />
      </section>
    </div>
  );
}
