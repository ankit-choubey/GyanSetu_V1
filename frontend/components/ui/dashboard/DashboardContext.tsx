"use client";

import React, { createContext, useContext, useMemo, useState } from "react";

interface DashboardContextType {
  persona: "jso" | "new" | "admin";
  setPersona: (persona: "jso" | "new" | "admin") => void;
  userName: string;
  roleName: string;
  setUserInfo: (name: string, role: string) => void;
  isDiagnosticModalOpen: boolean;
  setIsDiagnosticModalOpen: (open: boolean) => void;
}

const DashboardContext = createContext<DashboardContextType>({
  persona: "jso",
  setPersona: () => {},
  userName: "Ramesh Kumar",
  roleName: "Statistical Officer",
  setUserInfo: () => {},
  isDiagnosticModalOpen: false,
  setIsDiagnosticModalOpen: () => {},
});

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [persona, setPersonaState] = useState<"jso" | "new" | "admin">("jso");
  const [userName, setUserName] = useState<string>("Ramesh Kumar");
  const [roleName, setRoleName] = useState<string>("Statistical Officer");
  const [isDiagnosticModalOpen, setIsDiagnosticModalOpen] = useState(false);

  const setPersona = (newPersona: "jso" | "new" | "admin") => {
    setPersonaState(newPersona);
    if (newPersona === "new") {
      setUserName("Priya Verma");
      setRoleName("Junior Statistical Officer");
    } else if (newPersona === "admin") {
      setUserName("System Admin");
      setRoleName("Platform Administrator");
    } else {
      setUserName("Ramesh Kumar");
      setRoleName("Statistical Officer");
    }
  };

  const setUserInfo = (name: string, role: string) => {
    setUserName(name);
    setRoleName(role);
  };

  const contextValue = useMemo(
    () => ({
      persona,
      setPersona,
      userName,
      roleName,
      setUserInfo,
      isDiagnosticModalOpen,
      setIsDiagnosticModalOpen,
    }),
    [persona, userName, roleName, isDiagnosticModalOpen]
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
