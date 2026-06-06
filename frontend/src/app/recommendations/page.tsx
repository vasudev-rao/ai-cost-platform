"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useRecommendations, useAnalyzeRecommendations } from "@/hooks/useRecommendations";
import { formatCurrency } from "@/lib/utils";
import { Lightbulb, RefreshCw, ArrowRight, DollarSign, Zap, Database, Layers } from "lucide-react";
import toast from "react-hot-toast";
import type { Recommendation } from "@/types";

const REC_ICONS: Record<string, React.ElementType> = {
  model_switch: Zap, caching: Database, prompt_optimization: Layers, batching: Layers,
};

const REC_COLORS: Record<string, string> = {
  model_switch: "bg-blue-50 border-blue-200",
  caching: "bg-green-50 border-green-200",
  prompt_optimization: "bg-purple-50 border-purple-200",
  batching: "bg-amber-50 border-amber-200",
};

function RecCard({ rec }: { rec: Recommendation }) {
  const Icon = REC_ICONS[rec.rec_type] ?? Lightbulb;
  const colorClass = REC_COLORS[rec.rec_type] ?? "bg-gray-50 border-gray-200";
  return (
    <div className={`rounded-xl border p-5 ${colorClass}`}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex gap-3">
          <div className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-white shadow-sm">
            <Icon className="h-5 w-5 text-blue-600" />
          </div>
          <div>
            <h3 className="font-semibold text-sm">{rec.title}</h3>
            <p className="mt-1 text-xs text-gray-600 leading-relaxed">{rec.description}</p>
            {rec.current_model && rec.recommended_model && (
              <div className="mt-2 flex items-center gap-2 text-xs">
                <Badge variant="outline" className="font-mono text-[10px]">{rec.current_model}</Badge>
                <ArrowRight className="h-3 w-3 text-gray-400" />
                <Badge variant="secondary" className="font-mono text-[10px]">{rec.recommended_model}</Badge>
              </div>
            )}
          </div>
        </div>
        <div className="shrink-0 text-right">
          <p className="text-lg font-bold text-green-700">{formatCurrency(rec.estimated_savings_usd)}</p>
          <p className="text-xs text-gray-500">{rec.estimated_savings_pct.toFixed(0)}% savings/mo</p>
          <p className="mt-1 text-xs text-gray-400">{(rec.confidence * 100).toFixed(0)}% confidence</p>
        </div>
      </div>
    </div>
  );
}

export default function RecommendationsPage() {
  const { data: recs, isLoading } = useRecommendations();
  const { mutateAsync: analyze, isPending } = useAnalyzeRecommendations();

  const handleAnalyze = async () => {
    try {
      const result = await analyze();
      toast.success(`Generated ${(result as any).data?.generated ?? 0} new recommendations!`);
    } catch {
      toast.error("Analysis failed. Ensure you have cost data for the past 30 days.");
    }
  };

  const totalSavings = (recs as Recommendation[] ?? []).reduce((s: number, r: Recommendation) => s + r.estimated_savings_usd, 0);

  return (
    <AppShell title="Recommendations">
      <div className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            {totalSavings > 0 && (
              <div className="flex items-center gap-2 text-sm">
                <DollarSign className="h-4 w-4 text-green-600" />
                <span className="font-medium text-green-700">
                  Potential monthly savings: {formatCurrency(totalSavings)}
                </span>
              </div>
            )}
          </div>
          <Button onClick={handleAnalyze} disabled={isPending} variant="outline" className="gap-2">
            <RefreshCw className={`h-4 w-4 ${isPending ? "animate-spin" : ""}`} />
            {isPending ? "Analyzing…" : "Re-analyze"}
          </Button>
        </div>

        {/* List */}
        {isLoading ? (
          <div className="space-y-3">
            {[...Array(4)].map((_, i) => <Skeleton key={i} className="h-32" />)}
          </div>
        ) : (recs as Recommendation[])?.length ? (
          <div className="space-y-3">
            {(recs as Recommendation[]).map((r: Recommendation) => <RecCard key={r.id} rec={r} />)}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <Lightbulb className="h-12 w-12 text-gray-300 mb-4" />
              <p className="text-sm font-medium text-gray-500">No recommendations yet</p>
              <p className="text-xs text-gray-400 mt-1">Click Re-analyze to generate optimization recommendations</p>
            </CardContent>
          </Card>
        )}
      </div>
    </AppShell>
  );
}
