import api from "@/services/api.service";
import { Transaction, TransactionList } from "./types";
import { TransactionFilters } from "./hooks/useTransactionFilters";

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
      return data;
   },
   create: async (transaction: Partial<Transaction>, portfolio_id: string) => {
      const { data } = await api.post<Transaction>(`/transactions/${portfolio_id}`, transaction);
      return data;
   },
   createFromMmkPdf: async (file: File, portfolio_id: string) => {
      const formData = new FormData();
      formData.append("file", file);

      const { data } = await api.post<{
         message: string;
         job_id: string;
      }>(`/transactions/${portfolio_id}/upload/pdf`, formData, {
         headers: {
            // This forces Axios to treat it as a proper form submission
            "Content-Type": "multipart/form-data",
         },
      });
      return data;
   },
};
