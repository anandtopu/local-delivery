import useSWR from "swr";
import { OrderResponse, listOrders } from "../services/ordersService";

export function useOrders(skip = 0, limit = 20) {
  const { data, error, isLoading, mutate } = useSWR<OrderResponse[]>(
    ["orders", skip, limit],
    () => listOrders(skip, limit),
    { refreshInterval: 30_000 }
  );

  return { orders: data ?? [], error, isLoading, mutate };
}
