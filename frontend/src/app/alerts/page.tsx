"use client";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { useAlerts, useResolveAlert } from "@/hooks/useAlerts";
import { getSeverityColor } from "@/lib/utils";
import { Bell, CheckCircle, AlertTriangle, Info, XCircle } from "lucide-react";
import toast from "react-hot-toast";
import type { Alert } from "@/types";

const SEVERITY_ICONS = { info: Info, warning: AlertTriangle, critical: XCircle };

function AlertRow({ alert }: { alert: Alert }) {
  const { mutateAsync: resolve, isPending } = useResolveAlert();
  const Icon = SEVERITY_ICONS[alert.severity] ?? Info;
  const colorClass = getSeverityColor(alert.severity);

  const handleResolve = async () => {
    try {
      await resolve(alert.id);
      toast.success("Alert resolved");
    } catch {
      toast.error("Failed to resolve alert");
    }
  };

  return (
    <div className="flex items-start gap-4 border-b py-4 last:border-0">
      <div className={`mt-0.5 rounded-full p-1.5 ${colorClass}`}>
        <Icon className="h-4 w-4" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="text-sm font-medium">{alert.title}</p>
          <Badge variant={alert.severity === "critical" ? "destructive" : alert.severity === "warning" ? "warning" : "info"} className="text-[10px]">
            {alert.severity}
          </Badge>
        </div>
        <p className="text-xs text-muted-foreground">{alert.message}</p>
        <p className="text-xs text-gray-400 mt-1">{new Date(alert.created_at).toLocaleString()}</p>
      </div>
      {!alert.is_resolved && (
        <Button size="sm" variant="ghost" onClick={handleResolve} disabled={isPending} className="shrink-0 gap-1">
          <CheckCircle className="h-3.5 w-3.5" />
          Resolve
        </Button>
      )}
    </div>
  );
}

export default function AlertsPage() {
  const { data: alerts, isLoading } = useAlerts(false);
  const unresolved = (alerts as Alert[] ?? []).filter((a: Alert) => !a.is_resolved);
  const resolved = (alerts as Alert[] ?? []).filter((a: Alert) => a.is_resolved);

  return (
    <AppShell title="Alerts">
      <div className="space-y-4">
        <div className="flex items-center gap-3">
          <Bell className="h-5 w-5 text-amber-500" />
          <span className="text-sm font-medium">{unresolved.length} unresolved alert{unresolved.length !== 1 ? "s" : ""}</span>
        </div>
        <Card>
          <CardContent className="p-0">
            {isLoading ? (
              <div className="p-6 space-y-3">{[...Array(5)].map((_, i) => <Skeleton key={i} className="h-16" />)}</div>
            ) : (alerts as Alert[])?.length ? (
              <div className="px-6">
                {unresolved.length > 0 && (
                  <>
                    <p className="pt-4 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">Unresolved</p>
                    {unresolved.map((a: Alert) => <AlertRow key={a.id} alert={a} />)}
                  </>
                )}
                {resolved.length > 0 && (
                  <>
                    <p className="pt-4 pb-2 text-xs font-semibold text-muted-foreground uppercase tracking-wide">Resolved</p>
                    {resolved.slice(0, 10).map((a: Alert) => <AlertRow key={a.id} alert={a} />)}
                  </>
                )}
              </div>
            ) : (
              <div className="flex flex-col items-center justify-center py-16">
                <CheckCircle className="h-12 w-12 text-green-400 mb-3" />
                <p className="text-sm font-medium text-gray-500">All clear! No alerts.</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
