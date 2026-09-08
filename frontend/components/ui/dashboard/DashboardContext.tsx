"use client";

import React, { createContext, useContext, useMemo, useState } from "react";

export const DEMO_LEARNER_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzg4OTA1MjU0fQ.3vttz6_9enGhy2SXwMtPgzfpBFZL414SDNcrXO8FpI4";
export const NEW_LEARNER_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIzIiwiZXhwIjoxNzg4OTA2MDM5fQ.I7K0poC0VsqwR-UAOOAD0XkO-7W9OTeMqR5JFMXa9Ls";
export const DEMO_ADMIN_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIyIiwiZXhwIjoxNzg4OTA1Mjg0fQ.hw-gi8MeOTWNqawFp3gqRCe6C8C6lPm0g_sWl1EpxrI";

interface DashboardContextType {
  persona: "jso" | "new" | "admin";
  setPersona: (persona: "jso" | "new" | "admin") => void;
  userName: string;
  roleName: string;
  setUserInfo: (name: string, role: string) => void;
  isDiagnosticModalOpen: boolean;
  setIsDiagnosticModalOpen: (open: boolean) => void;
  refreshCount: number;
  refreshDashboard: () => void;
}

const DashboardContext = createContext<DashboardContextType>({
  persona: "jso",
  setPersona: () => {},
  userName: "Sample Learner",
  roleName: "Statistical Officer",
  setUserInfo: () => {},
  isDiagnosticModalOpen: false,
  setIsDiagnosticModalOpen: () => {},
  refreshCount: 0,
  refreshDashboard: () => {},
});

export function DashboardProvider({ children }: { children: React.ReactNode }) {
  const [persona, setPersonaState] = useState<"jso" | "new" | "admin">("jso");
  const [userName, setUserName] = useState<string>("Sample Learner");
  const [roleName, setRoleName] = useState<string>("Statistical Officer");
  const [isDiagnosticModalOpen, setIsDiagnosticModalOpen] = useState(false);
  const [refreshCount, setRefreshCount] = useState(0);

  const refreshDashboard = () => {
    setRefreshCount((c) => c + 1);
  };

  const setPersona = (newPersona: "jso" | "new" | "admin") => {
    setPersonaState(newPersona);
    if (typeof window !== "undefined") {
      try {
        const hasRealUser = !!localStorage.getItem("gyansetu_user");
        if (!hasRealUser) {
          if (newPersona === "new") {
            localStorage.setItem("gyansetu_auth_token", NEW_LEARNER_TOKEN);
          } else if (newPersona === "admin") {
            localStorage.setItem("gyansetu_auth_token", DEMO_ADMIN_TOKEN);
          } else {
            localStorage.setItem("gyansetu_auth_token", DEMO_LEARNER_TOKEN);
          }
        }
      } catch {
        // Storage unavailable
      }
    }
    if (newPersona === "new") {
      setUserName("Sandbox Analyst (New)");
      setRoleName("Statistical Officer");
    } else if (newPersona === "admin") {
      setUserName("Sandbox Administrator");
      setRoleName("Platform Administrator");
    } else {
      setUserName("Sample Learner");
      setRoleName("Statistical Officer");
    }
    setRefreshCount((c) => c + 1);
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
      refreshCount,
      refreshDashboard,
    }),
    [persona, userName, roleName, isDiagnosticModalOpen, refreshCount]
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
