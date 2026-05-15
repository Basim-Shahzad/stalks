import api from "@/services/api.service";
import type { Portfolio, PortfolioList } from "./portfolios.types";

export const usePortfolio = {
   getAll: async () => {
      const { data } = await api.get<PortfolioList>("/portfolios");
      return data;
   },
   create: async (portfolio: Partial<Portfolio>) => {
      const { data } = await api.post<Portfolio>("/portfolios", portfolio);
      return data;
   },
   get: async (id: string) => {
      const { data } = await api.get<Portfolio>(`/portfolios/${id}`);
      return data;
   },
};
