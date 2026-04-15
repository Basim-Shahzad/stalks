import { createContext, type ReactNode } from "react";
import type { TradeTransaction } from "../types";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api.services";

interface TransactionsContextType {
   transactions: TradeTransaction[] | undefined;
   isLoading: boolean;
}

interface TransactionsResponseType {
   success: boolean;
   data: TradeTransaction[];
}

export const TransactionsContext = createContext<TransactionsContextType | undefined>(undefined);

export const TransactionsProvider = ({ children }: { children: ReactNode }) => {
   const getTransactions = async (): Promise<TransactionsResponseType> => {
      const res = await api.get("/transactions");
      return res.data;
   };

   const { data, isLoading } = useQuery({
      queryKey: ["transactions"],
      queryFn: getTransactions,
   });

   return (
      <TransactionsContext.Provider
         value={{
            transactions: data?.data,
            isLoading,
         }}>
         {children}
      </TransactionsContext.Provider>
   );
};
