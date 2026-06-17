"use client";

import { useState, useRef, useEffect } from "react";
import { PortfolioHolding } from "@/types/portfolios.types";

type ColDef = {
   key: keyof PortfolioHolding;
   label: string;
   sticky?: boolean;
   defaultOn?: boolean;
   align?: "left" | "right";
};

const COLS: ColDef[] = [
   { key: "symbol", label: "Symbol", sticky: true, defaultOn: true, align: "left" },
   { key: "company", label: "Company", sticky: false, defaultOn: true, align: "left" },
   { key: "sector", label: "Sector", defaultOn: false, align: "left" },
   { key: "quantity", label: "Qty", defaultOn: true },
   { key: "avgCost", label: "Avg Cost", defaultOn: true },
   { key: "currentPrice", label: "Price", defaultOn: true },
   { key: "ldcp", label: "LDCP", defaultOn: false },
   { key: "dayChange", label: "Day Chg", defaultOn: true },
   { key: "dayChange_pct", label: "Day %", defaultOn: true },
   { key: "marketValue", label: "Mkt Value", defaultOn: true },
   { key: "totalInvested", label: "Invested", defaultOn: false },
   { key: "totalFees", label: "Fees", defaultOn: false },
   { key: "costBasis", label: "Cost Basis", defaultOn: false },
   { key: "unrealisedPnl", label: "Unreal P&L", defaultOn: true },
   { key: "unrealisedPnlPct", label: "Unreal %", defaultOn: true },
   { key: "realisedPnl", label: "Real P&L", defaultOn: false },
   { key: "totalPnl", label: "Total P&L", defaultOn: true },
];

const PNL_KEYS = new Set<keyof PortfolioHolding>([
   "dayChange",
   "dayChange_pct",
   "unrealisedPnl",
   "unrealisedPnlPct",
   "realisedPnl",
   "totalPnl",
]);

function pnlClass(value: string | undefined) {
   if (!value) return "text-[#a0a0a0]";
   if (value.startsWith("+")) return "text-[#00ff87]";
   if (value.startsWith("-")) return "text-red-500";
   return "text-green-500";
}

const Table = ({ holdings = [] }: { holdings: PortfolioHolding[] }) => {
   const initVisible = () => {
      const m: Record<string, boolean> = {};
      COLS.forEach((c) => (m[c.key] = c.defaultOn ?? true));
      return m;
   };

   const [visible, setVisible] = useState<Record<string, boolean>>(initVisible);
   const [panelOpen, setPanelOpen] = useState(false);
   const panelRef = useRef<HTMLDivElement>(null);

   const activeCols = COLS.filter((c) => visible[c.key]);

   const toggle = (key: string) => setVisible((prev) => ({ ...prev, [key]: !prev[key] }));

   useEffect(() => {
      const handler = (e: MouseEvent) => {
         if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
            setPanelOpen(false);
         }
      };
      document.addEventListener("mousedown", handler);
      return () => document.removeEventListener("mousedown", handler);
   }, []);

   return (
      <div className="bg-[#111213] rounded-xl border border-[#2e3033] overflow-hidden">
         {/* Toolbar */}
         <div className="flex items-center justify-between px-3.5 py-2.5 bg-[#0d0e0f] border-b border-[#2e3033] gap-2 flex-wrap">
            <div className="flex items-center gap-2">
               <span className="text-[10px] font-medium tracking-widest uppercase text-[#a0a0a0]">Holdings</span>
               <span className="text-[11px] font-medium px-2 py-0.5 rounded bg-[#00ff8720] text-[#00ff87] border border-[#00ff8740]">
                  {holdings.length} positions
               </span>
            </div>

            {/* Column toggle dropdown */}
            <div className="relative min-w-full" ref={panelRef}>
               <button
                  onClick={() => setPanelOpen((v) => !v)}
                  className="flex items-center gap-1.5 text-[12px] text-[#a0a0a0] bg-[#1c1d1f] border border-[#2e3033] px-2.5 py-1 rounded-md hover:border-[#00ff87] hover:text-white transition-colors cursor-pointer"
               >
                  <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                     <rect x="3" y="3" width="7" height="18" rx="1" />
                     <rect x="14" y="3" width="7" height="18" rx="1" />
                  </svg>
                  Columns
               </button>

               {panelOpen && (
                  <div className="absolute top-[calc(100%+6px)] right-0 z-50 bg-[#161718] border border-[#2e3033] rounded-xl p-2 shadow-2xl">
                     <p className="text-[10px] tracking-widest uppercase text-[#444] px-1.5 pb-2 mb-1.5 border-b border-[#2e3033]">
                        Show / hide columns
                     </p>
                     <div className="grid grid-cols-2 gap-0.5">
                        {COLS.map((col) => (
                           <label
                              key={col.key}
                              className="flex items-center gap-2 px-1.5 py-1.5 rounded-md hover:bg-[#1c1d1f] cursor-pointer"
                           >
                              <input
                                 type="checkbox"
                                 checked={!!visible[col.key]}
                                 disabled={col.sticky}
                                 onChange={() => toggle(col.key)}
                                 className="accent-[#00ff87] w-3 h-3 cursor-pointer shrink-0 disabled:opacity-40"
                              />
                              <span
                                 className={`text-[12px] select-none ${visible[col.key] ? "text-white" : "text-[#888]"}`}
                              >
                                 {col.label}
                              </span>
                           </label>
                        ))}
                     </div>
                  </div>
               )}
            </div>
         </div>

         {/* Table */}
         <div className="overflow-x-auto">
            <table className="w-full border-collapse text-[12px]">
               <thead>
                  <tr className="border-b border-[#2e3033]">
                     {activeCols.map((col) => (
                        <th
                           key={col.key}
                           className={`px-3 py-2.5 text-[10px] font-medium tracking-widest uppercase text-[#444] whitespace-nowrap ${
                              col.align === "left" ? "text-left" : "text-right"
                           }`}
                        >
                           {col.label}
                        </th>
                     ))}
                  </tr>
               </thead>
               <tbody>
                  {holdings.map((row, i) => (
                     <tr
                        key={i}
                        className="border-b border-[#1c1d1f] last:border-none hover:bg-[#161718] transition-colors"
                     >
                        {activeCols.map((col) => {
                           const val = row[col.key];
                           const isPnl = PNL_KEYS.has(col.key);
                           return (
                              <td
                                 key={col.key}
                                 className={`px-3 py-2.5 whitespace-nowrap ${
                                    col.align === "left" ? "text-left" : "text-right"
                                 } ${
                                    col.key === "symbol"
                                       ? "text-[#00ff87] font-medium tracking-wider"
                                       : col.key === "company"
                                         ? "text-[#888]"
                                         : isPnl
                                           ? pnlClass(val)
                                           : "text-[#a0a0a0]"
                                 }`}
                              >
                                 {col.key === "sector" ? (
                                    <span className="text-[10px] bg-[#1c1d1f] border border-[#2e3033] px-2 py-0.5 rounded text-[#888]">
                                       {val}
                                    </span>
                                 ) : (
                                    val
                                 )}
                              </td>
                           );
                        })}
                     </tr>
                  ))}
                  {holdings.length === 0 && (
                     <tr>
                        <td
                           colSpan={activeCols.length}
                           className="text-center py-12 text-[#444] text-[12px] tracking-wide"
                        >
                           No holdings found
                        </td>
                     </tr>
                  )}
               </tbody>
            </table>
         </div>
      </div>
   );
};

export default Table;