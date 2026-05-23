"use client";

import { useEffect } from "react";
import Header from "./components/Header";
import Sidebar from "./components/Sidebar";
import { useAuthStore } from "@/stores/useAuthStore";
import { useRouter } from "next/navigation";

export default function Layout({ children }: { children: React.ReactNode }) {
   const { accessToken, user } = useAuthStore();
   const router = useRouter();

   useEffect(() => {
      if (!accessToken || !user) router.push("/");
   }, [accessToken, user, router]);

   if (!accessToken || !user) return null;

   return (
      <div className="flex min-h-screen bg-[#070707] text-white">
         <aside className="w-[250px] h-screen fixed top-0 left-0 z-20">
            <Sidebar />
         </aside>
         <main className="flex-1 bg-[#0F1010] rounded-3xl ml-[260px] mr-[16px] my-[10px] flex flex-col border border-white/5">
            {children}
         </main>
      </div>
   );
}
