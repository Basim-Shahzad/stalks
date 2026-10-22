import { useQuery } from "@tanstack/react-query";
import { useMarketDataApi } from "./api";

export function useMarketData(exchange: string, symbol: string) {
   return useQuery({
      queryKey: ["marketData", exchange, symbol],
      queryFn: () => useMarketDataApi.get(exchange, symbol),
      placeholderData: (prev) => prev,
      staleTime: Infinity,
   });
}
