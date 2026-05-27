import { useTransactionApi } from "@/hooks/useTransactionApi";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Transaction } from "@/types/transactions.types";

export function useTransactions(portfolio_id: string) {
   return useQuery({
      queryKey: ["transactions", portfolio_id],
      queryFn: () => useTransactionApi.getAllByPortfolioId(portfolio_id),
   });
}
export function useCreateTransaction(transaction: Partial<Transaction>, portfolio_id: string) {
   return useMutation({
      mutationFn: () => useTransactionApi.create(transaction, portfolio_id),
   });
}
