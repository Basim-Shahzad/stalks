"use client";

import { useMemo, useState } from "react";
import type { Transaction } from "@/features/transactions/types";
import { Input } from "@/components/ui/input";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import { Checkbox } from "@/components/ui/checkbox";
import { Menu, Check } from "lucide-react";
import { formatPKRFull } from "../../utils";

const StockHoldings: React.FC<{ transactions: Transaction[] }> = ({ transactions }) => {
   const [searchQuery, setSearchQuery] = useState("");
   const [sortKey, setSortKey] = useState<"amount" | "portfolio" | "shares" | "avgBuyPrice" | "minimumBuy">("amount");
   const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
   const [visibleColumns, setVisibleColumns] = useState<string[]>([
      "symbol",
      "company",
      "sector",
      "shares",
      "avgBuyPrice",
      "minimumBuy",
      "amount",
      "portfolio",
   ]);

   const { stockRows, totalAmount, sharesTotal } = useMemo(() => {
      const map = new Map<
         string,
         {
            company: string;
            symbol: string;
            sector: string;
            shares: number;
            amount: number;
            minimumBuy: number;
            totalBuyCost: number;
            totalBuyShares: number;
         }
      >();
      (transactions ?? []).forEach((t) => {
         const key = t.symbol;
         const existing = map.get(key);
         const isBuy = t.side === "BUY";
         const sharesDelta = isBuy ? Number(t.quantity) : -Number(t.quantity);
         const amountDelta = Number(t.totalAmount) || 0;
         const rate = Number(t.rate) || 0;
         if (existing) {
            existing.shares += sharesDelta;
            existing.amount += amountDelta;
            if (isBuy) {
               if (rate > 0 && rate < existing.minimumBuy) existing.minimumBuy = rate;
               existing.totalBuyCost += amountDelta;
               existing.totalBuyShares += Number(t.quantity);
            }
         } else {
            map.set(key, {
               symbol: t.symbol,
               company: t.company,
               sector: t.sector || "Unknown",
               shares: sharesDelta,
               amount: amountDelta,
               minimumBuy: isBuy && rate > 0 ? rate : Infinity,
               totalBuyCost: isBuy ? amountDelta : 0,
               totalBuyShares: isBuy ? Number(t.quantity) : 0,
            });
         }
      });
      const total = Array.from(map.values()).reduce((s, r) => s + r.amount, 0);
      const sharesTotal = Array.from(map.values()).reduce((s, r) => s + r.shares, 0);
      return {
         stockRows: Array.from(map.values()).map((r) => ({
            ...r,
            portfolio: total > 0 ? (r.amount / total) * 100 : 0,
            minimumBuy: r.minimumBuy === Infinity ? 0 : r.minimumBuy,
            avgBuyPrice: r.totalBuyShares > 0 ? r.totalBuyCost / r.totalBuyShares : 0,
         })),
         totalAmount: total,
         sharesTotal: sharesTotal,
      };
   }, [transactions]);

   const filteredAndSorted = useMemo(() => {
      return stockRows
         .filter(
            (row) =>
               row.symbol.toLowerCase().includes(searchQuery.toLowerCase()) ||
               row.company.toLowerCase().includes(searchQuery.toLowerCase()),
         )
         .sort((a, b) => {
            const diff = a[sortKey] - b[sortKey];
            return sortDir === "desc" ? -diff : diff;
         });
   }, [stockRows, searchQuery, sortKey, sortDir]);

   const isVisible = (col: string) => visibleColumns.includes(col);

   const handleSort = (key: "amount" | "portfolio" | "shares" | "avgBuyPrice" | "minimumBuy") => {
      if (sortKey === key) {
         setSortDir((d) => (d === "desc" ? "asc" : "desc"));
      } else {
         setSortKey(key);
         setSortDir("desc");
      }
   };

   const ALL_COLUMNS = ["symbol", "company", "sector", "shares", "avgBuyPrice", "minimumBuy", "amount", "portfolio"];
   const COLUMN_LABELS: Record<string, string> = {
      symbol: "Symbol",
      company: "Company",
      sector: "Sector",
      shares: "Shares",
      avgBuyPrice: "Avg Buy Price",
      minimumBuy: "Min Buy",
      amount: "Amount",
      portfolio: "% Portfolio",
   };

   return (
      <div className="rounded-2xl shadow-sm overflow-hidden border border-border">
         <div className="px-5 py-4 border-b border-border flex items-center justify-between gap-4">
            <div className="flex items-center gap-4">
               <h2 className="text-sm font-bold tracking-tight">Stock-Level Summary</h2>
            </div>

            <div className="flex items-center">
               <Input
                  className="w-64 bg-primary/10 focus-visible:ring-ring/30 text-foreground placeholder:text-muted-foreground"
                  placeholder="Search..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
               />

               <Popover>
                  <PopoverTrigger render={<button type="button" className="ml-2" />}>
                     <Menu className="cursor-pointer text-muted-foreground" />
                  </PopoverTrigger>
                  <PopoverContent align="end" className="p-4 bg-background border border-border w-auto">
                     <div className="flex flex-col gap-1 w-40">
                        <p className="text-xs font-bold text-foreground uppercase opacity-50">Columns</p>
                        <div className="flex flex-col gap-2 mt-1">
                           {ALL_COLUMNS.map((col) => (
                              <label key={col} className="flex items-center justify-between gap-2 w-full text-xs text-foreground cursor-pointer">
                                 <span className="flex items-center gap-2">
                                    <Checkbox
                                       checked={visibleColumns.includes(col)}
                                       onCheckedChange={(checked) =>
                                          setVisibleColumns((prev) =>
                                             checked ? [...prev, col] : prev.filter((c) => c !== col),
                                          )
                                       }
                                    />
                                    {COLUMN_LABELS[col]}
                                 </span>
                                 {visibleColumns.includes(col) && <Check className="text-primary" size={12} />}
                              </label>
                           ))}
                        </div>
                     </div>
                  </PopoverContent>
               </Popover>
            </div>
         </div>

         <div className="overflow-x-auto">
            <table className="w-full text-sm border-collapse">
               <thead>
                  <tr className="border-b border-border">
                     {isVisible("symbol") && (
                        <th className="text-left px-5 py-3 text-xs font-semibold uppercase">Symbol</th>
                     )}
                     {isVisible("company") && (
                        <th className="text-left px-3 py-3 text-xs font-semibold uppercase">Company</th>
                     )}
                     {isVisible("sector") && (
                        <th className="text-left px-3 py-3 text-xs font-semibold uppercase">Sector</th>
                     )}
                     {isVisible("shares") && (
                        <th
                           className="text-right px-3 py-3 text-xs font-semibold uppercase cursor-pointer"
                           onClick={() => handleSort("shares")}>
                           Shares
                        </th>
                     )}
                     {isVisible("avgBuyPrice") && (
                        <th
                           className="text-right px-3 py-3 text-xs font-semibold uppercase cursor-pointer"
                           onClick={() => handleSort("avgBuyPrice")}>
                           Avg Buy
                        </th>
                     )}
                     {isVisible("minimumBuy") && (
                        <th
                           className="text-right px-3 py-3 text-xs font-semibold uppercase cursor-pointer"
                           onClick={() => handleSort("minimumBuy")}>
                           Min Buy
                        </th>
                     )}
                     {isVisible("amount") && (
                        <th
                           className="text-right px-3 py-3 text-xs font-semibold uppercase cursor-pointer"
                           onClick={() => handleSort("amount")}>
                           Amount
                        </th>
                     )}
                     {isVisible("portfolio") && (
                        <th
                           className="text-right px-5 py-3 text-xs font-semibold uppercase cursor-pointer"
                           onClick={() => handleSort("portfolio")}>
                           % Portfolio
                        </th>
                     )}
                  </tr>
               </thead>
               <tbody>
                  {filteredAndSorted.map((row) => (
                     <tr key={row.symbol} className="border-b border-border/40 hover:bg-accent/40 transition-colors">
                        {isVisible("symbol") && <td className="px-5 py-2.5 font-bold">{row.symbol}</td>}
                        {isVisible("company") && <td className="px-3 py-2.5">{row.company}</td>}
                        {isVisible("sector") && <td className="px-3 py-2.5 text-xs opacity-60">{row.sector}</td>}
                        {isVisible("shares") && (
                           <td className="px-3 py-2.5 text-right tabular-nums">{row.shares.toLocaleString()}</td>
                        )}
                        {isVisible("avgBuyPrice") && (
                           <td className="px-3 py-2.5 text-right tabular-nums">
                              {formatPKRFull(row.avgBuyPrice)}
                           </td>
                        )}
                        {isVisible("minimumBuy") && (
                           <td className="px-3 py-2.5 text-right tabular-nums">
                              {formatPKRFull(row.minimumBuy)}
                           </td>
                        )}
                        {isVisible("amount") && (
                           <td className="px-3 py-2.5 text-right font-medium tabular-nums">
                              {formatPKRFull(row.amount)}
                           </td>
                        )}
                        {isVisible("portfolio") && (
                           <td className="px-5 py-2.5 text-right font-semibold tabular-nums">
                              {row.portfolio.toFixed(2)}%
                           </td>
                        )}
                     </tr>
                  ))}
               </tbody>
            </table>
         </div>

         <div className="px-5 py-3 border-t border-border flex justify-end items-center gap-6 bg-muted/40">
            <span className="text-xs font-bold uppercase tracking-wider opacity-60">Total</span>
            <span className="pr-10 text-sm font-bold tabular-nums">{formatPKRFull(totalAmount)}</span>
            <span className="text-sm font-bold">100.00%</span>
         </div>
      </div>
   );
};

export default StockHoldings;