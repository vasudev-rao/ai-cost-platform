"use client";
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { CostTrend } from "@/types";

interface Props { data: CostTrend[]; height?: number }

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-lg border bg-white p-3 shadow-lg text-sm">
      <p className="font-medium mb-1">{label}</p>
      <p className="text-blue-600">Cost: {formatCurrency(payload[0]?.value ?? 0)}</p>
      <p className="text-gray-500">Requests: {payload[1]?.value?.toLocaleString()}</p>
    </div>
  );
};

export function CostTrendChart({ data, height = 300 }: Props) {
  const formatted = data.map((d) => ({ ...d, date: formatDate(d.date) }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={formatted} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="costGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#3B82F6" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip content={<CustomTooltip />} />
        <Area type="monotone" dataKey="cost_usd" stroke="#3B82F6" strokeWidth={2} fill="url(#costGrad)" name="Cost ($)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
