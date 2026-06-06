import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, decimals = 2): string {
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}K`;
  return `$${value.toFixed(decimals)}`;
}

export function formatNumber(value: number): string {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`;
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`;
  return value.toString();
}

export function formatPct(value: number): string {
  const sign = value >= 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function getProviderColor(provider: string): string {
  const map: Record<string, string> = {
    openai: "#10A37F",
    anthropic: "#D4A574",
    gemini: "#4285F4",
    azure_openai: "#0089D6",
    bedrock: "#FF9900",
    self_hosted: "#6366F1",
  };
  return map[provider.toLowerCase()] ?? "#6B7280";
}

export function getSeverityColor(severity: string): string {
  const map: Record<string, string> = {
    info: "text-blue-600 bg-blue-50",
    warning: "text-amber-600 bg-amber-50",
    critical: "text-red-600 bg-red-50",
  };
  return map[severity] ?? "text-gray-600 bg-gray-50";
}
