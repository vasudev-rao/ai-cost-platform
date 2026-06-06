"use client";
import {
  ComposedChart, Area, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, Legend,
} from "recharts";
import { formatDate, formatCurrency } from "@/lib/utils";
import type { ForecastDataPoint } from "@/types";

interface Props { data: ForecastDataPoint[]; height?: number }

export function ForecastChart({ data, height = 320 }: Props) {
  const formatted = data.map((d) => ({
    date: formatDate(d.date),
    predicted: d.predicted_usd,
    lower: d.lower_bound_usd,
    upper: d.upper_bound_usd,
    band: [d.lower_bound_usd, d.upper_bound_usd],
  }));
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={formatted} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <defs>
          <linearGradient id="confGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#8B5CF6" stopOpacity={0.2} />
            <stop offset="95%" stopColor="#8B5CF6" stopOpacity={0.05} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
        <XAxis dataKey="date" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} interval={6} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip formatter={(v: number) => formatCurrency(v)} />
        <Area type="monotone" dataKey="upper" stroke="none" fill="url(#confGrad)" name="Upper" />
        <Area type="monotone" dataKey="lower" stroke="none" fill="#fff" name="Lower" />
        <Line type="monotone" dataKey="predicted" stroke="#8B5CF6" strokeWidth={2} dot={false} name="Predicted ($)" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
