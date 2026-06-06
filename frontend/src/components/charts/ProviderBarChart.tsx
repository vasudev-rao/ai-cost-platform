"use client";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts";
import { formatCurrency, getProviderColor } from "@/lib/utils";

interface Props { data: Array<{ provider: string; total_cost_usd: number; total_requests: number }> }

export function ProviderBarChart({ data }: Props) {
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
        <CartesianGrid strokeDasharray="3 3" stroke="#F1F5F9" />
        <XAxis dataKey="provider" tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <YAxis tickFormatter={(v) => `$${v}`} tick={{ fontSize: 11 }} tickLine={false} axisLine={false} />
        <Tooltip formatter={(v: number) => formatCurrency(v)} />
        <Bar dataKey="total_cost_usd" radius={[4, 4, 0, 0]} name="Cost ($)">
          {data.map((entry, i) => (
            <Cell key={i} fill={getProviderColor(entry.provider)} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
