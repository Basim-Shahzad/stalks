import React, { useMemo } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useTransactions } from "../hooks/useTransactions";
import type { TradeTransaction } from "../types";

const COLORS = ["#4F46E5", "#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE", "#E0E7FF"];

type ChartData = {
   name: string;
   value: number;
};

const formatPKR = (value: number) =>
   new Intl.NumberFormat("en-PK", {
      style: "currency",
      currency: "PKR",
      maximumFractionDigits: 0,
   }).format(value);

/**
 * 🎯 TOOLTIP DESCRIPTIONS (CLEAR HUMAN LANGUAGE)
 */
const STAT_INFO: Record<string, string> = {
   transactions: "Total number of buy/sell records in your portfolio.",
   activeSectors: "Number of unique sectors your investments are spread across.",
   totalBuy: "Total money deployed into buying stocks.",
   totalSell: "Total money received from selling stocks.",
   avgTrade: "Average value of each transaction in your portfolio.",
   totalCosts: "Total fees including commission, taxes, and charges.",
   netValue: "Total current value of all your holdings combined.",
   netFlow: "Difference between selling and buying activity (cash pressure indicator).",
};

const Portfolio = () => {
   const { transactions } = useTransactions();

   const safeTransactions: TradeTransaction[] = useMemo(() => transactions ?? [], [transactions]);

   /**
    * 🔥 SINGLE PASS CALCULATION ENGINE
    */
   const stats = useMemo(() => {
      let totalValue = 0;
      let totalBuyValue = 0;
      let totalSellValue = 0;

      let totalCommission = 0;
      let totalTaxes = 0;
      let totalCharges = 0;

      const sectorMap: Record<string, number> = {};
      const stockMap: Record<string, number> = {};

      for (const t of safeTransactions) {
         const value = t.total_amount ?? 0;
         totalValue += value;

         const isBuy = (t.buy ?? 0) > (t.sell ?? 0);
         const isSell = (t.sell ?? 0) > (t.buy ?? 0);

         if (isBuy) totalBuyValue += value;
         if (isSell) totalSellValue += value;

         totalCommission += t.commission ?? 0;
         totalTaxes += t.taxes ?? 0;
         totalCharges += t.charges ?? 0;

         const sector = t.sector ?? "Unknown";
         sectorMap[sector] = (sectorMap[sector] || 0) + value;

         const symbol = t.symbol ?? "Unknown";
         stockMap[symbol] = (stockMap[symbol] || 0) + value;
      }

      const sectorData: ChartData[] = Object.entries(sectorMap).map(([name, value]) => ({ name, value }));

      const topSectors = sectorData.sort((a, b) => b.value - a.value).slice(0, 4);

      const mostActiveStock = Object.entries(stockMap).sort((a, b) => b[1] - a[1])[0]?.[0] ?? "N/A";

      const avgTransaction = safeTransactions.length ? totalValue / safeTransactions.length : 0;

      const totalCosts = totalCommission + totalTaxes + totalCharges;

      const netFlow = totalSellValue - totalBuyValue;

      return {
         totalValue,
         totalBuyValue,
         totalSellValue,
         avgTransaction,
         totalCosts,
         netFlow,
         sectorData,
         topSectors,
         mostActiveStock,
      };
   }, [safeTransactions]);

   const transactionCount = safeTransactions.length;
   const activeSectorsCount = stats.sectorData.length;

   const marketBias = stats.netFlow >= 0 ? "Selling Pressure Dominant" : "Buying Pressure Dominant";

   return (
      <div className="p-8 bg-slate-50 min-h-screen">
         <div className="flex flex-col md:flex-row gap-8 items-start">
            {/* PIE CHART */}
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm w-full md:w-[480px] h-[480px] flex flex-col">
               <h3 className="text-slate-800 font-bold text-lg mb-4">Sector Allocation</h3>
               <SectorPieChart data={stats.sectorData} />
            </div>

            {/* SUMMARY */}
            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex-1 w-full space-y-6">
               {/* TOTAL VALUE */}
               <div>
                  <h2 className="text-slate-500 text-sm font-bold uppercase tracking-widest mb-1">Portfolio Value</h2>
                  <div className="text-4xl font-black text-slate-900">{formatPKR(stats.totalValue)}</div>
               </div>

               {/* METRICS */}
               <div className="grid grid-cols-2 gap-4">
                  <StatCard label="Transactions" value={transactionCount} info={STAT_INFO.transactions} />

                  <StatCard label="Active Sectors" value={activeSectorsCount} info={STAT_INFO.activeSectors} />

                  <StatCard label="Total Buy" value={formatPKR(stats.totalBuyValue)} info={STAT_INFO.totalBuy} />

                  <StatCard label="Total Sell" value={formatPKR(stats.totalSellValue)} info={STAT_INFO.totalSell} />

                  <StatCard label="Avg Trade" value={formatPKR(stats.avgTransaction)} info={STAT_INFO.avgTrade} />

                  <StatCard label="Total Costs" value={formatPKR(stats.totalCosts)} info={STAT_INFO.totalCosts} />
               </div>

               {/* INSIGHTS */}
               <div className="p-4 rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                  <div className="text-xs text-slate-500 font-semibold">Insights</div>

                  <div className="text-sm text-slate-700">
                     📊 Most Active Stock: <span className="font-bold text-indigo-600">{stats.mostActiveStock}</span>
                  </div>

                  <div className="text-sm text-slate-700">
                     ⚖️ Market Flow: <span className="font-bold text-indigo-600">{marketBias}</span>
                  </div>

                  <div className="text-sm text-slate-700">
                     💰 Net Flow: <span className="font-bold text-indigo-600">{formatPKR(stats.netFlow)}</span>
                  </div>
               </div>

               {/* TOP SECTORS */}
               <div className="space-y-3 pt-4 border-t border-slate-100">
                  {stats.topSectors.map((sector, i) => (
                     <div key={sector.name} className="flex justify-between items-center text-sm">
                        <div className="flex items-center gap-2">
                           <div
                              className="w-2 h-2 rounded-full"
                              style={{
                                 backgroundColor: COLORS[i % COLORS.length],
                              }}
                           />
                           <span className="text-slate-600 font-medium">{sector.name}</span>
                        </div>

                        <span className="text-slate-900 font-semibold">{formatPKR(sector.value)}</span>
                     </div>
                  ))}
               </div>
            </div>
         </div>
      </div>
   );
};

