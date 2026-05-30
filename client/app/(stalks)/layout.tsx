"use client";

import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import { useAuthStore } from "@/stores/useAuthStore";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function Layout({ children }: { children: React.ReactNode }) {
   const { isInitialized, user } = useAuthStore();
   const router = useRouter();

   useEffect(() => {
      if (isInitialized && !user) {
         router.replace("/login");
      }
   }, [isInitialized, user]);

   // Don't render anything until auth is resolved
   if (!isInitialized) return null;

   // Auth resolved but no user — redirect is in flight
   if (!user) return null;

   return (
      <div className="flex min-h-screen bg-[#070707] text-white">
         <aside className="w-62.5 h-screen fixed top-0 left-0 z-20">
            <Sidebar />
         </aside>
         <main className="flex-1 bg-[#0F1010] rounded-3xl ml-65 mr-4 my-2.5 flex flex-col border border-white/5">
            {children}
         </main>
      </div>
   );
}
