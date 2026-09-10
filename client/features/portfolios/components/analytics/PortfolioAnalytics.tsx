"use client";

import React, { useMemo } from "react";
import { Transaction } from "@/features/transactions/types";
import { Portfolio } from "../../types";
import { formatPKRFull } from "../../utils";
import { computeRealizedProfit } from "@/lib/realizedProfit";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
   title: string | undefined;
   stat: number | undefined;
   isSkeleton: boolean;
}

const StatCard: React.FC<StatCardProps> = ({ title, stat, isSkeleton }) => {
   return (
      <div className="relative select-none overflow-hidden rounded-2xl border border-primary/20 bg-background p-6 transition-all duration-300 hover:border-primary/40 hover:shadow-[0_0_20px_var(--primary)]/10">
         <div className="absolute inset-0 bg-primary/10 pointer-events-none" />

         <div className="relative z-10 flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">{title}</span>

            <span className="text-3xl font-bold font-mono tracking-tight text-foreground">
               {
                  isSkeleton ? (
                     <Skeleton className="h-8 w-full bg-primary/10" />
                  ) : (
                     formatPKRFull(stat!)
                  )
               }
            </span>
         </div>
      </div>
   );
};

type PortfolioAnalyticsProps = {
   transactions: Transaction[] | undefined;
   portfolio: Portfolio | undefined;
   isSkeleton: boolean;
};

const PortfolioAnalytics: React.FC<PortfolioAnalyticsProps> = ({ transactions, isSkeleton }) => {
   const stats = useMemo(() => {
      const totalAmountInvested = transactions?.reduce((acc, t) => {
         const amount = t.rate * t.quantity;
         if (t.side === "BUY") {
            return acc + amount;
         } else if (t.side === "SELL") {
            return acc - amount;
         }

         return acc;
      }, 0);

      const totalCosts = transactions?.reduce((acc, t) => {
         const charges = Number(t.charges) || 0;
         const commission = Number(t.commission) || 0;
         const taxes = Number(t.taxes) || 0;

         return acc + charges + commission + taxes;
      }, 0);

      const { totalRealizedProfit } = computeRealizedProfit(transactions);

      return [
         { title: "Total Amount Invested", stat: totalAmountInvested },
         { title: "Total Costs", stat: totalCosts },
         { title: "Realized Profit", stat: totalRealizedProfit },
      ];
   }, [transactions]);

   return (
      <div className="grid grid-cols-4 gap-4 my-8 mx-8">
         {stats.map((stat) => (
            <StatCard key={stat.title} title={stat.title} stat={stat.stat} isSkeleton={isSkeleton} />
         ))}
      </div>
   );
};

export default PortfolioAnalytics;
