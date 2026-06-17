import { usePortfolioApi } from "@/hooks/usePortfolioApi";
import { useQuery, useMutation } from "@tanstack/react-query";
import { Portfolio } from "@/types/portfolios.types";

export function usePortfolios() {
   return useQuery({
      queryKey: ["portfolios"],
      queryFn: () => usePortfolioApi.getAll(),
   });
}

export function usePortfolio(id: string) {
   return useQuery({
      queryKey: ["portfolio", id],
      queryFn: () => usePortfolioApi.get(id),
   });
}

export function useCreatePortfolio(portfolio: Partial<Portfolio>) {
   return useMutation({
      mutationFn: () => usePortfolioApi.create(portfolio),
   });
}

export function usePortfolioHoldings(id: string) {
   return useQuery({
      queryKey: ["portfolioHoldings", id],
      queryFn: () => usePortfolioApi.holdings(id),
      placeholderData: (prev) => prev,
      staleTime: Infinity,
   });
}
