import api from "./api";

export interface DCResponse {
  id: number;
  name: string;
  lat: number;
  lng: number;
  zipcode: string;
  region_id: string;
  address: string | null;
  city: string | null;
  state: string | null;
  is_active: boolean;
  created_at: string;
  inventory_count: number;
}

export interface DCCreate {
  name: string;
  lat: number;
  lng: number;
  zipcode: string;
  address?: string;
  city?: string;
  state?: string;
  is_active?: boolean;
}

export async function listDCs(region?: string): Promise<DCResponse[]> {
  const res = await api.get<DCResponse[]>("/api/v1/dcs", {
    params: region ? { region } : {},
  });
  return res.data;
}

export async function getDC(id: number): Promise<DCResponse> {
  const res = await api.get<DCResponse>(`/api/v1/dcs/${id}`);
  return res.data;
}

export async function createDC(payload: DCCreate): Promise<DCResponse> {
  const res = await api.post<DCResponse>("/api/v1/dcs", payload);
  return res.data;
}
