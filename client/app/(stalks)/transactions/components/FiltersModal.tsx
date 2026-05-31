"use client";

import React, { useState, useEffect } from "react";
import { Chip } from "@heroui/react";
import { PortfolioList } from "@/types/portfolios.types";
import { TransactionSide } from "@/types/transactions.types";
import { TransactionFilters } from "@/lib/hooks/useTransactionFilters";

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

   const chipStyle = (active: boolean): React.CSSProperties => ({
      background: active ? "#001a0f" : "#161718",
      border: `0.5px solid ${active ? "#00ff87" : "#2e3033"}`,
      color: active ? "#00ff87" : "#888888",
      borderRadius: "20px",
      fontSize: "12px",
      fontWeight: 500,
      cursor: "pointer",
      transition: "all 0.15s ease",
   });

   return (
      <div className="flex flex-col gap-4 p-5 w-[260px]" style={{ fontFamily: "var(--font-sans, system-ui)" }}>
         {/* Header */}
         <div className="flex items-center justify-between pb-3" style={{ borderBottom: "0.5px solid #2e3033" }}>
            <span className="text-sm font-medium tracking-widest uppercase" style={{ color: "#f5f5f5" }}>
               Filters
            </span>
            {draftCount > 0 && (
               <span
                  className="flex items-center justify-center w-4 h-4 rounded-full text-[9px] font-bold"
                  style={{ background: "#00ff87", color: "#070707" }}
               >
                  {draftCount}
               </span>
            )}
         </div>

         {/* Portfolios */}
         <div className="flex flex-col gap-2">
            <span className="text-[10px] font-medium tracking-widest uppercase" style={{ color: "#444444" }}>
               Portfolios
            </span>
            <div className="flex flex-wrap gap-1.5">
               {portfolios.map((p) => (
                  <Chip
                     key={p.id}
                     size="sm"
                     variant="soft"
                     onClick={() => togglePortfolio(p.id)}
                     style={chipStyle(draft.portfolios.has(p.id))}
                  >
                     {p.name}
                  </Chip>
               ))}
            </div>
         </div>

         {/* Sides */}
         <div className="flex flex-col gap-2">
            <span className="text-[10px] font-medium tracking-widest uppercase" style={{ color: "#444444" }}>
               Transaction side
            </span>
            <div className="flex flex-wrap gap-1.5">
               {ALL_SIDES.map((side) => (
                  <Chip
                     key={side}
                     size="sm"
                     variant="soft"
                     onClick={() => toggleSide(side)}
                     style={chipStyle(draft.sides.has(side))}
                  >
                     {SIDE_ICONS[side]} {side}
                  </Chip>
               ))}
            </div>
         </div>

         {/* Footer */}
         <div className="flex items-center justify-between pt-3" style={{ borderTop: "0.5px solid #2e3033" }}>
            <button
               onClick={handleClear}
               className="text-[11px] tracking-wide bg-transparent border-none cursor-pointer transition-colors"
               style={{ color: "#444444" }}
               onMouseEnter={(e) => (e.currentTarget.style.color = "#888888")}
               onMouseLeave={(e) => (e.currentTarget.style.color = "#444444")}
            >
               Clear all
            </button>
            <button
               onClick={() => onApply(draft)}
               className="text-xs font-medium px-3.5 py-1.5 rounded-md transition-opacity"
               style={{ background: "#00ff87", color: "#070707", border: "none", cursor: "pointer" }}
               onMouseEnter={(e) => (e.currentTarget.style.opacity = "0.85")}
               onMouseLeave={(e) => (e.currentTarget.style.opacity = "1")}
            >
               Apply →
            </button>
         </div>
      </div>
   );
};

export default FiltersModal;
