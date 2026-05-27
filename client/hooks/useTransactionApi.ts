import api from "@/services/api.service";
import { Transaction, TransactionList } from "../types/transactions.types";

export const useTransactionApi = {
   getAllByPortfolioId: async (portfolio_id: string) => {
      const { data } = await api.get<TransactionList>(`/transactions/`, {
         params: { portfolio_id },
      });
      return data;
   },
   create: async (transaction: Partial<Transaction>, portfolio_id: string) => {
      const { data } = await api.post<Transaction>(`/transactions/${portfolio_id}`, transaction);
      return data;
   },
};
