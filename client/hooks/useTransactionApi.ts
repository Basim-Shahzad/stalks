import api from "@/services/api.service";
import { Transaction, TransactionList } from "../types/transactions.types";
import { TransactionFilters } from "@/lib/hooks/useTransactionFilters";

export const useTransactionApi = {
   getAll: async (filters?: TransactionFilters) => {
      const { data } = await api.get<TransactionList>(`/transactions/`, {
         params: {
            portfolios: filters?.portfolios ? [...filters.portfolios] : undefined,
            sides: filters?.sides ? [...filters.sides] : undefined,
         },
         paramsSerializer: (params) => {
            const search = new URLSearchParams();
            for (const [key, value] of Object.entries(params)) {
               if (Array.isArray(value)) {
                  value.forEach((v) => search.append(key, v));
               } else if (value !== undefined) {
                  search.append(key, value);
               }
            }
            return search.toString();
         },
      });
      console.log("raw response:", data); // inspect this
      return data;
   },
   create: async (transaction: Partial<Transaction>, portfolio_id: string) => {
      const { data } = await api.post<Transaction>(`/transactions/${portfolio_id}`, transaction);
      return data;
   },
};
