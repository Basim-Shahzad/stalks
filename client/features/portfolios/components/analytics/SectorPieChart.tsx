import React from "react";
import { Transaction } from "@/features/transactions/types";
import { Pie, PieChart, Tooltip } from "recharts";

type SectorPieChartProps = {
   transactions: Transaction[];
};

const SectorPieChart: React.FC<SectorPieChartProps> = ({ transactions }) => {
   return (
      <article>
         <PieChart width={400} height={400}>
            <Pie
               data={transactions}
               dataKey="sector"
               // isAnimationActive={isAnimationActive}
            />
            <Tooltip defaultIndex={2} />
         </PieChart>
      </article>
   );
};

export default SectorPieChart;
