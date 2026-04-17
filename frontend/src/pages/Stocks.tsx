import React, { useMemo } from "react";
import type { StockByApi } from "../types";
import { useStocks } from "../hooks/useStocks";
import { useTransactions } from "../hooks/useTransactions";

interface StockCardProps {
   stock: StockByApi;
}

const StockCard = ({ stock }: StockCardProps) => {
   const { isLoading, transactions } = useTransactions();

   const currentStockTransactions = useMemo(() => {
      return transactions?.filter((t) => t.symbol === stock.symbol) || [];
   }, [transactions, stock.symbol]);

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

   if (isLoading || !transactions) return null;

   // Helper to calculate position on the line
   const getPos = (val: number) => {
      const range = stats.max - stats.min;
      // If only one buy price exists (range 0), center everything at 50%
      if (range === 0) return 50;
      return Math.min(Math.max(((val - stats.min) / range) * 100, 0), 100);
   };

   return (
      <div className="group cursor-pointer p-4 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all duration-200">
         {/* Header Section */}
         <div className="flex justify-between items-start mb-2">
            <div>
               <h3 className="text-lg font-black text-slate-900 uppercase tracking-tight group-hover:text-indigo-600 transition-colors">
                  {stock.symbol}
               </h3>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">{stats.net} IN PF</span>
            </div>
            <div className="text-right">
               <p className="text-xl font-bold text-slate-900">{stock.price.toLocaleString()}</p>
               <p
                  className={`text-xs font-bold flex items-center justify-end gap-1 ${stock.change >= 0 ? "text-emerald-500" : "text-rose-500"}`}>
                  {stock.change >= 0 ? "▲" : "▼"} {Math.abs(stock.change).toFixed(2)}
                  <span className="font-medium text-px]">
                     ({Math.abs(stock.changePercent * 100).toFixed(2)}%)
                  </span>
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
                  <div className="absolute top-1/2 -translate-y-1/2 z-10" style={{ left: `${getPos(stock.price)}%` }}>
                     <div
                        className={`w-3 h-3 rounded-full border-2 border-white shadow-md ${stock.change >= 0 ? "bg-emerald-500" : "bg-rose-500"}`}
                     />
                     <div className="absolute -top-8 left-1/2 -translate-x-1/2 flex flex-col items-center">
                        <span className="text-[13px] font-bold text-slate-900 leading-none">{stock.price}</span>
                        <span
                           className={`text-[9px] font-black uppercase ${stock.change >= 0 ? "text-emerald-600" : "text-rose-600"}`}>
                           CURRENT
                        </span>
                     </div>
                  </div>
               </div>
            ) : (
               <div className="h-1.5 w-full bg-slate-100 rounded-full flex items-center justify-center">
                  <span className="text-[10px] text-slate-300 font-bold uppercase tracking-widest">No Buy History</span>
               </div>
            )}
         </div>

         {/* Footer Info */}
         <div className="grid grid-cols-2 gap-3 pt-4 border-t border-slate-50">
            <div>
               <p className="text-[10px] font-semibold text-slate-400 uppercase">Volume</p>
               <p className="text-sm font-medium text-slate-700">{(stock.volume / 1000000).toFixed(2)}M</p>
            </div>
            <div className="text-right">
               <p className="text-[10px] font-semibold text-slate-400 uppercase">Trades</p>
               <p className="text-sm font-medium text-slate-700">{stock.trades.toLocaleString()}</p>
            </div>
         </div>
      </div>
   );
};

const Stocks = () => {
   // const { data, isLoading, error } = useStocks()

   const data = [
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 0.08,
         changePercent: 0.00521,
         high: 15.79,
         low: 15.3,
         market: "REG",
         price: 15.44,
         st: "SUS",
         symbol: "AHCL",
         timestamp: 1776426586,
         trades: 3552,
         value: 276036153.06,
         volume: 17782223,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 1.76,
         changePercent: 0.02172,
         high: 84.25,
         low: 81.5,
         market: "REG",
         price: 82.78,
         st: "SUS",
         symbol: "AICL",
         timestamp: 1776426581,
         trades: 588,
         value: 37379758.33,
         volume: 449443,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 3.69,
         changePercent: 0.03885,
         high: 99.9,
         low: 95.1,
         market: "REG",
         price: 98.67,
         st: "SUS",
         symbol: "AKBL",
         timestamp: 1776426583,
         trades: 2096,
         value: 395811922.02,
         volume: 4018774,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 0.19,
         changePercent: 0.01908,
         high: 10.35,
         low: 9.5,
         market: "REG",
         price: 10.15,
         st: "SUS",
         symbol: "ANL",
         timestamp: 1776426339,
         trades: 321,
         value: 4358829.24,
         volume: 429657,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 32.93,
         changePercent: 0.019,
         high: 1770,
         low: 1720,
         market: "REG",
         price: 1766.52,
         st: "SUS",
         symbol: "ATLH",
         timestamp: 1776425933,
         trades: 289,
         value: 16335963.67,
         volume: 9329,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 7.4,
         changePercent: 0.00853,
         high: 879.88,
         low: 867,
         market: "REG",
         price: 875.15,
         st: "SUS",
         symbol: "ATRL",
         timestamp: 1776426456,
         trades: 2281,
         value: 609061506.83,
         volume: 697551,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 3.93,
         changePercent: 0.0322,
         high: 126.48,
         low: 121.51,
         market: "REG",
         price: 125.34,
         st: "SUS",
         symbol: "BAFL",
         timestamp: 1776409199,
         trades: 1060,
         value: 196892596.27,
         volume: 1579607,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 1.47,
         changePercent: 0.05145,
         high: 30.48,
         low: 28.49,
         market: "REG",
         price: 30.04,
         st: "SUS",
         symbol: "BIPL",
         timestamp: 1776426583,
         trades: 2002,
         value: 107986251.21,
         volume: 3639845,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 3.07,
         changePercent: 0.09045,
         high: 37.33,
         low: 33.94,
         market: "REG",
         price: 37.01,
         st: "SUS",
         symbol: "BOP",
         timestamp: 1776426597,
         trades: 32707,
         value: 5505244494.79,
         volume: 153717760,
      },
      {
         ask: 0,
         askVol: 0,
         bid: 0,
         bidVol: 0,
         change: 0.26,
         changePercent: 0.03476,
         high: 7.84,
         low: 7.5,
         market: "REG",
         price: 7.74,
         st: "SUS",
         symbol: "CNERGY",
         timestamp: 1776426444,
         trades: 4522,
         value: 260058437.67,
         volume: 33693931,
      },
   ];

   if (!data) {
      return "LOADING";
   }

   return (
      <div className="p-8 bg-slate-50">
         <div className="">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5 gap-1.5">
               {data!.map((stock) => (
                  <StockCard stock={stock} key={stock.symbol} />
               ))}
            </div>
         </div>
      </div>
   );
};

export default Stocks;
