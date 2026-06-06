"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export function useAlerts(unresolvedOnly = true) {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery({
    queryKey: ["alerts", orgId, unresolvedOnly],
    queryFn: async () => {
      const res = await api.alerts.list(orgId!, unresolvedOnly);
      return res.data;
    },
    enabled: !!orgId,
    refetchInterval: 30_000,
  });
}

export function useResolveAlert() {
  const orgId = useAuthStore((s) => s.orgId);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (alertId: string) => api.alerts.resolve(alertId),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["alerts", orgId] }),
  });
}
