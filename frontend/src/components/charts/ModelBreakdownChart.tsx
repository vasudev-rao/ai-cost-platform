"use client";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { formatCurrency } from "@/lib/utils";
import type { ModelCost } from "@/types";

const COLORS = ["#3B82F6","#10B981","#F59E0B","#EF4444","#8B5CF6","#06B6D4","#F97316","#84CC16"];

interface Props { data: ModelCost[] }

export function ModelBreakdownChart({ data }: Props) {
  const top = data.slice(0, 7);
  const other = data.slice(7).reduce((s, m) => s + m.total_cost_usd, 0);
  const chartData = [
    ...top.map((m) => ({ name: m.model, value: m.total_cost_usd })),
    ...(other > 0 ? [{ name: "Other", value: other }] : []),
  ];
  return (
    <ResponsiveContainer width="100%" height={280}>
      <PieChart>
        <Pie data={chartData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false} fontSize={11}>
          {chartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
        </Pie>
        <Tooltip formatter={(v: number) => formatCurrency(v)} />
      </PieChart>
    </ResponsiveContainer>
  );
}
