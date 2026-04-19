import { useQuery } from "@tanstack/react-query";
import api from "../services/api.services";
import type { StockByApi } from "../types";

interface StocksPage {
   stocks: StockByApi[];
   page: number;
   page_size: number;
   total: number;
   total_pages: number;
   has_next: boolean;
   has_prev: boolean;
}

const getStocksData = async (page: number, pageSize: number): Promise<StocksPage> => {
   const res = await api.get<StocksPage>("/stocks", {
      params: { page, page_size: pageSize },
   });
   return res.data;
};

export const useStocks = (page: number = 1, pageSize: number = 10) => {
   return useQuery({
      queryKey: ["stocks", page, pageSize],
      queryFn: () => getStocksData(page, pageSize),
      placeholderData: (prev) => prev,
   });
};