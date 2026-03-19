import useSWR from "swr";
import { DCResponse, listDCs } from "../services/dcsService";

export function useDCs(region?: string) {
  const { data, error, isLoading, mutate } = useSWR<DCResponse[]>(
    ["dcs", region ?? ""],
    () => listDCs(region)
  );

  return { dcs: data ?? [], error, isLoading, mutate };
}
