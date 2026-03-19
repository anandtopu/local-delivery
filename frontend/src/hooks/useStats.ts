import useSWR from "swr";
import api from "../services/api";

export interface StatsResponse {
  total_dcs: number;
  total_items: number;
  total_orders: number;
  orders_today: number;
  active_regions: number;
}

async function fetchStats(): Promise<StatsResponse> {
  const res = await api.get<StatsResponse>("/api/v1/admin/stats");
  return res.data;
}

export function useStats() {
  const { data, error, isLoading } = useSWR<StatsResponse>(
    "admin-stats",
    fetchStats,
    { refreshInterval: 10_000 }
  );

  return { stats: data, error, isLoading };
}
