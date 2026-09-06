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

export const client = {
  async get<T>(path: string): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
      headers: {
        "Content-Type": "application/json",
      },
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
      headers: {
        "Content-Type": "application/json",
      },
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
};
