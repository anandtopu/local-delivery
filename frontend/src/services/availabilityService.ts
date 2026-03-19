import api from "./api";

export interface AvailabilityResult {
  dc_id: number;
  dc_name: string;
  region_id: string;
  item_id: number;
  item_name: string;
  quantity: number;
  travel_minutes: number;
  distance_km: number;
  can_deliver_in_1h: boolean;
}

export interface AvailabilityResponse {
  results: AvailabilityResult[];
  query_lat: number;
  query_lng: number;
  cache_status: "HIT" | "MISS" | "PARTIAL";
  response_ms: number;
}

export async function checkAvailability(
  lat: number,
  lng: number,
  itemIds: number[],
  radiusKm: number = 15
): Promise<AvailabilityResponse> {
  const res = await api.get<AvailabilityResponse>("/api/v1/availability", {
    params: {
      lat,
      lng,
      item_ids: itemIds.join(","),
      radius_km: radiusKm,
    },
  });
  return res.data;
}
