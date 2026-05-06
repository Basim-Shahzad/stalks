import { useQuery } from "@tanstack/react-query";
import type { StockByApi } from "../types";
import api from "../services/api.services";

interface StocksPage {
   stocks: StockByApi[];
   page: number;
   page_size: number;
   total: number;
   total_pages: number;
   has_next: boolean;
   has_prev: boolean;
}

interface StocksAll {
   stocks: StockByApi[];
   total: number;
}

const getStocksData = async (page: number, pageSize: number): Promise<StocksPage> => {
   const res = await api.get<StocksPage>("/stocks", {
      params: { page, page_size: pageSize },
   });
   return res.data;
};

const getAllStocksData = async (): Promise<StocksAll> => {
   const res = await api.get<StocksAll>("/stocks", {
      params: { paginated: false },
   });
   return res.data;
};

export function useStocks(
   paginated?: true,
   page?: number,
   pageSize?: number,
   enabled?: boolean,
): ReturnType<typeof useQuery<StocksPage>>;
export function useStocks(
   paginated: false,
   page?: number,
   pageSize?: number,
   enabled?: boolean,
): ReturnType<typeof useQuery<StocksAll>>;
export function useStocks(paginated: boolean = true, page: number = 1, pageSize: number = 10, enabled: boolean = true) {
   return useQuery({
      queryKey: paginated === false ? ["stocks"] : ["stocks", page, pageSize],
      queryFn: paginated === false ? () => getAllStocksData() : () => getStocksData(page, pageSize),
      enabled: paginated === false ? enabled : true,
      placeholderData: (prev) => prev,
      staleTime: 60_000,
   });
}
