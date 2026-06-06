"use client";
import { AppShell } from "@/components/layout/AppShell";
import { MetricCard } from "@/components/ui/MetricCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CostTrendChart } from "@/components/charts/CostTrendChart";
import { ModelBreakdownChart } from "@/components/charts/ModelBreakdownChart";
import { Skeleton } from "@/components/ui/skeleton";
import { useDashboard } from "@/hooks/useDashboard";
import { formatCurrency, formatNumber } from "@/lib/utils";
import { DollarSign, Hash, Activity, AlertTriangle, TrendingUp, Zap } from "lucide-react";

export default function DashboardPage() {
  const { data, isLoading } = useDashboard();

  if (isLoading) return (
    <AppShell title="Dashboard">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
      </div>
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <Skeleton className="h-80" />
        <Skeleton className="h-80" />
      </div>
    </AppShell>
  );

  return (
    <AppShell title="Dashboard">
      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          title="Monthly Spend"
          value={formatCurrency(data?.current_month_cost_usd ?? 0)}
          change={data?.mom_change_pct}
          icon={DollarSign}
          iconColor="text-blue-600"
        />
        <MetricCard
          title="Total Tokens"
          value={formatNumber(data?.current_month_tokens ?? 0)}
          icon={Hash}
          iconColor="text-purple-600"
          description="This month"
        />
        <MetricCard
          title="API Requests"
          value={formatNumber(data?.current_month_requests ?? 0)}
          icon={Activity}
          iconColor="text-green-600"
          description="This month"
        />
        <MetricCard
          title="Active Alerts"
          value={String(data?.active_alerts_count ?? 0)}
          icon={AlertTriangle}
          iconColor="text-amber-600"
          description={`${data?.anomalies_count ?? 0} anomalies detected`}
        />
      </div>

      {/* Charts Row */}
      <div className="mt-4 grid gap-4 lg:grid-cols-3">
        {/* Trend */}
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <TrendingUp className="h-4 w-4 text-blue-600" /> Daily Cost Trend (30 days)
            </CardTitle>
          </CardHeader>
          <CardContent>
            <CostTrendChart data={data?.daily_trend ?? []} height={280} />
          </CardContent>
        </Card>

        {/* Model Breakdown */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Zap className="h-4 w-4 text-purple-600" /> Cost by Model
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ModelBreakdownChart data={data?.top_models ?? []} />
          </CardContent>
        </Card>
      </div>

      {/* Top Models Table */}
      <div className="mt-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Top Models by Spend</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
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
                  {(data?.top_models ?? []).slice(0, 8).map((m: any, i: number) => (
                    <tr key={i} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-medium">{m.model}</td>
                      <td className="py-3 pr-4">
                        <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-0.5 text-xs font-medium text-blue-700">
                          {m.provider}
                        </span>
                      </td>
                      <td className="py-3 pr-4 text-right tabular-nums">{m.total_requests?.toLocaleString()}</td>
                      <td className="py-3 pr-4 text-right tabular-nums">{formatNumber(m.total_tokens ?? 0)}</td>
                      <td className="py-3 text-right font-medium tabular-nums">{formatCurrency(m.total_cost_usd ?? 0)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {!data?.top_models?.length && (
                <p className="py-8 text-center text-sm text-muted-foreground">No cost data yet. Ingest events via the SDK or API.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
