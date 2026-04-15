import { useContext } from "react";
import { TransactionsContext } from "../contexts/TransactionHistoryContext";

export const useTransactions = () => {
   const context = useContext(TransactionsContext);
   if (!context) throw new Error("useTransactions must be used within TransactionsProvider");
   return context;
};
