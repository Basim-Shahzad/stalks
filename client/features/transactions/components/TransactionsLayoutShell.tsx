"use client";

import Header from "@/features/layout/components/Header";
import HeaderRight from "./HeaderRight";

export default function TransactionsLayoutShell({ children }: { children: React.ReactNode }) {
   return (
      <div className="">
         <Header title="Transactions" right={<HeaderRight />} />
         {children}
      </div>
   );
}
