import api from "./api";

export interface ItemResponse {
  id: number;
  sku: string;
  name: string;
  description: string | null;
  category: string;
  unit_price_cents: number;
  weight_grams: number | null;
  is_active: boolean;
  created_at: string;
}

export async function listItems(category?: string): Promise<ItemResponse[]> {
  const res = await api.get<ItemResponse[]>("/api/v1/items", {
    params: category ? { category } : {},
  });
  return res.data;
}

export async function getItem(id: number): Promise<ItemResponse> {
  const res = await api.get<ItemResponse>(`/api/v1/items/${id}`);
  return res.data;
}
