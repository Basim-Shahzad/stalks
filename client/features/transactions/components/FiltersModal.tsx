"use client";

import React, { useState, useEffect } from "react";
import { PortfolioList } from "@/features/portfolios/types";
import { TransactionSide } from "../types";
import { TransactionFilters } from "../hooks/useTransactionFilters";

const ALL_SIDES: TransactionSide[] = ["BUY", "SELL", "DEPOSIT", "WITHDRAW", "INCOME", "FEE"];

const SIDE_ICONS: Record<TransactionSide, string> = {
   BUY: "↗",
   SELL: "↙",
   DEPOSIT: "↓",
   WITHDRAW: "↑",
   INCOME: "$",
   FEE: "%",
};

type FiltersModalProps = {
   portfolios: PortfolioList;
   filters: TransactionFilters;
   onApply: (filters: TransactionFilters) => void;
   onClear: () => void;
   onClose: () => void;
};

const FiltersModal: React.FC<FiltersModalProps> = ({ portfolios, filters, onApply, onClear, onClose }) => {
   // Local draft state — only commits to URL on Apply
   const [draft, setDraft] = useState<TransactionFilters>(filters);

   // Sync draft when URL filters change externally (e.g. back/forward nav)
   useEffect(() => {
      setDraft(filters);
   }, [filters]);

   const togglePortfolio = (id: string) => {
      setDraft((prev) => {
         const next = new Set(prev.portfolios);
         next.has(id) ? next.delete(id) : next.add(id);
         return { ...prev, portfolios: next };
      });
   };

   const toggleSide = (side: TransactionSide) => {
      setDraft((prev) => {
         const next = new Set(prev.sides);
         next.has(side) ? next.delete(side) : next.add(side);
         return { ...prev, sides: next };
      });
   };

   const handleClear = () => {
      setDraft({ portfolios: new Set(), sides: new Set() });
      onClear();
      onClose();
   };

   const draftCount = draft.portfolios.size + draft.sides.size;

   const chipCls = (active: boolean) =>
      `rounded-[20px] text-xs font-medium cursor-pointer transition-all duration-150 px-2.5 py-1 border ${
         active
            ? "bg-primary/10 border-primary text-primary"
            : "bg-muted border-border text-muted-foreground hover:text-foreground"
      }`;

   return (
      <div className="flex flex-col gap-4 p-5 w-[260px] font-sans">
         {/* Header */}
         <div className="flex items-center justify-between pb-3 border-b border-border">
            <span className="text-sm font-medium tracking-widest uppercase text-foreground">Filters</span>
            {draftCount > 0 && (
               <span className="flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold bg-primary text-primary-foreground">
                  {draftCount}
               </span>
            )}
         </div>

         {/* Portfolios */}
         <div className="flex flex-col gap-2">
            <span className="text-[10px] font-medium tracking-widest uppercase text-muted-foreground/60">
               Portfolios
            </span>
            <div className="flex flex-wrap gap-1.5">
               {portfolios.map((p) => (
                  <button
                     type="button"
                     key={p.id}
                     onClick={() => togglePortfolio(p.id)}
                     className={chipCls(draft.portfolios.has(p.id))}
                  >
                     {p.name}
                  </button>
               ))}
            </div>
         </div>

         {/* Sides */}
         <div className="flex flex-col gap-2">
            <span className="text-[10px] font-medium tracking-widest uppercase text-muted-foreground/60">
               Transaction side
            </span>
            <div className="flex flex-wrap gap-1.5">
               {ALL_SIDES.map((side) => (
                  <button
                     type="button"
                     key={side}
                     onClick={() => toggleSide(side)}
                     className={chipCls(draft.sides.has(side))}
                  >
                     {SIDE_ICONS[side]} {side}
                  </button>
               ))}
            </div>
         </div>

         {/* Footer */}
         <div className="flex items-center justify-between pt-3 border-t border-border">
            <button
               onClick={handleClear}
               className="text-[11px] tracking-wide bg-transparent border-none cursor-pointer transition-colors text-muted-foreground/60 hover:text-muted-foreground"
            >
               Clear all
            </button>
            <button
               onClick={() => onApply(draft)}
               className="text-xs font-medium px-3.5 py-1.5 rounded-md transition-opacity bg-primary text-primary-foreground border-none cursor-pointer hover:opacity-85"
            >
               Apply →
            </button>
         </div>
      </div>
   );
};

export default FiltersModal;
