import { createContext, type ReactNode, type Dispatch, type SetStateAction, useState } from "react";
import type { TradeTransaction } from "../types";
import { useQuery } from "@tanstack/react-query";
import api from "../services/api.services";

interface TransactionsContextType {
   transactions: TradeTransaction[] | undefined;
   isLoading: boolean;
   globalFilter: string
   setGlobalFilter: Dispatch<SetStateAction<string>>
}

interface TransactionsResponseType {
   success: boolean;
   data: TradeTransaction[];
}

export const TransactionsContext = createContext<TransactionsContextType | undefined>(undefined);

export const TransactionsProvider = ({ children }: { children: ReactNode }) => {
   const [globalFilter, setGlobalFilter] = useState("");
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
            globalFilter,
            setGlobalFilter
         }}>
         {children}
      </TransactionsContext.Provider>
   );
};
