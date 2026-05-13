"use client";

import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/stores/useAuthStore";
import { LayoutDashboard, TrendingUp, BookOpen, Notebook, PieChart, BarChart2 } from "lucide-react";
import Image from "next/image";
import { Separator, Avatar } from "@heroui/react";

function getInitials(name: string): string {
   if (!name) return "";
   const words = name.trim().split(/\s+/);
   return words
      .slice(0, 2)
      .map((word) => word[0]?.toUpperCase() ?? "")
      .join("");
}

export default function Sidebar() {
   const router = useRouter();
   const pathname = usePathname();
   const user = useAuthStore((state) => state.user);

   // Helper to determine if a route is active
   const isActive = (id: string) => pathname === `/${id}` || (id === "dashboard" && pathname === "/");

   return (
      <aside className="h-screen w-full flex flex-col shrink-0 z-10 border-r border-[#1e2023] bg-black">
         {/* Logo Section */}
         <div className="flex items-center gap-2.5 p-3 pb-4 border-b border-[#1e2023]">
            <Image src="/logo.png" alt="logo" width={32} height={32} priority={true} />
            <div>
               <div className="font-extrabold text-lg tracking-tight text-[#ffffff] leading-none">STALKS</div>
               <div className="mt-0.5 text-[9px] tracking-[2px] text-[#888888]">TRADE · TRACK · WIN</div>
            </div>
         </div>

         <div className="px-4 pt-4 pb-1 text-[9px] tracking-[2px] text-[#444444] font-bold">NAVIGATION</div>

         {/* Primary Nav */}
         <nav className="flex-1 px-2 py-1 overflow-y-auto mt-2">
            {[
               { id: "portfolio", label: "Portfolio", icon: LayoutDashboard },
               { id: "stocks", label: "Stocks", icon: LayoutDashboard },
               { id: "transactions", label: "Transactions", icon: PieChart },
               { id: "strategies", label: "Strategies", icon: Notebook, badge: "3" },
            ].map((item) => {
               const active = isActive(item.id);
               return (
                  <button
                     key={item.id}
                     onClick={() => router.push(`/${item.id}`)}
                     className={`group flex items-center w-full mb-0.5 rounded px-2.5 py-2 gap-2.5 transition-all duration-150 whitespace-nowrap ${
                        active ? "bg-[#111213] text-[#00ff87]" : "text-[#a0a0a0] hover:bg-[#161718] hover:text-white"
                     }`}>
                     <item.icon size={18} className={`flex-shrink-0 ${active ? "stroke-2" : "stroke-[1.5]"}`} />
                     <span className="flex-1 text-left text-xs tracking-wide">{item.label}</span>
                     {item.badge && (
                        <span
                           className={`px-1.5 py-0.5 rounded text-[8px] border font-bold ${
                              item.badge ? "bg-[#1c1d1f] text-[#888888] border-[#2e3033]" : ""
                           }`}>
                           {item.badge ? item.badge : ""}
                        </span>
                     )}
                  </button>
               );
            })}
         </nav>

         <Separator className="bg-white/20" />

         {/* Bottom Nav */}
         <div className="px-2 pt-3 pb-4 cursor-pointer flex items-center gap-2 hover:bg-gray-900/25">
            <Avatar className="bg-black" color="default">
               <Avatar.Fallback className="bg-green-500">{getInitials(user!.name)}</Avatar.Fallback>
            </Avatar>
            <div className="select-none">
               <span className="text-white">{user?.name}</span>
               <div className="text-[9px] text-[#888888]">{user?.email}</div>
            </div>
         </div>
      </aside>
   );
}
