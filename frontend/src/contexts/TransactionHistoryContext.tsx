import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import type { StockRow } from "../types";

interface TransactionHistoryContextType {
   transactionsHistory: StockRow[];
   setTransactionsHistory: (data: StockRow[]) => void;
}

const TransactionHistoryContext = createContext<TransactionHistoryContextType | undefined>(undefined);

export const TransactionHistoryProvider = ({ children }: { children: ReactNode }) => {
   const [transactionsHistory, setTransactionsHistory] = useState<StockRow[]>([]);
   const [isLoaded, setIsLoaded] = useState(false);

   useEffect(() => {
      const saved = localStorage.getItem("csvData");
      if (saved) {
         try {
            setTransactionsHistory(JSON.parse(saved));
         } catch (e) {
            console.error("Failed to parse localStorage", e);
         }
      }
      setIsLoaded(true);
   }, []);

   useEffect(() => {
      if (!isLoaded) return;

      localStorage.setItem("csvData", JSON.stringify(transactionsHistory));
   }, [transactionsHistory, isLoaded]);

   return (
      <TransactionHistoryContext.Provider value={{ transactionsHistory, setTransactionsHistory }}>
         {children}
      </TransactionHistoryContext.Provider>
   );
};

export const useTransactionHistory = () => {
   const context = useContext(TransactionHistoryContext);
   if (!context) throw new Error("useData must be used within TransactionHistoryProvider");
   return context;
};
