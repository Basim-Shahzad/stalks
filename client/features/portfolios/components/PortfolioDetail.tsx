"use client";

import { use } from "react";
import { usePortfolio, usePortfolioHoldings } from "../hooks";
import Header from "@/features/layout/components/Header";
import HoldingsTable from "./HoldingsTable";

const PortfolioDetail = ({ params }: { params: Promise<{ portfolio_id: string }> }) => {
   const { portfolio_id } = use(params);

   const { data: portfolio, isLoading: portfolioLoading, isError: portfolioError } = usePortfolio(portfolio_id);

   const {
      data: portfolioHoldings,
      isLoading: holdingsLoading,
      isError: holdingsError,
   } = usePortfolioHoldings(portfolio_id);

   let isSkeleton: boolean = portfolioLoading || !portfolio || holdingsLoading || !portfolioHoldings;

   if (
      portfolioLoading ||
      holdingsLoading ||
      isSkeleton ||
      portfolioError ||
      holdingsError ||
      !portfolio ||
      !portfolioHoldings
   ) {
      return (
         <div>
            <Header title="Loading..."></Header>
         </div>
      )
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
         <Header title={portfolio?.name ?? "Portfolio"} />

         <section>
            <HoldingsTable holdings={portfolioHoldings?.holdings} />
         </section>
      </main>
   );
};

export default PortfolioDetail;
