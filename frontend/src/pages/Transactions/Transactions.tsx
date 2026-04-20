import BuyAndSell from "./BuyAndSell";
import TransactionsHeader from "./TransactionHeader";
import TransactionsTable from "./TransactionsTable";

const Transactions = () => {
   return (
      <main className="min-h-screen p-2">
         <div className="flex items-center justify-between">
            <div>
               <TransactionsHeader />
            </div>

            <div>
               <BuyAndSell />
            </div>
         </div>
         <TransactionsTable />
      </main>
   );
};

export default Transactions;
