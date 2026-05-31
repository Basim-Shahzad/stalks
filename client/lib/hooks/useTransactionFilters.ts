import { useRouter, usePathname, useSearchParams } from "next/navigation";
import { useCallback, useMemo } from "react";
import { TransactionSide } from "@/types/transactions.types";

export type TransactionFilters = {
   portfolios: Set<string>;
   sides: Set<TransactionSide>;
};

const VALID_SIDES = new Set<TransactionSide>(["BUY", "SELL", "DEPOSIT", "WITHDRAW", "INCOME", "FEE"]);

export function useTransactionFilters() {
   const router = useRouter();
   const pathname = usePathname();
   const searchParams = useSearchParams();

   // Parse current URL → filters
   const filters = useMemo<TransactionFilters>(() => {
      const portfolios = new Set(searchParams.getAll("portfolios"));
      const sides = new Set(
         searchParams.getAll("sides").filter((s): s is TransactionSide => VALID_SIDES.has(s as TransactionSide)),
      );
      return { portfolios, sides };
   }, [searchParams]);

   const activeCount = filters.portfolios.size + filters.sides.size;

   // Write filters → URL (replaces current history entry, no push)
   const setFilters = useCallback(
      (next: TransactionFilters) => {
         const params = new URLSearchParams(searchParams.toString());

         params.delete("portfolios");
         next.portfolios.forEach((id) => params.append("portfolios", id));

         params.delete("sides");
         next.sides.forEach((side) => params.append("sides", side));

         router.replace(`${pathname}?${params.toString()}`, { scroll: false });
      },
      [router, pathname, searchParams],
   );

   const clearFilters = useCallback(() => {
      const params = new URLSearchParams(searchParams.toString());
      params.delete("portfolios");
      params.delete("sides");
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
   }, [router, pathname, searchParams]);

   return { filters, activeCount, setFilters, clearFilters };
}
