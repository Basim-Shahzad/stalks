import { useMemo, useState } from "react";
import { useTransactions } from "../../hooks/useTransactions";
import type { TradeTransaction } from "../../types";

function formatPKRFull(value: number): string {
   return value.toLocaleString("en-PK", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

const StockLevelSummary = () => {
   const { transactions } = useTransactions();
   const safeTransactions: TradeTransaction[] = useMemo(() => transactions ?? [], [transactions]);

   const [sortKey, setSortKey] = useState<"amount" | "portfolio" | "shares" | null>("amount");
   const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");

   const { stockRows, totalAmount } = useMemo(() => {
      const map = new Map<
         string,
         { company: string; symbol: string; sector: string; shares: number; amount: number }
      >();

      for (const t of safeTransactions) {
         const key = t.symbol;
         const existing = map.get(key);
         const isBuy = (t.buy ?? 0) > 0;
         const sharesDelta = isBuy ? (t.buy ?? 0) : -(t.sell ?? 0);
         if (existing) {
            existing.shares += sharesDelta;
            existing.amount += t.total_amount ?? 0;
         } else {
            map.set(key, {
               symbol: t.symbol,
               company: t.company,
               sector: t.sector ?? "Unknown",
               shares: sharesDelta,
               amount: t.total_amount ?? 0,
            });
         }
      }

      const total = Array.from(map.values()).reduce((s, r) => s + r.amount, 0);
      const rows = Array.from(map.values()).map((r) => ({
         ...r,
         portfolio: total > 0 ? (r.amount / total) * 100 : 0,
      }));

      return { stockRows: rows, totalAmount: total };
   }, [safeTransactions]);

   const sorted = useMemo(() => {
      if (!sortKey) return stockRows;
      return [...stockRows].sort((a, b) => {
         const diff = a[sortKey] - b[sortKey];
         return sortDir === "desc" ? -diff : diff;
      });
   }, [stockRows, sortKey, sortDir]);

   function handleSort(key: "amount" | "portfolio" | "shares") {
      if (sortKey === key) {
         setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
         setSortKey(key);
         setSortDir("desc");
      }
   }

   function SortIcon({ col }: { col: "amount" | "portfolio" | "shares" }) {
      if (sortKey !== col) return <span className="text-slate-300 ml-1">↕</span>;
      return <span className="text-slate-700 ml-1">{sortDir === "desc" ? "↓" : "↑"}</span>;
   }

   return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-0 overflow-hidden">
         {/* Header */}
         <div className="px-5 py-4 border-b border-slate-100 flex items-center gap-2">
            <h2 className="text-sm font-semibold text-slate-800 tracking-tight">Stock-Level Summary</h2>
            <span className="text-xs text-slate-400 font-medium">({stockRows.length} stocks)</span>
         </div>

         {/* Table */}
         <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
               <thead>
                  <tr className="bg-slate-50 border-b border-slate-100">
                     <th className="text-left px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide w-20">
                        Symbol
                     </th>
                     <th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                        Company
                     </th>
                     <th className="text-left px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                        Sector
                     </th>
                     <th
                        className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer select-none hover:text-slate-700 whitespace-nowrap"
                        onClick={() => handleSort("shares")}>
                        Shares <SortIcon col="shares" />
                     </th>
                     <th
                        className="text-right px-3 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer select-none hover:text-slate-700 whitespace-nowrap"
                        onClick={() => handleSort("amount")}>
                        Amount (PKR) <SortIcon col="amount" />
                     </th>
                     <th
                        className="text-right px-5 py-3 text-xs font-semibold text-slate-500 uppercase tracking-wide cursor-pointer select-none hover:text-slate-700 whitespace-nowrap"
                        onClick={() => handleSort("portfolio")}>
                        % Portfolio <SortIcon col="portfolio" />
                     </th>
                  </tr>
               </thead>
               <tbody>
                  {sorted.map((row, i) => (
                     <tr
                        key={row.symbol}
                        className={`border-b border-slate-50 hover:bg-slate-50 transition-colors ${
                           i % 2 === 0 ? "bg-white" : "bg-slate-50/40"
                        }`}>
                        <td className="px-5 py-2.5 font-bold text-slate-800 whitespace-nowrap">{row.symbol}</td>
                        <td className="px-3 py-2.5 text-slate-700 whitespace-nowrap">{row.company}</td>
                        <td className="px-3 py-2.5 text-slate-400 text-xs whitespace-nowrap">{row.sector}</td>
                        <td className="px-3 py-2.5 text-right text-slate-700 tabular-nums">
                           {row.shares.toLocaleString()}
                        </td>
                        <td className="px-3 py-2.5 text-right font-medium text-slate-800 tabular-nums whitespace-nowrap">
                           {formatPKRFull(row.amount)}
                        </td>
                        <td className="px-5 py-2.5 text-right font-semibold text-slate-800 tabular-nums whitespace-nowrap">
                           {row.portfolio.toFixed(2)}%
                        </td>
                     </tr>
                  ))}
               </tbody>
            </table>
         </div>

         {/* Footer total */}
         <div className="px-5 py-3 bg-slate-50 border-t border-slate-100 flex justify-end items-center gap-6">
            <span className="text-xs text-slate-500 font-medium uppercase tracking-wide">Total</span>
            <span className="text-sm font-bold text-slate-800 tabular-nums">PKR {formatPKRFull(totalAmount)}</span>
            <span className="text-sm font-bold text-slate-800">100.00%</span>
         </div>
      </div>
   );
};

export default StockLevelSummary;
