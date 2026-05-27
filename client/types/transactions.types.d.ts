export interface Transaction {
   id: string;
   transactionDate: string;
   company: string;
   symbol: string;
   sector: string;
   side: "SELL" | "BUY";
   quantity: number;
   rate: number;
   commission: number;
   taxes: number;
   charges: number;
   totalAmount: number;
}

export type TransactionList = Transaction[];