"use client";

import Sidebar from "./Sidebar";
import { useAuthStore } from "@/features/auth/store";
import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";

const PUBLIC_PATHS = ["/", "/login", "/signup"];

export default function AppShell({ children }: { children: React.ReactNode }) {
   const { isInitialized, user } = useAuthStore();
   const router = useRouter();
   const pathname = usePathname();
   const isPublic = PUBLIC_PATHS.includes(pathname);

   useEffect(() => {
      if (isInitialized && !user && !isPublic) {
         router.replace("/login");
      }
   }, [isInitialized, user, isPublic, router]);

   if (!isInitialized) return null;
   if (!user && !isPublic) return null;

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