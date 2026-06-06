"use client";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select } from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import { ProviderBarChart } from "@/components/charts/ProviderBarChart";
import { useCostByModel } from "@/hooks/useDashboard";
import { formatCurrency, formatNumber, getProviderColor } from "@/lib/utils";
import { BrainCircuit } from "lucide-react";

const DAYS_OPTIONS = [
  { value: "7", label: "Last 7 days" },
  { value: "30", label: "Last 30 days" },
  { value: "90", label: "Last 90 days" },
];

export default function ModelsPage() {
  const [days, setDays] = useState("30");
  const { data: models, isLoading } = useCostByModel(Number(days));

  const providerAgg = (models as any[] ?? []).reduce((acc: any, m: any) => {
    if (!acc[m.provider]) acc[m.provider] = { provider: m.provider, total_cost_usd: 0, total_requests: 0 };
    acc[m.provider].total_cost_usd += m.total_cost_usd;
    acc[m.provider].total_requests += m.total_requests;
    return acc;
  }, {});

  return (
    <AppShell title="Models">
      <div className="space-y-4">
        <Select value={days} onValueChange={setDays} options={DAYS_OPTIONS} className="w-44" />

        {/* Provider Bar Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Cost by Provider</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? <Skeleton className="h-56" /> : <ProviderBarChart data={Object.values(providerAgg)} />}
          </CardContent>
        </Card>

        {/* Model Table */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Model Breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-2">{[...Array(6)].map((_, i) => <Skeleton key={i} className="h-10" />)}</div>
            ) : (models as any[])?.length ? (
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs font-medium text-muted-foreground">
                    <th className="pb-3 pr-4">Model</th>
                    <th className="pb-3 pr-4">Provider</th>
                    <th className="pb-3 pr-4 text-right">Requests</th>
                    <th className="pb-3 pr-4 text-right">Tokens</th>
                    <th className="pb-3 text-right">Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {(models as any[]).map((m: any, i: number) => (
                    <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <BrainCircuit className="h-4 w-4 text-gray-400" />
                          <span className="font-mono text-xs font-medium">{m.model}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <span className="inline-flex items-center gap-1.5 text-xs">
                          <span className="h-2 w-2 rounded-full" style={{ background: getProviderColor(m.provider) }} />
                          {m.provider}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">{m.total_requests?.toLocaleString()}</td>
                      <td className="py-3 pr-4 text-right tabular-nums">{formatNumber(m.total_tokens ?? 0)}</td>
                      <td className="py-3 text-right font-semibold tabular-nums">{formatCurrency(m.total_cost_usd ?? 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">No model data for this period.</p>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
