import React, { useMemo } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useTransactionHistory } from "../contexts/TransactionHistoryContext";

const COLORS = ["#4F46E5", "#6366F1", "#818CF8", "#A5B4FC", "#C7D2FE", "#E0E7FF"];

type ChartData = {
   name: string;
   value: number;
};

const formatPKR = (value: number) => {
   return new Intl.NumberFormat("en-PK", {
      style: "currency",
      currency: "PKR",
      maximumFractionDigits: 0,
   }).format(value);
};

const Portfolio = () => {
   const { transactionsHistory } = useTransactionHistory();

   const sectorData: ChartData[] = useMemo(() => {
      const map: Record<string, number> = {};
      transactionsHistory.forEach((row) => {
         const value = Number(row["Total Amount"]) || 0;
         const sector = row.Sector || "Unknown";
         map[sector] = (map[sector] || 0) + value;
      });
      return Object.entries(map).map(([name, value]) => ({ name, value }));
   }, [transactionsHistory]);

   const totalInvested = useMemo(() => {
      return transactionsHistory.reduce((sum, row) => sum + (Number(row["Total Amount"]) || 0), 0);
   }, [transactionsHistory]);

   return (
      <div className="p-8 bg-slate-50 min-h-screen">
         <div className="max-w-6xl mx-auto flex flex-col md:flex-row gap-8 items-start">
            <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm w-full md:w-[480px] h-[480px] flex flex-col">
               <h3 className="text-slate-800 font-bold text-lg mb-4">Sector Distribution</h3>
               <SectorPieChart data={sectorData} />
            </div>

            <div className="bg-white p-8 rounded-2xl border border-slate-200 shadow-sm flex-1 w-full space-y-6">
               <div>
                  <h2 className="text-slate-500 text-sm font-bold uppercase tracking-widest mb-1">Portfolio Summary</h2>
                  <div className="text-4xl font-black text-slate-900 tracking-tight">{formatPKR(totalInvested)}</div>
               </div>

               <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                     <div className="text-slate-500 text-xs font-semibold mb-1">Total Transactions</div>
                     <div className="text-2xl font-bold text-indigo-600">{transactionsHistory.length}</div>
                  </div>
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
                     <div className="text-slate-500 text-xs font-semibold mb-1">Active Sectors</div>
                     <div className="text-2xl font-bold text-indigo-600">{sectorData.length}</div>
                  </div>
               </div>

               <div className="space-y-3 pt-4 border-t border-slate-100">
                  {sectorData
                     .sort((a, b) => b.value - a.value)
                     .slice(0, 4)
                     .map((sector, i) => (
                        <div key={sector.name} className="flex justify-between items-center text-sm">
                           <div className="flex items-center gap-2">
                              <div
                                 className="w-2 h-2 rounded-full"
                                 style={{ backgroundColor: COLORS[i % COLORS.length] }}
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
                  <Cell
                     key={`cell-${index}`}
                     fill={COLORS[index % COLORS.length]}
                     className="hover:opacity-80 transition-opacity outline-none"
                  />
               ))}
            </Pie>
            <Tooltip
               formatter={(value) => formatPKR(Number(value ?? 0))}
               contentStyle={{
                  background: "#fff",
                  border: "1px solid #E2E8F0",
                  borderRadius: "12px",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                  padding: "12px",
               }}
               itemStyle={{ color: "#4F46E5", fontWeight: "bold" }}
            />
         </PieChart>
      </ResponsiveContainer>
   );
};

export default Portfolio;
