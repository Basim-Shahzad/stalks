import { useMemo } from "react";
import { useTransactions } from "../../hooks/useTransactions";
import type { TradeTransaction } from "../../types";
import { StatCard } from "./Card";
import SectorAllocation from "./SectorAllocation";
import StockLevelSummary from "./StockLevelSummary";

const Portfolio = () => {
   const { transactions } = useTransactions();

   const safeTransactions: TradeTransaction[] = useMemo(() => transactions ?? [], [transactions]);

   const stats = useMemo(() => {
      let totalValue = 0;
      let totalBuyValue = 0;
      let totalSellValue = 0;

      let totalCommission = 0;
      let totalTaxes = 0;
      let totalCharges = 0;

      const companies: string[] = [];
      const sectors: string[] = [];

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

         const symbol = t.symbol ?? "Unknown";
         const sector = t.sector ?? "Unknown";

         if (!companies.includes(symbol)) {
            companies.push(symbol);
         }

         if (!sectors.includes(sector)) {
            sectors.push(sector);
         }
      }

      const totalCosts = totalCommission + totalTaxes + totalCharges;

      return [
         {
            title: "Total Invested",
            stat: totalValue,
            isCurrency: true,
         },
         {
            title: "Total Companies",
            stat: companies.length ?? 0,
            isCurrency: false,
         },
         {
            title: "Unique Stocks",
            stat: sectors.length,
            isCurrency: false,
         },
         {
            title: "Total Transactions",
            stat: safeTransactions.length,
            isCurrency: false,
         },
         {
            title: "Total Costs",
            stat: totalCosts,
            isCurrency: true,
         },
      ];
   }, [safeTransactions]);

   return (
      <div className="p-8 bg-slate-50 min-h-screen">
         <div style={{ display: "flex", gap: "16px" }}>
            {stats.map((s, index) => (
               <StatCard key={index} title={s.title} stat={s.stat} isCurrency={s.isCurrency} />
            ))}
         </div>

         <div className="mt-8">
            <SectorAllocation />
         </div>

         <div className="mt-8">
            <StockLevelSummary />
         </div>
      </div>
   );
};

/**
 * 🎯 HOVERABLE STAT CARD
 */
// const StatCard = ({ label, value, info }: { label: string; value: string | number; info: string }) => {
//    return (
//       <div className="relative group p-4 rounded-xl bg-slate-50 border border-slate-100">
//          <div className="text-slate-500 text-xs font-semibold mb-1">{label}</div>

//          <div className="text-2xl font-bold text-indigo-600">{value}</div>

//          <div className="absolute z-10 left-1/2 -translate-x-1/2 bottom-full mb-2 hidden group-hover:block w-56">
//             <div className="bg-slate-900 text-white text-xs p-3 rounded-lg shadow-lg">{info}</div>
//          </div>
//       </div>
//    );
// };

/**
 * PIE CHART
 */
// const SectorPieChart = ({ data }: { data: ChartData[] }) => {
//    return (
//       <ResponsiveContainer width="100%" height="100%">
//          <PieChart>
//             <Pie
//                data={data}
//                dataKey="value"
//                nameKey="name"
//                outerRadius={140}
//                innerRadius={100}
//                paddingAngle={5}
//                stroke="none">
//                {data.map((_, index) => (
//                   <Cell key={index} fill={COLORS[index % COLORS.length]} />
//                ))}
//             </Pie>

//             <Tooltip
//                formatter={(value) => formatPKR(Number(value ?? 0))}
//                contentStyle={{
//                   background: "#fff",
//                   border: "1px solid #E2E8F0",
//                   borderRadius: "12px",
//                   padding: "12px",
//                }}
//             />
//          </PieChart>
//       </ResponsiveContainer>
//    );
// };

export default Portfolio;
