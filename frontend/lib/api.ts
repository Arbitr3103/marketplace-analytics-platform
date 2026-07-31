export type DashboardSummary = {
  period_days: number;
  stores: number;
  sku_count: number;
  orders: number;
  revenue: number;
  average_order_value: number;
  stock_alerts: number;
  generated_at: string;
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function getDashboard(days = 30): Promise<DashboardSummary> {
  const response = await fetch(`${API_URL}/api/v1/dashboard?days=${days}`, {
    cache: "no-store",
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new Error(`Dashboard API returned ${response.status}`);
  }

  return (await response.json()) as DashboardSummary;
}
