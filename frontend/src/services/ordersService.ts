import api from "./api";

export interface OrderItemRequest {
  item_id: number;
  quantity: number;
}

export interface PlaceOrderRequest {
  customer_id: string;
  dc_id: number;
  items: OrderItemRequest[];
}

export interface OrderItemResponse {
  id: number;
  item_id: number;
  quantity: number;
  unit_price_cents: number;
}

export interface OrderResponse {
  id: string;
  customer_id: string;
  dc_id: number;
  status: string;
  total_price_cents: number;
  placed_at: string;
  delivered_at: string | null;
  order_items: OrderItemResponse[];
}

export async function placeOrder(payload: PlaceOrderRequest): Promise<OrderResponse> {
  const res = await api.post<OrderResponse>("/api/v1/orders", payload);
  return res.data;
}

export async function listOrders(skip = 0, limit = 20): Promise<OrderResponse[]> {
  const res = await api.get<OrderResponse[]>("/api/v1/orders", {
    params: { skip, limit },
  });
  return res.data;
}

export async function getOrder(id: string): Promise<OrderResponse> {
  const res = await api.get<OrderResponse>(`/api/v1/orders/${id}`);
  return res.data;
}
