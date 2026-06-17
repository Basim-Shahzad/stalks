import { useTransactionApi } from "@/hooks/useTransactionApi";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Transaction } from "@/types/transactions.types";
import { TransactionFilters } from "@/lib/hooks/useTransactionFilters";

export function useTransactions(filters?: TransactionFilters) {
   return useQuery({
      queryKey: ["transactions", [...(filters?.portfolios ?? [])], [...(filters?.sides ?? [])]],
      queryFn: () => useTransactionApi.getAll(filters),
   });
}

export function useCreateTransaction(transaction: Partial<Transaction>, portfolio_id: string) {
   return useMutation({
      mutationFn: () => useTransactionApi.create(transaction, portfolio_id),
   });
}
