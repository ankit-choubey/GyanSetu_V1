/**
 * GyanSetu API Client Wrapper
 */

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(message: string, status: number, data?: any) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.data = data;
  }
}

function getHeaders(): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (typeof window !== "undefined") {
    const token =
      localStorage.getItem("gyansetu_auth_token") ||
      sessionStorage.getItem("gyansetu_auth_token");
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }
  return headers;
}

export const client = {
  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: getHeaders(),
      next: { revalidate: 0 },
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => null);
      throw new ApiError(
        `API Request Failed: ${res.status} ${res.statusText}`,
        res.status,
        errorData
      );
    }

    return res.json();
  },

  async post<T>(path: string, body: any): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: getHeaders(),
      body: JSON.stringify(body),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => null);
      throw new ApiError(
        `API Request Failed: ${res.status} ${res.statusText}`,
        res.status,
        errorData
      );
    }

    return res.json();
  },

  async postFormData<T>(path: string, formData: FormData): Promise<T> {
    const headers: Record<string, string> = {};
    if (typeof window !== "undefined") {
      const token =
        localStorage.getItem("gyansetu_auth_token") ||
        sessionStorage.getItem("gyansetu_auth_token");
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
      }
    }

    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers,
      body: formData,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => null);
      throw new ApiError(
        `API Request Failed: ${res.status} ${res.statusText}`,
        res.status,
        errorData
      );
    }

    return res.json();
  },
};
