"use client";

import { useState } from "react";
import Header from "../components/Header";
import HeaderRight from "./components/HeaderRight";
import AddTransactionsModal from "./components/AddTransactionsModal";

export default function Layout({ children }: { children: React.ReactNode }) {
   const [isAddTransactionModalOpen, setIsAddTransactionModalOpen] = useState<boolean>(false);

   return (
      <div className="">
         <Header
            title="Transactions"
            right={<HeaderRight setIsAddTransactionModalOpen={setIsAddTransactionModalOpen} />}
         />
         <AddTransactionsModal isOpen={isAddTransactionModalOpen} onOpenChange={setIsAddTransactionModalOpen} />
         {children}

      </div>
   );
}
