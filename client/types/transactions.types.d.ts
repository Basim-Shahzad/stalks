export type TransactionSide = "SELL" | "BUY" | "DEPOSIT" | "WITHDRAW" | "INCOME" | "FEE";

export interface Transaction {
   id: string;
   transactionDate: string;
   company: string;
   symbol: string;
   sector: string;
   side: TransactionSide;
   quantity: number;
   rate: number;
   commission: number;
   taxes: number;
   charges: number;
   totalAmount: number;
}

export type TransactionList = Transaction[];