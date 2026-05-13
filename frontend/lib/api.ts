"use client";

import axios, { AxiosError, type AxiosInstance } from "axios";

import { useAuthStore } from "@/lib/store";

/**
 * Single Axios instance for the whole app.
 *
 * - All requests are sent to `/api/v1/*` so Next.js dev-time rewrites or a
 *   production nginx route can forward them to the FastAPI backend.
 * - Tokens are injected from the Zustand auth store on every call so we never
 *   have to remember to attach them by hand.
 * - 401 responses trigger an automatic refresh-token retry once per request.
 */
export const api: AxiosInstance = axios.create({
  baseURL: "/api/v1",
  timeout: 30000,
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().accessToken;
  if (token) {
    config.headers = config.headers ?? {};
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

let refreshInFlight: Promise<string | null> | null = null;

api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (typeof error.config & { _retried?: boolean })
      | undefined;
    if (!original || error.response?.status !== 401 || original._retried) {
      return Promise.reject(error);
    }
    original._retried = true;

    refreshInFlight ??= refreshAccessToken();
    const newToken = await refreshInFlight;
    refreshInFlight = null;

    if (!newToken) {
      useAuthStore.getState().logout();
      return Promise.reject(error);
    }
    original.headers = original.headers ?? {};
    original.headers.Authorization = `Bearer ${newToken}`;
    return api(original);
  },
);

async function refreshAccessToken(): Promise<string | null> {
  const refresh = useAuthStore.getState().refreshToken;
  if (!refresh) return null;
  try {
    const { data } = await axios.post("/api/v1/auth/refresh", {
      refresh_token: refresh,
    });
    useAuthStore
      .getState()
      .setTokens(data.access_token, data.refresh_token, data.user);
    return data.access_token as string;
  } catch {
    return null;
  }
}

/**
 * Typed wrapper functions — keep call sites concise and ensure that every
 * frontend page can be code-searched for "endpoint usage" easily.
 */
export const endpoints = {
  // --- auth ---------------------------------------------------------
  login: (email: string, password: string) =>
    api.post("/auth/login", { email, password }).then((r) => r.data),
  me: () => api.get("/auth/me").then((r) => r.data),

  // --- chat ---------------------------------------------------------
  sendMessage: (message: string, sessionId?: string | null) =>
    api
      .post("/chat/message", { message, session_id: sessionId, channel: "web" })
      .then((r) => r.data),
  listConversations: () => api.get("/chat/conversations").then((r) => r.data),

  // --- documents ----------------------------------------------------
  listDocuments: () => api.get("/documents").then((r) => r.data),
  uploadDocument: (file: File, title?: string, category = "genel") => {
    const form = new FormData();
    form.append("file", file);
    if (title) form.append("title", title);
    form.append("category", category);
    return api
      .post("/documents/upload", form, {
        headers: { "Content-Type": "multipart/form-data" },
      })
      .then((r) => r.data);
  },
  deleteDocument: (id: number) => api.delete(`/documents/${id}`),

  // --- inventory ----------------------------------------------------
  listProducts: (onlyLowStock = false) =>
    api
      .get("/inventory", { params: { only_low_stock: onlyLowStock } })
      .then((r) => r.data),
  adjustInventory: (
    id: number,
    quantity: number,
    movement_type: "inbound" | "outbound" | "adjustment",
    note?: string,
  ) =>
    api
      .post(`/inventory/${id}/adjust`, { quantity, movement_type, note })
      .then((r) => r.data),
  forecastInventory: (id: number) =>
    api.post(`/inventory/${id}/forecast`).then((r) => r.data),

  // --- shipments ----------------------------------------------------
  listShipments: () => api.get("/shipments").then((r) => r.data),
  checkShipment: (id: number) =>
    api.post(`/shipments/${id}/check-status`).then((r) => r.data),

  // --- tasks --------------------------------------------------------
  listTasks: () => api.get("/tasks").then((r) => r.data),
  generateTasks: () => api.post("/tasks/generate").then((r) => r.data),
  updateTask: (id: number, payload: Record<string, unknown>) =>
    api.patch(`/tasks/${id}`, payload).then((r) => r.data),

  // --- alerts -------------------------------------------------------
  listAlerts: () => api.get("/alerts").then((r) => r.data),
  markAlertRead: (id: number) =>
    api.post(`/alerts/${id}/read`).then((r) => r.data),
  resolveAlert: (id: number) =>
    api.post(`/alerts/${id}/resolve`).then((r) => r.data),

  // --- analytics ----------------------------------------------------
  salesAnalytics: (days = 14) =>
    api.get("/analytics/sales", { params: { days } }).then((r) => r.data),
  inventoryAnalytics: () => api.get("/analytics/inventory").then((r) => r.data),
  shippingAnalytics: () => api.get("/analytics/shipping").then((r) => r.data),

  // --- dashboard ----------------------------------------------------
  dailyDashboard: () => api.get("/dashboard/daily").then((r) => r.data),

  // --- customer portal ----------------------------------------------
  myOrders: () => api.get("/portal/my-orders").then((r) => r.data),
  myShipments: () => api.get("/portal/my-shipments").then((r) => r.data),
  publicTrack: (code: string) =>
    api.get(`/portal/track/${code}`).then((r) => r.data),

  // --- AI health probe (root path, bypasses /api/v1 prefix) ---------
  aiHealth: () =>
    fetch(`${process.env.NEXT_PUBLIC_API_URL ?? ""}/health/ai`).then((r) =>
      r.json(),
    ),
};

export type ApiEndpoints = typeof endpoints;
