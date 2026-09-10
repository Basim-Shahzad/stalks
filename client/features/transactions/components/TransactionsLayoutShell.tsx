"use client";

import { useState } from "react";
import Header from "@/features/layout/components/Header";
import HeaderRight from "./HeaderRight";
import AddTransactionsModal from "./AddTransactionsModal";

export default function TransactionsLayoutShell({ children }: { children: React.ReactNode }) {
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
