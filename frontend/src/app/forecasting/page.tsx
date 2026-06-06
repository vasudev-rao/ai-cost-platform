"use client";
import { useState } from "react";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { ForecastChart } from "@/components/charts/ForecastChart";
import { Skeleton } from "@/components/ui/skeleton";
import { useLatestForecasts, useGenerateForecast } from "@/hooks/useForecasts";
import { formatCurrency } from "@/lib/utils";
import { TrendingUp, RefreshCw, Brain, Calendar } from "lucide-react";
import toast from "react-hot-toast";

const HORIZONS = [
  { value: "30d", label: "30 Days" },
  { value: "90d", label: "90 Days" },
  { value: "365d", label: "1 Year" },
];

export default function ForecastingPage() {
  const [horizon, setHorizon] = useState("30d");
  const { data: forecasts, isLoading } = useLatestForecasts();
  const { mutateAsync: generate, isPending } = useGenerateForecast();

  const handleGenerate = async () => {
    try {
      await generate(horizon);
      toast.success("Forecast generated successfully!");
    } catch {
      toast.error("Failed to generate forecast. Need at least 7 days of cost data.");
    }
  };

  const activeF = forecasts?.[0];

  return (
    <AppShell title="Cost Forecasting">
      <div className="space-y-4">
        {/* Controls */}
        <div className="flex items-center gap-3">
          <Select value={horizon} onValueChange={setHorizon} options={HORIZONS} className="w-40" />
          <Button onClick={handleGenerate} disabled={isPending} className="gap-2">
            <RefreshCw className={`h-4 w-4 ${isPending ? "animate-spin" : ""}`} />
            {isPending ? "Generating…" : "Generate Forecast"}
          </Button>
        </div>

        {/* Summary Cards */}
        {activeF && (
          <div className="grid gap-4 md:grid-cols-3">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <TrendingUp className="h-5 w-5 text-purple-600" />
                  <p className="text-sm text-muted-foreground">Predicted Total</p>
                </div>
                <p className="text-2xl font-bold">{formatCurrency(activeF.total_predicted_usd ?? 0)}</p>
                <p className="text-xs text-muted-foreground mt-1">For next {activeF.horizon}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Brain className="h-5 w-5 text-blue-600" />
                  <p className="text-sm text-muted-foreground">Model Used</p>
                </div>
                <p className="text-2xl font-bold capitalize">{activeF.model_used ?? "Prophet"}</p>
                <p className="text-xs text-muted-foreground mt-1">Forecasting engine</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center gap-3 mb-2">
                  <Calendar className="h-5 w-5 text-green-600" />
                  <p className="text-sm text-muted-foreground">Confidence Score</p>
                </div>
                <p className="text-2xl font-bold">
                  {((activeF.confidence_score ?? 0) * 100).toFixed(0)}%
                </p>
                <p className="text-xs text-muted-foreground mt-1">Model confidence</p>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Chart */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base font-semibold">Cost Forecast with Confidence Intervals</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-80" />
            ) : activeF?.data_points?.length ? (
              <ForecastChart data={activeF.data_points} height={320} />
            ) : (
              <div className="flex h-64 items-center justify-center text-muted-foreground text-sm">
                <div className="text-center">
                  <TrendingUp className="mx-auto h-10 w-10 mb-3 opacity-30" />
                  <p>No forecast data yet.</p>
                  <p className="text-xs mt-1">Select a horizon and click Generate Forecast.</p>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Historical Forecasts */}
        {(forecasts?.length ?? 0) > 1 && (
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-base font-semibold">Previous Forecasts</CardTitle>
            </CardHeader>
            <CardContent>
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left text-xs font-medium text-muted-foreground">
                    <th className="pb-3 pr-4">Horizon</th>
                    <th className="pb-3 pr-4">Model</th>
                    <th className="pb-3 pr-4 text-right">Predicted Total</th>
                    <th className="pb-3 text-right">Confidence</th>
                  </tr>
                </thead>
                <tbody>
                  {forecasts?.map((f: any) => (
                    <tr key={f.id} className="border-b last:border-0">
                      <td className="py-3 pr-4 font-medium">{f.horizon}</td>
                      <td className="py-3 pr-4 capitalize">{f.model_used}</td>
                      <td className="py-3 pr-4 text-right">{formatCurrency(f.total_predicted_usd)}</td>
                      <td className="py-3 text-right">{((f.confidence_score ?? 0) * 100).toFixed(0)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
