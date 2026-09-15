import type { TransactionList } from "@/features/transactions/types";

class Stats {
   transactions: TransactionList;
   constructor(transactions: TransactionList) {
      this.transactions = transactions;
   }

   getTotalCapital(): number {
      let invested = 0;

      this.transactions?.forEach((t) => {
         if (t.side !== "DEPOSIT" && t.side !== "WITHDRAW") return;
         const totalAmount = parseFloat(String(t.totalAmount)) || 0;
         invested += t.side === "DEPOSIT" ? totalAmount : -totalAmount;
      });
      return invested;
   }

   getTotalFees(): number {
      return (
         this.transactions?.reduce((fees, t) => {
            if (t.side !== "BUY" && t.side !== "SELL") return fees;
            const commission = parseFloat(String(t.commission)) || 0;
            const charges = parseFloat(String(t.charges)) || 0;
            const taxes = parseFloat(String(t.taxes)) || 0;
            return fees + commission + charges + taxes;
         }, 0) ?? 0
      );
   }

   getTotalBuyValue(): number {
      return this.transactions.reduce((buyValue, t) => {
         if (t.side !== "BUY") return buyValue;
         return buyValue + (parseFloat(String(t.totalAmount)) || 0);
      }, 0);
   }

   getTotalSellValue(): number {
      return this.transactions.reduce((sellValue, t) => {
         if (t.side !== "SELL") return sellValue;
         return sellValue + (parseFloat(String(t.totalAmount)) || 0);
      }, 0);
   }
}

export { Stats };
