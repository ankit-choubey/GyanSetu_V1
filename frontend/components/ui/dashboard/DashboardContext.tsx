"use client";

import React, { createContext, useContext, useMemo, useState } from "react";

interface DashboardContextType {
  persona: "jso" | "new";
  setPersona: (persona: "jso" | "new") => void;
  isDiagnosticModalOpen: boolean;
  setIsDiagnosticModalOpen: (open: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType>({
  persona: "jso",
  setPersona: () => {},
  isDiagnosticModalOpen: false,
  setIsDiagnosticModalOpen: () => {},
});

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [persona, setPersona] = useState<"jso" | "new">("jso");
  const [isDiagnosticModalOpen, setIsDiagnosticModalOpen] = useState(false);

  const contextValue = useMemo(
    () => ({
      persona,
      setPersona,
      isDiagnosticModalOpen,
      setIsDiagnosticModalOpen,
    }),
    [persona, isDiagnosticModalOpen]
  );

  return (
    <DashboardContext.Provider value={contextValue}>
      {children}
    </DashboardContext.Provider>
  );
}

export function useDashboard() {
  return useContext(DashboardContext);
}
