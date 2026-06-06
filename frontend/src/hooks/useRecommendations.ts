"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuthStore } from "@/store/authStore";

export function useRecommendations() {
  const orgId = useAuthStore((s) => s.orgId);
  return useQuery({
    queryKey: ["recommendations", orgId],
    queryFn: async () => {
      const res = await api.recommendations.list(orgId!);
      return res.data;
    },
    enabled: !!orgId,
    staleTime: 120_000,
  });
}

export function useAnalyzeRecommendations() {
  const orgId = useAuthStore((s) => s.orgId);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => api.recommendations.analyze(orgId!),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["recommendations", orgId] }),
  });
}
