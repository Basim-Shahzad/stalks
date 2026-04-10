import React from "react";
import type { StockByApi } from "../types";
import { useStocks } from "../hooks/useStocks";

interface StockCardProps {
   stock: StockByApi;
}

const StockCard = ({ stock }: StockCardProps) => {
   const isPositive = stock.change >= 0;

   return (
      <div className="group p-5 bg-white border border-slate-200 rounded-xl hover:border-indigo-300 hover:shadow-md transition-all duration-200">
         <div className="flex justify-between items-start mb-4">
            <div>
               <h3 className="text-lg font-black text-slate-900 tracking-tight group-hover:text-indigo-600 transition-colors">
                  {stock.symbol}
               </h3>
               <span className="text-[10px] font-bold text-slate-400 uppercase tracking-widest">
                  {stock.market} • {stock.st}
               </span>
            </div>
            <div className="text-right">
               <p className="text-xl font-bold text-slate-900">{stock.price.toLocaleString()}</p>
               <p
                  className={`text-xs font-bold flex items-center justify-end gap-1 ${isPositive ? "text-emerald-500" : "text-rose-500"}`}>
                  {isPositive ? "▲" : "▼"}
                  {Math.abs(stock.change).toFixed(2)} ({Math.abs(stock.changePercent * 100).toFixed(2)}%)
               </p>
            </div>
         </div>

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
   const { data, isLoading, error } = useStocks()

   return (
      <div className="p-8 bg-slate-50 min-h-screen">
         <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
               {data.map((stock) => (
                  <StockCard stock={stock} key={stock.symbol} />
               ))}
            </div>
         </div>
      </div>
   );
};

export default Stocks;
