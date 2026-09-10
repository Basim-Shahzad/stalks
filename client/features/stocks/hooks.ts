import api from "@/services/api.service";
import { useQuery } from "@tanstack/react-query";
import { OHLCV } from "./components/CandlestickChart";

type MarketDataType = {
   exchange: string;
   symbol: string;
   rows: number;
   data: OHLCV[];
};

export function useMarketData(exchange: string, symbol: string, limit: number) {
   return useQuery({
      queryKey: ["marketData", exchange, symbol, limit],
      queryFn: () => api.get<MarketDataType>(`/market/data/${exchange}/${symbol}`, { params: { limit } }),
      placeholderData: (prev) => prev,
      staleTime: Infinity,
   });
}
