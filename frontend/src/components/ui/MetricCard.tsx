import { Card, CardContent } from "./card";
import { cn, formatPct } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

interface Props {
  title: string;
  value: string;
  change?: number;
  icon: LucideIcon;
  iconColor?: string;
  description?: string;
}

export function MetricCard({ title, value, change, icon: Icon, iconColor = "text-blue-600", description }: Props) {
  const isPositive = (change ?? 0) >= 0;
  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between mb-3">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          <div className={cn("flex h-9 w-9 items-center justify-center rounded-lg bg-gray-100", iconColor.replace("text-", "bg-").replace("600", "100"))}>
            <Icon className={cn("h-5 w-5", iconColor)} />
          </div>
        </div>
        <p className="text-2xl font-bold">{value}</p>
        {change !== undefined && (
          <p className={cn("mt-1 text-xs font-medium", isPositive ? "text-red-600" : "text-green-600")}>
            {formatPct(change)} vs last month
          </p>
        )}
        {description && <p className="mt-1 text-xs text-muted-foreground">{description}</p>}
      </CardContent>
    </Card>
  );
}
