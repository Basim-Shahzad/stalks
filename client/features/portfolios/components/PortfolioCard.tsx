"use client";

import React from "react";
import { Portfolio } from "../types";
import { useRouter } from "next/navigation";

type PortfolioCardProps = {
   portfolio: Portfolio;
};

const PortfolioCard: React.FC<PortfolioCardProps> = ({ portfolio }) => {
   const router = useRouter();

   return (
      <article
         onClick={() => router.push(`/portfolio/${portfolio.id}`)}
         className="group cursor-pointer relative bg-black border border-white/10 p-6 rounded-xl hover:border-[#00FF87] transition-all duration-300 ease-in-out shadow-2xl">
         {/* Top Section: Exchange & ID */}
         <div className="flex justify-between items-start mb-6">
            <div className="flex flex-col">
               <span className="text-[10px] font-bold tracking-[0.2em] text-[#00FF87] uppercase mb-1">
                  {portfolio.exchange}
               </span>
               <h3 className="text-xl font-semibold text-white group-hover:text-[#00FF87] transition-colors">
                  {portfolio.name}
               </h3>
            </div>
         </div>

         {/* Description Body */}
         <div className="min-h-15 mb-8">
            <p className="text-gray-400 text-sm leading-relaxed line-clamp-3">
               {portfolio.description || "No additional details provided for this portfolio."}
            </p>
         </div>

         {/* Bottom Section: Meta Data */}
         <div className="flex items-center justify-between pt-4 border-t border-white/5">
            <div className="flex flex-col">
               <span className="text-[9px] uppercase text-gray-500 font-bold tracking-wider">Currency</span>
               <span className="text-sm font-mono text-white">{portfolio.currency}</span>
            </div>

            <div className="flex flex-col items-end">
               <span className="text-[9px] uppercase text-gray-500 font-bold tracking-wider">Last Modified</span>
               <span className="text-sm font-mono text-gray-300">
                  {new Date(portfolio.updatedAt).toLocaleDateString(undefined, {
                     month: "short",
                     day: "numeric",
                     year: "2-digit",
                  })}
               </span>
            </div>
         </div>

         {/* Subtle Glow Accent */}
         <div className="absolute inset-0 rounded-xl bg-[#00FF87]/0 group-hover:bg-[#00FF87]/5 pointer-events-none transition-colors duration-300" />
      </article>
   );
};

export default PortfolioCard;
