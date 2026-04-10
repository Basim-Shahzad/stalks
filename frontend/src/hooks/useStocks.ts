import { useQuery } from "@tanstack/react-query";
import api from "../services/api.services";
import type { StockByApi } from "../types";

const getStocksData = async () => {
   const res = await api.get<StockByApi[]>("/stocks");
   return res.data;
};

export const useStocks = () => {
   return useQuery({
      queryKey: ["stocks"],
      queryFn: getStocksData,
   });
};
