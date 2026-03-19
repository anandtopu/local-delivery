import useSWR from "swr";
import {
  AvailabilityResponse,
  checkAvailability,
} from "../services/availabilityService";

interface AvailabilityParams {
  lat: number;
  lng: number;
  itemIds: number[];
  radiusKm?: number;
}

export function useAvailability(params: AvailabilityParams | null) {
  const key = params
    ? ["availability", params.lat, params.lng, params.itemIds.join(","), params.radiusKm ?? 15]
    : null;

  const { data, error, isLoading, mutate } = useSWR<AvailabilityResponse>(
    key,
    () =>
      checkAvailability(
        params!.lat,
        params!.lng,
        params!.itemIds,
        params!.radiusKm ?? 15
      )
  );

  return { data, error, isLoading, mutate };
}
