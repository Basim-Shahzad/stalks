import { useMemo, useState } from "react";
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer } from "recharts";
import { useTransactions } from "../../hooks/useTransactions";
import type { TradeTransaction } from "../../types";

const COLORS = [
   "#1B3A6B",
   "#E63946",
   "#2A9D8F",
   "#E9C46A",
   "#6A0572",
   "#56B4D3",
   "#C1440E",
   "#264653",
   "#F4A261",
   "#457B9D",
   "#A8DADC",
   "#8B5E3C",
   "#6DBF67",
   "#FF6B6B",
   "#4ECDC4",
   "#C3A6FF",
   "#FFD166",
   "#06D6A0",
   "#118AB2",
   "#073B4C",
   "#B5838D",
   "#6C757D",
];

function formatPKR(value: number): string {
   if (value >= 1_000_000) return `PKR ${(value / 1_000_000).toFixed(2)}M`;
   if (value >= 1_000) return `PKR ${(value / 1_000).toFixed(2)}K`;
   return `PKR ${value.toFixed(2)}`;
}

function formatPKRFull(value: number): string {
   return `PKR ${value.toLocaleString("en-PK", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

interface TooltipPayloadItem {
   name: string;
   payload: { percent: number; amount: number };
}

const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: TooltipPayloadItem[] }) => {
   if (!active || !payload?.length) return null;
   const { name, payload: inner } = payload[0];
   return (
      <div className="bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 shadow-xl text-sm min-w-[160px]">
         <p className="font-semibold text-slate-100">{name}</p>
         <p className="text-slate-400 mt-0.5">{formatPKRFull(inner.amount)}</p>
         <p className="text-sky-400 font-bold mt-0.5">{inner.percent.toFixed(2)}%</p>
      </div>
   );
};

const SectorAllocation = () => {
   const { transactions } = useTransactions();
   const safeTransactions: TradeTransaction[] = useMemo(() => transactions ?? [], [transactions]);
   const [activeIndex, setActiveIndex] = useState<number | null>(null);

   const sectorData = useMemo(() => {
      const map = new Map<string, number>();
      for (const t of safeTransactions) {
         const sector = t.sector?.trim() || "Unknown";
         map.set(sector, (map.get(sector) ?? 0) + (t.total_amount ?? 0));
      }
      const total = Array.from(map.values()).reduce((a, b) => a + b, 0);
      return Array.from(map.entries())
         .map(([name, amount]) => ({
            name,
            amount,
            percent: total > 0 ? (amount / total) * 100 : 0,
         }))
         .sort((a, b) => b.amount - a.amount);
   }, [safeTransactions]);

   const totalAmount = useMemo(() => sectorData.reduce((s, d) => s + d.amount, 0), [sectorData]);

   return (
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-7">
         {/* Header */}
         <div className="flex items-center gap-3 mb-6">
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Sector Allocation</h2>
            <span className="text-xs font-semibold text-green-600 bg-green-100 px-2.5 py-0.5 rounded-full">
               Verified ✓
            </span>
         </div>

         {/* Body */}
         <div className="flex flex-wrap gap-10 items-start">
            {/* Donut chart */}
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
                        onMouseEnter={(_, index) => setActiveIndex(index)}
                        onMouseLeave={() => setActiveIndex(null)}
                        stroke="none">
                        {sectorData.map((entry, index) => (
                           <Cell
                              key={entry.name}
                              fill={COLORS[index % COLORS.length]}
                              opacity={activeIndex === null || activeIndex === index ? 1 : 0.4}
                              style={{ cursor: "pointer", transition: "opacity 0.2s" }}
                           />
                        ))}
                     </Pie>
                     <Tooltip content={<CustomTooltip />} />
                  </PieChart>
               </ResponsiveContainer>

               {/* Centre label */}
               <div className="absolute inset-0 flex flex-col items-center justify-center pointer-events-none text-center">
                  {activeIndex !== null ? (
                     <>
                        <span className="text-xs font-bold text-slate-800 leading-tight max-w-[80px] break-words">
                           {sectorData[activeIndex]?.name}
                        </span>
                        <span className="text-xs text-slate-500 mt-0.5">
                           {sectorData[activeIndex]?.percent.toFixed(1)}%
                        </span>
                     </>
                  ) : (
                     <>
                        <span className="text-xs text-slate-400 font-medium">Total</span>
                        <span className="text-sm font-bold text-slate-800 mt-0.5">{formatPKR(totalAmount)}</span>
                     </>
                  )}
               </div>
            </div>

            {/* Legend table */}
            <div className="flex-1 min-w-[280px]e max-h-[420px]e pr-1">
               <table className="w-full border-collapse">
                  <tbody>
                     {sectorData.map((row, index) => (
                        <tr
                           key={row.name}
                           onMouseEnter={() => setActiveIndex(index)}
                           onMouseLeave={() => setActiveIndex(null)}
                           className={`cursor-pointer transition-colors ${
                              activeIndex === index ? "bg-slate-100" : "hover:bg-slate-50"
                           }`}>
                           <td className="py-1.5 pr-3 whitespace-nowrap">
                              <div className="flex items-center gap-2">
                                 <span
                                    className="inline-block w-2.5 h-2.5 rounded-sm shrink-0"
                                    style={{ backgroundColor: COLORS[index % COLORS.length] }}
                                 />
                                 <span className="text-sm text-slate-600">{row.name}</span>
                              </div>
                           </td>
                           <td className="py-1.5 px-3 text-sm font-bold text-slate-900 text-right whitespace-nowrap">
                              {row.percent.toFixed(2)}%
                           </td>
                           <td className="py-1.5 pl-2 text-sm text-slate-500 text-right whitespace-nowrap">
                              {formatPKRFull(row.amount)}
                           </td>
                        </tr>
                     ))}
                  </tbody>
               </table>
            </div>
         </div>
      </div>
   );
};

export default SectorAllocation;
