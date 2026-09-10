"use client";

import { useMemo, useState } from "react";
import { PieChart, Pie, Tooltip, ResponsiveContainer, Sector } from "recharts";
import { Transaction } from "@/features/transactions/types";
import { formatPKRFull, formatPKR } from "../../utils";

const COLORS = [
   "#004D00",
   "#006400",
   "#007500",
   "#008000",
   "#009900",
   "#00AD00",
   "#00C200",
   "#00D600",
   "#00EB00",
   "#00FF00",
   "#1AFF1A",
   "#33FF33",
   "#4DFF4D",
   "#66FF66",
   "#80FF80",
   "#99FF99",
   "#B2FFB2",
   "#CCFFCC",
   "#E6FFE6",
   "#228B22",
   "#32CD32",
   "#2E8B57",
];


const CustomTooltip = ({ active, payload }: any) => {
   if (!active || !payload?.length) return null;
   const { name, payload: data } = payload[0];
   return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 shadow-xl text-sm min-w-[160px]">
         <p className="font-semibold text-slate-100">{name}</p>
         <p className="text-slate-400 mt-0.5">{formatPKRFull(data.amount)}</p>
         <p className="text-sky-400 font-bold mt-0.5">{data.percent.toFixed(2)}%</p>
      </div>
   );
};

export default function SectorAllocation({ transactions = [] }: { transactions: Transaction[] }) {
   const [activeIndex, setActiveIndex] = useState<number | null>(null);

   const { sectorData, totalAmount } = useMemo(() => {
      const map = new Map<string, number>();
      let total = 0;

      transactions.forEach((t) => {
         const amount = Number(t.totalAmount) || 0;
         const sector = t.sector?.trim() || "Unknown";
         map.set(sector, (map.get(sector) || 0) + amount);
         total += amount;
      });

      const data = Array.from(map.entries())
         .map(([name, amount], index) => ({
            name,
            amount,
            percent: total > 0 ? (amount / total) * 100 : 0,
            fill: COLORS[index % COLORS.length],
         }))
         .sort((a, b) => b.amount - a.amount);

      return { sectorData: data, totalAmount: total };
   }, [transactions]);

   // Using the Sector component from Recharts to handle the shape correctly
   const renderShape = (props: any) => {
      const { fill, index, ...rest } = props;
      const isFocused = activeIndex === null || activeIndex === index;

      return (
         <Sector
            {...rest}
            fill={fill}
            opacity={isFocused ? 1 : 0.4}
            className="transition-opacity duration-200 cursor-pointer"
         />
      );
   };

   return (
      <div className="rounded-2xl shadow-sm p-6">
         {/* <div className="flex items-center gap-3 mb-6">
            <h2 className="text-lg font-bold tracking-tight">Sector Allocation</h2>
         </div> */}

         <div className="flex flex-wrap gap-10 items-start">
            <div className="relative shrink-0 w-106 h-106">
               <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                     <Pie
                        data={sectorData}
                        cx="50%"
                        cy="50%"
                        innerRadius={100}
                        outerRadius={200}
                        paddingAngle={1}
                        dataKey="amount"
                        onMouseEnter={(_, i) => setActiveIndex(i)}
                        onMouseLeave={() => setActiveIndex(null)}
                        stroke="none"
                        shape={renderShape}
                     />
                     <Tooltip content={<CustomTooltip />} />
                  </PieChart>
               </ResponsiveContainer>

               <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                  <span className="text-xs font-bold leading-tight max-w-[80px] break-words">
                     {activeIndex !== null ? sectorData[activeIndex].name : "Total"}
                  </span>
                  <span className="text-sm font-bold mt-0.5">
                     {activeIndex !== null ? `${sectorData[activeIndex].percent.toFixed(1)}%` : formatPKR(totalAmount)}
                  </span>
               </div>
            </div>

            <div className="flex-1 min-w-[280px]">
               <div className="flex flex-col gap-1">
                  {sectorData.map((row, i) => (
                     <div
                        key={row.name}
                        onMouseEnter={() => setActiveIndex(i)}
                        onMouseLeave={() => setActiveIndex(null)}
                        className={`flex items-center justify-between p-2 px-4 select-none transition-colors duration-100 rounded-xl ${
                           activeIndex === i ? "bg-green-500/10" : ""
                        }`}>
                        <div className="flex items-center gap-2 flex-1 min-w-0">
                           <span className="w-2.5 h-2.5 rounded-sm shrink-0" style={{ backgroundColor: row.fill }} />
                           <span className="text-sm truncate">{row.name}</span>
                        </div>

                        <div className="flex items-center gap-4 ml-4">
                           <span className="text-sm font-bold w-14 text-right">{row.percent.toFixed(2)}%</span>
                           <span className="text-sm text-right min-w-[100px]">{formatPKRFull(row.amount)}</span>
                        </div>
                     </div>
                  ))}
               </div>
            </div>
         </div>
      </div>
   );
}
