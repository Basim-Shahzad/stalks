import TransactionsHeader from "./TransactionHeader";
import TransactionsTable from "./TransactionsTable";

const Transactions = () => {
   return (
      <main className="min-h-screen p-2">
         <TransactionsHeader />
         <TransactionsTable />
      </main>
   );
};

export default Transactions;
