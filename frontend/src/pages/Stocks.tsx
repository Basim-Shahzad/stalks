import { useMemo, useState } from "react";
import type { StockByApi } from "../types";
import { useStocks } from "../hooks/useStocks";
import { useTransactions } from "../hooks/useTransactions";
import { Skeleton } from "@mantine/core";

interface StockCardProps {
   stock: StockByApi;
   isSkeleton?: boolean;
}

const StockCard = ({ stock, isSkeleton }: StockCardProps) => {
   const { isLoading: transLoading, transactions } = useTransactions();

   const currentStockTransactions = useMemo(() => {
      if (isSkeleton) return [];
      return transactions?.filter((t) => t.symbol === stock.symbol) || [];
   }, [transactions, stock.symbol, isSkeleton]);

   const stats = useMemo(() => {
      // 1. Separate Buys from everything else
      const buyTrades = currentStockTransactions.filter((t) => t.buy > 0);
      const net = currentStockTransactions.reduce((acc, t) => acc + (t.buy - t.sell), 0);

      // If no buys, return zeros and a flag so we can handle the UI
      if (buyTrades.length === 0) return { net, min: 0, max: 0, avg: 0, hasBuys: false };

      const totalBuyQty = buyTrades.reduce((acc, t) => acc + t.buy, 0);
      const totalBuyCost = buyTrades.reduce((acc, t) => acc + t.buy * t.rate, 0);
      const buyRates = buyTrades.map((t) => t.rate);

      return {
         net,
         min: Math.min(...buyRates),
         max: Math.max(...buyRates),
         avg: totalBuyCost / totalBuyQty,
         hasBuys: true,
      };
   }, [currentStockTransactions]);

   // Helper to calculate position on the line
   const getPos = (val: number) => {
      const range = stats.max - stats.min;
      // If only one buy price exists (range 0), center everything at 50%
      if (range === 0) return 50;
      return Math.min(Math.max(((val - stats.min) / range) * 100, 0), 100);
   };

   return (
      <Skeleton visible={isSkeleton || transLoading}>
         <div className="group cursor-pointer p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all duration-200">
            {/* Header Section */}
            <div className="flex justify-between items-start mb-2">
               <div>
                  <h3 className="text-lg font-black text-slate-900 uppercase tracking-tight group-hover:text-indigo-600 transition-colors">
                     {stock.symbol}
                  </h3>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                     {stats.net} IN PF
                  </span>
               </div>
               <div className="text-right">
                  <p className="text-xl font-bold text-slate-900">{stock.price?.toLocaleString() ?? "0.00"}</p>
                  <p
                     className={`text-xs font-bold flex items-center justify-end gap-1 ${(stock.change ?? 0) >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                     {(stock.change ?? 0) >= 0 ? "▲" : "▼"} {Math.abs(stock.change ?? 0).toFixed(2)}
                     <span className="font-medium text-px]">({Math.abs(stock.changePercent * 100).toFixed(2)}%)</span>
                  </p>
               </div>
            </div>

            {/* Number Line Visualizer */}
            <div className="py-10 px-2">
               {stats.hasBuys ? (
                  <div className="relative h-1.5 w-full bg-slate-200 rounded-full">
                     {/* MIN Label */}
                     <div className="flex flex-col absolute left-0 -bottom-9 items-start">
                        <span className="text-[13px] font-bold text-slate-900 leading-none">{stats.min}</span>
                        <span className="text-[9px] text-slate-400 font-black uppercase">MIN BUY</span>
                     </div>

                     {/* MAX Label */}
                     <div className="flex flex-col absolute right-0 -bottom-9 items-end">
                        <span className="text-[13px] font-bold text-slate-900 leading-none">{stats.max}</span>
                        <span className="text-[9px] text-slate-400 font-black uppercase">MAX BUY</span>
                     </div>

                     {/* AVG Marker */}
                     <div className="absolute top-1/2 -translate-y-1/2" style={{ left: `${getPos(stats.avg)}%` }}>
                        <div className="w-1 h-3 bg-amber-400 rounded-full mx-auto" />
                        <div className="absolute -bottom-7 left-1/2 -translate-x-1/2 flex flex-col items-center">
                           <span className="text-[13px] font-bold text-slate-700 leading-none">
                              {stats.avg.toFixed(1)}
                           </span>
                           <span className="text-[9px] font-black text-amber-600 uppercase">AVG</span>
                        </div>
                     </div>

                     {/* CURRENT Marker */}
                     <div
                        className="absolute top-1/2 -translate-y-1/2 z-10"
                        style={{ left: `${getPos(stock.price ?? 0)}%` }}>
                        <div
                           className={`w-3 h-3 rounded-full border-2 border-white shadow-md ${(stock.change ?? 0) >= 0 ? "bg-emerald-500" : "bg-rose-500"}`}
                        />
                        <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center">
                           <span className="text-[13px] font-bold text-slate-900 leading-none">{stock.price ?? 0}</span>
                           <span
                              className={`text-[9px] font-black uppercase ${(stock.change ?? 0) >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                              CURRENT
                           </span>
                        </div>
                     </div>
                  </div>
               ) : (
                  <div className="h-1.5 w-full bg-slate-100 rounded-full flex items-center justify-center">
                     <span className="text-[10px] text-slate-300 font-bold uppercase tracking-widest">
                        No Buy History
                     </span>
                  </div>
               )}
            </div>

            {/* Footer Info */}
            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-50">
               <div>
                  <p className="text-[10px] font-semibold text-slate-400 uppercase">Volume</p>
                  <p className="text-sm font-medium text-slate-700">{((stock.volume ?? 0) / 1000000).toFixed(2)}M</p>
               </div>
               <div className="text-right">
                  <p className="text-[10px] font-semibold text-slate-400 uppercase">Trades</p>
                  <p className="text-sm font-medium text-slate-700">{(stock.trades ?? 0).toLocaleString()}</p>
               </div>
            </div>
         </div>
      </Skeleton>
   );
};

const PAGE_SIZE = 10;

const Stocks = () => {
   const [page, setPage] = useState(1);
   const { data, isLoading } = useStocks(page, PAGE_SIZE);

   console.log(data)

   const displayData =
      isLoading || !data ? Array.from({ length: PAGE_SIZE }, (_, i) => ({ symbol: `skeleton-${i}` })) : data.stocks;

   return (
      <div className="p-8 bg-slate-50">
         <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-1.5">
            {displayData.map((stock) => (
               <StockCard stock={stock as any} key={stock.symbol} isSkeleton={isLoading || !data} />
            ))}
         </div>

         {data && data.total_pages > 1 && (
            <div className="flex items-center justify-center gap-2 mt-6">
               <button
                  onClick={() => setPage((p) => p - 1)}
                  disabled={!data.has_prev}
                  className="px-3 py-1.5 text-sm rounded-md border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100 transition-colors">
                  ← Prev
               </button>

               <span className="text-sm text-slate-500">
                  {page} / {data.total_pages}
               </span>

               <button
                  onClick={() => setPage((p) => p + 1)}
                  disabled={!data.has_next}
                  className="px-3 py-1.5 text-sm rounded-md border border-slate-200 bg-white disabled:opacity-40 hover:bg-slate-100 transition-colors">
                  Next →
               </button>
            </div>
         )}
      </div>
   );
};

export default Stocks;