/**
 * 🎯 HOVERABLE STAT CARD
 */
const StatCard = ({ label, value, info }: { label: string; value: string | number; info: string }) => {
   return (
      <div className="relative group p-4 rounded-xl bg-slate-50 border border-slate-100">
         <div className="text-slate-500 text-xs font-semibold mb-1">{label}</div>

         <div className="text-2xl font-bold text-indigo-600">{value}</div>

         {/* Tooltip */}
         <div className="absolute z-10 left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-56">
            <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-lg">{info}</div>
         </div>
      </div>
   );
};

/**
 * PIE CHART
 */
const SectorPieChart = ({ data }: { data: ChartData[] }) => {
   return (
      <ResponsiveContainer width="100%" height="100%">
         <PieChart>
            <Pie
               data={data}
               dataKey="value"
               nameKey="name"
               outerRadius={140}
               innerRadius={100}
               paddingAngle={5}
               stroke="none">
               {data.map((_, index) => (
                  <Cell key={index} fill={COLORS[index % COLORS.length]} />
               ))}
            </Pie>

            <Tooltip
               formatter={(value) => formatPKR(Number(value ?? 0))}
               contentStyle={{
                  background: "#fff",
                  border: "1px solid #E2E8F0",
                  borderRadius: "12px",
                  padding: "12px",
               }}
            />
         </PieChart>
      </ResponsiveContainer>
   );
};

export default Portfolio;
