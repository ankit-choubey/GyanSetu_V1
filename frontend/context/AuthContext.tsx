"use client";

import React, { createContext, useContext, useEffect, useState, useMemo } from "react";

import { client } from "@/lib/api/client";

export interface UserProfile {
  id?: number;
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
  login: (email: string, password: string) => Promise<UserProfile>;
  register: (payload: {
    email: string;
    full_name: string;
    password: string;
    role?: "learner" | "admin";
  }) => Promise<UserProfile>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  isAuthenticated: false,
  user: null,
  isLoading: true,
  login: async () => {
    throw new Error("AuthProvider not mounted");
  },
  register: async () => {
    throw new Error("AuthProvider not mounted");
  },
  logout: () => {},
});

const STORAGE_KEY = "gyansetu_auth_session";
const TOKEN_KEY = "gyansetu_auth_token";

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Restore and verify session on mount
  useEffect(() => {
    async function restoreSession() {
      try {
        const storedToken = localStorage.getItem(TOKEN_KEY);
        const stored = localStorage.getItem(STORAGE_KEY);
        if (stored && storedToken) {
          const parsed = JSON.parse(stored);
          if (parsed && parsed.email) {
            try {
              const me = await client.get<any>("/api/auth/me", { token: storedToken });
              const verifiedProfile: UserProfile = {
                id: me.id,
                name: me.full_name,
                email: me.email,
                role: me.role,
                designation: me.designation,
                department: me.department,
              };
              setUser(verifiedProfile);
              localStorage.setItem(STORAGE_KEY, JSON.stringify(verifiedProfile));
              setIsLoading(false);
              return;
            } catch (err) {
              console.warn("Stored session expired or invalid:", err);
              localStorage.removeItem(STORAGE_KEY);
              localStorage.removeItem(TOKEN_KEY);
              setUser(null);
            }
          }
        }
      } catch {
        // Storage unavailable
      } finally {
        setIsLoading(false);
      }
    }
    restoreSession();
  }, []);

  const login = async (email: string, password: string): Promise<UserProfile> => {
    const res = await client.post<{
      access_token: string;
      token_type: string;
      user: {
        id: number;
        email: string;
        full_name: string;
        role: "learner" | "admin";
        designation: string;
        department: string;
      };
    }>("/api/auth/login", { email, password });

    const u = res.user;
    const profile: UserProfile = {
      id: u.id,
      name: u.full_name,
      email: u.email,
      role: u.role,
      designation: u.designation,
      department: u.department,
    };

    setUser(profile);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
      localStorage.setItem(TOKEN_KEY, res.access_token);
    } catch {
      // Storage unavailable
    }
    return profile;
  };

  const register = async (payload: {
    email: string;
    full_name: string;
    password: string;
    role?: "learner" | "admin";
  }): Promise<UserProfile> => {
    const res = await client.post<{
      access_token: string;
      token_type: string;
      user: {
        id: number;
        email: string;
        full_name: string;
        role: "learner" | "admin";
        designation: string;
        department: string;
      };
    }>("/api/auth/register", payload);

    const u = res.user;
    const profile: UserProfile = {
      id: u.id,
      name: u.full_name,
      email: u.email,
      role: u.role,
      designation: u.designation,
      department: u.department,
    };

    setUser(profile);
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(profile));
      localStorage.setItem(TOKEN_KEY, res.access_token);
    } catch {
      // Storage unavailable
    }
    return profile;
  };

  const logout = () => {
    setUser(null);
    try {
      localStorage.removeItem(STORAGE_KEY);
      localStorage.removeItem(TOKEN_KEY);
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
      register,
      logout,
    }),
    [user, isLoading]
  );

  return <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  return useContext(AuthContext);
}
