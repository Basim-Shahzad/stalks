"use client";

import Header from "../components/Header";
import HeaderRight from "./components/HeaderRight";

export default function Layout({ children }: { children: React.ReactNode }) {

   return (
      <div className="">
         <Header title="Transactions" right={<HeaderRight />} />
         {children}
      </div>
   );
}
