import api from "@/services/api.service";
import { MarketDataResponse } from "./types";

export const useMarketDataApi = {
   get: async (exchange: string, symbol: string) => {
      const { data } = await api.get<MarketDataResponse>(`/market/data/${exchange}/${symbol}`);
      return data;
   },
};
