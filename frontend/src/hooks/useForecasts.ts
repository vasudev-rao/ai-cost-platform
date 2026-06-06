"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export function useLatestForecasts() {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery({
    queryKey: ["forecasts-latest", orgId],
    queryFn: async () => {
      const res = await api.forecasts.latest(orgId!);
      return res.data;
    },
    enabled: !!orgId,
    staleTime: 300_000,
  });
}

export function useGenerateForecast() {
  const orgId = useAuthStore((s) => s.orgId);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (horizon: string) => api.forecasts.generate(orgId!, horizon),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["forecasts-latest", orgId] }),
  });
}
