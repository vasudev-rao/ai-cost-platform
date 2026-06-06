"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";
import type { DashboardMetrics } from "@/types";

export function useDashboard() {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery<DashboardMetrics>({
    queryKey: ["dashboard", orgId],
    queryFn: async () => {
      const res = await api.costs.dashboard(orgId!);
      return res.data;
    },
    enabled: !!orgId,
    refetchInterval: 60_000,
    staleTime: 30_000,
  });
}

export function useCostTrend(days = 30) {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery({
    queryKey: ["cost-trend", orgId, days],
    queryFn: async () => {
      const res = await api.costs.trend(orgId!, days);
      return res.data;
    },
    enabled: !!orgId,
    staleTime: 60_000,
  });
}

export function useCostByModel(days = 30) {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery({
    queryKey: ["cost-by-model", orgId, days],
    queryFn: async () => {
      const res = await api.costs.byModel(orgId!, days);
      return res.data;
    },
    enabled: !!orgId,
    staleTime: 60_000,
  });
}
