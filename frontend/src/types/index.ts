export interface Organization {
  id: string;
  name: string;
  slug: string;
  plan: string;
  is_active: boolean;
  created_at: string;
}

export interface Team {
  id: string;
  name: string;
  slug: string;
  organization_id: string;
  monthly_budget_usd: number;
}

export interface Project {
  id: string;
  name: string;
  slug: string;
  api_key: string;
  team_id?: string;
}

export interface CostTrend {
  date: string;
  cost_usd: number;
  tokens: number;
  requests: number;
}

export interface ModelCost {
  model: string;
  provider: string;
  total_cost_usd: number;
  total_tokens: number;
  total_requests: number;
}

export interface DashboardMetrics {
  current_month_cost_usd: number;
  previous_month_cost_usd: number;
  mom_change_pct: number;
  current_month_tokens: number;
  current_month_requests: number;
  daily_trend: CostTrend[];
  top_models: ModelCost[];
  top_teams: Array<{ team_id: string; name: string; cost_usd: number }>;
  budget_utilization_pct: number;
  anomalies_count: number;
  active_alerts_count: number;
}

export interface ForecastDataPoint {
  date: string;
  predicted_usd: number;
  lower_bound_usd: number;
  upper_bound_usd: number;
}

export interface Forecast {
  id: string;
  horizon: string;
  model_used: string;
  data_points: ForecastDataPoint[];
  total_predicted_usd: number;
  confidence_score: number;
  created_at: string;
}

export interface Recommendation {
  id: string;
  title: string;
  description: string;
  rec_type: string;
  current_model?: string;
  recommended_model?: string;
  estimated_savings_usd: number;
  estimated_savings_pct: number;
  confidence: number;
  evidence?: Record<string, unknown>;
  is_applied: boolean;
  created_at: string;
}

export interface Alert {
  id: string;
  alert_type: string;
  severity: "info" | "warning" | "critical";
  title: string;
  message: string;
  is_resolved: boolean;
  created_at: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string;
  role: string;
  organization_id?: string;
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
}
