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

const DEFAULT_DEMO_TOKEN =
  "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxIiwiZXhwIjoxNzkxNDEzNjM2fQ.TaeM6oIGwPkeJWH2o4WjMnQnCXKyYKJ_lfw9P_7jYDE";

function getHeaders(customHeaders?: Record<string, string>, customToken?: string): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(customHeaders || {}),
  };
  let token = customToken || DEFAULT_DEMO_TOKEN;
  if (!customToken && typeof window !== "undefined") {
    const storedToken =
      localStorage.getItem("gyansetu_auth_token") ||
      sessionStorage.getItem("gyansetu_auth_token");
    if (storedToken) {
      token = storedToken;
    }
  }
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

export const client = {
  async get<T>(path: string, options?: { headers?: Record<string, string>; token?: string }): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: getHeaders(options?.headers, options?.token),
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

  async post<T>(path: string, body: any, options?: { headers?: Record<string, string>; token?: string }): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      method: "POST",
      headers: getHeaders(options?.headers, options?.token),
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
