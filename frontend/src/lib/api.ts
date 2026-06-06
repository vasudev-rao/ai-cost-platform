import axios from "axios";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
  timeout: 30000,
});

apiClient.interceptors.request.use((config) => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem("access_token");
    if (token) config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

apiClient.interceptors.response.use(
  (res) => res,
  async (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem("access_token");
      window.location.href = "/auth/login";
    }
    return Promise.reject(error);
  }
);

// ── API FUNCTIONS ────────────────────────────────────────────────
export const api = {
  auth: {
    login: (email: string, password: string) =>
      apiClient.post("/auth/login", { email, password }),
    register: (data: { email: string; full_name: string; password: string; organization_name?: string }) =>
      apiClient.post("/auth/register", data),
    refresh: (refresh_token: string) =>
      apiClient.post("/auth/refresh", { refresh_token }),
  },
  costs: {
    dashboard: (orgId: string) =>
      apiClient.get(`/costs/dashboard?org_id=${orgId}`),
    trend: (orgId: string, days = 30) =>
      apiClient.get(`/costs/trend?org_id=${orgId}&days=${days}`),
    byModel: (orgId: string, days = 30) =>
      apiClient.get(`/costs/by-model?org_id=${orgId}&days=${days}`),
    summary: (orgId: string, startDate?: string, endDate?: string) =>
      apiClient.get(`/costs/summary?org_id=${orgId}${startDate ? `&start_date=${startDate}` : ""}${endDate ? `&end_date=${endDate}` : ""}`),
    ingest: (orgId: string, projectId: string, data: unknown) =>
      apiClient.post(`/costs/ingest?org_id=${orgId}&project_id=${projectId}`, data),
  },
  forecasts: {
    generate: (orgId: string, horizon = "30d") =>
      apiClient.post(`/forecasts/generate?org_id=${orgId}`, { horizon }),
    latest: (orgId: string) =>
      apiClient.get(`/forecasts/latest?org_id=${orgId}`),
  },
  recommendations: {
    list: (orgId: string) =>
      apiClient.get(`/recommendations/?org_id=${orgId}`),
    analyze: (orgId: string) =>
      apiClient.post(`/recommendations/analyze?org_id=${orgId}`),
  },
  alerts: {
    list: (orgId: string, unresolvedOnly = true) =>
      apiClient.get(`/alerts/?org_id=${orgId}&unresolved_only=${unresolvedOnly}`),
    resolve: (alertId: string) =>
      apiClient.patch(`/alerts/${alertId}/resolve`),
  },
  teams: {
    list: (orgId: string) =>
      apiClient.get(`/teams/?org_id=${orgId}`),
  },
  projects: {
    list: (orgId: string) =>
      apiClient.get(`/projects/?org_id=${orgId}`),
  },
  reports: {
    monthly: (orgId: string, year?: number, month?: number) =>
      apiClient.get(`/reports/monthly-summary?org_id=${orgId}${year ? `&year=${year}` : ""}${month ? `&month=${month}` : ""}`),
  },
};
