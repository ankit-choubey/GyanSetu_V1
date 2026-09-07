"use client";

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";

export interface UserProfile {
  name: string;
  email: string;
  role: "learner" | "admin";
  designation: string;
  department: string;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: UserProfile | null;
  isLoading: boolean;
  login: (role: "learner" | "admin", email: string, name?: string) => UserProfile;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  isLoading: true,
  login: () => ({
    name: "Ramesh Kumar",
    email: "officer.sharma@mospi.gov.in",
    role: "learner",
    designation: "Statistical Officer",
    department: "National Accounts Division (MoSPI)",
  }),
  logout: () => {},
});

const STORAGE_KEY = "gyansetu_auth_session";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore session on mount
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored);
        if (parsed && parsed.email) {
          setUser(parsed);
        }
      }
    } catch {
      // Ignore localStorage errors
    } finally {
      setIsLoading(false);
    }
  }, []);

  const login = (role: "learner" | "admin", email: string, customName?: string): UserProfile => {
    const newUser: UserProfile = {
      name:
        customName ||
        (role === "admin"
          ? "System Administrator"
          : email.split("@")[0].replace(".", " ").replace(/\b\w/g, (c) => c.toUpperCase()) || "Ramesh Kumar"),
      email,
      role,
      designation: role === "admin" ? "Workforce Platform Administrator" : "Statistical Officer",
      department: role === "admin" ? "DIID & Training Planning (MoSPI)" : "National Accounts Division (NAD)",
    };

    setUser(newUser);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(newUser));
    } catch {
      // Storage unavailable
    }
    return newUser;
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Storage unavailable
    }
  };

  const contextValue = useMemo(
    () => ({
      isAuthenticated: !!user,
      user,
      isLoading,
      login,
      logout,
    }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
