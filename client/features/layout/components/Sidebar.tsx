"use client";

import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/features/auth/store";
import { LayoutDashboard, TrendingUp, BookOpen, Notebook, PieChart, BarChart2 } from "lucide-react";
import Image from "next/image";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";

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
      <aside className="h-screen w-full flex flex-col shrink-0 z-10 bg-background">

         <div className="px-2 py-4 cursor-pointer flex items-center gap-2 hover:bg-accent/50">
            <Avatar>
               <AvatarFallback className="bg-primary text-primary-foreground">{getInitials(user?.name ?? "")}</AvatarFallback>
            </Avatar>
            <div className="select-none">
               <span className="text-foreground">{user?.name}</span>
               <div className="text-[9px] text-muted-foreground">{user?.email}</div>
            </div>
         </div>

         <div className="px-4 pt-4 pb-1 text-[9px] tracking-[2px] text-muted-foreground/60 font-bold">NAVIGATION</div>

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
                        active ? "bg-card text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"
                     }`}>
                     <item.icon size={18} className={`flex-shrink-0 ${active ? "stroke-2" : "stroke-[1.5]"}`} />
                     <span className="flex-1 text-left text-xs tracking-wide">{item.label}</span>
                     {item.badge && (
                        <span
                           className={`px-1.5 py-0.5 rounded text-[8px] border font-bold ${
                              item.badge ? "bg-secondary text-muted-foreground border-border" : ""
                           }`}>
                           {item.badge ? item.badge : ""}
                        </span>
                     )}
                  </button>
               );
            })}
         </nav>

         {/* Bottom Nav */}
      </aside>
   );
}
