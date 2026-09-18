"use client";

import { use, useState, useMemo } from "react";
import { usePortfolio, usePortfolioHoldings } from "../hooks";
import { useTransactions } from "@/features/transactions/hooks/useTransactions";
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs";
import Header from "@/features/layout/components/Header";
import HoldingsTable from "./HoldingsTable";
import { StatCard } from "./analytics/StatCard";
import SectorAllocation from "./analytics/SectorAllocation";
import { formatCamelCase } from "../utils";

const PortfolioDetail = ({
   params,
}: {
   params: Promise<{ portfolio_id: string }>;
}) => {
   const { portfolio_id } = use(params);
   const [activeTab, setActiveTab] = useState<"stats" | "holdings">("stats");

   const {
      data: portfolio,
      isLoading: portfolioLoading,
      isError: portfolioError,
   } = usePortfolio(portfolio_id);

   const {
      data: portfolioHoldings,
      isLoading: holdingsLoading,
      isError: holdingsError,
   } = usePortfolioHoldings(portfolio_id);

   const {
      data: transactions,
      isLoading: isTransactionsLoading,
      isError: isTransactionsError,
   } = useTransactions({
      portfolios: new Set([portfolio_id]),
   });

   if (portfolioLoading || !portfolio) {
      return (
         <div>
            <Header title="Loading..."></Header>
         </div>
      );
   }

   if (holdingsLoading || !portfolioHoldings) {
      return <div>Loading....</div>;
   }

   if (portfolioError) {
      return (
         <div className="w-full h-64 text-red-500 flex items-center justify-center">
            <h1>There was an error fetching your portfolio</h1>
         </div>
      );
   }

   return (
      <main>
         <Header
            title={portfolio?.name ?? "Portfolio"}
            right={
               <Tabs
                  value={activeTab}
                  onValueChange={(value) =>
                     setActiveTab(value as "stats" | "holdings")
                  }
                  className=""
               >
                  <TabsList className="w-75">
                     <TabsTrigger value="stats">Stats</TabsTrigger>
                     <TabsTrigger value="holdings">Holdings</TabsTrigger>
                  </TabsList>
               </Tabs>
            }
         />

         {activeTab === "holdings" && (
            <HoldingsTable holdings={portfolioHoldings?.holdings ?? []} />
         )}

         {activeTab === "stats" && (
            <div className="stats">
               <div className="mini-stats flex flex-wrap grid-cols-5 justify-center items-center gap-4 px-4 py-4">
                  {Object.entries(portfolioHoldings?.summary).map(
                     ([key, value]) => (
                        <StatCard
                           isSkeleton={holdingsLoading}
                           title={formatCamelCase(key)}
                           stat={Number(value)}
                           key={key}
                        />
                     ),
                  )}
               </div>
               <SectorAllocation transactions={transactions ?? []} />
            </div>
         )}
      </main>
   );
};

export default PortfolioDetail;
