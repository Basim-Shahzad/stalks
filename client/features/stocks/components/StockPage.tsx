"use client";

import Header from "@/features/layout/components/Header";
import { useMarketData } from "../hooks";
import StockChart from "./StockChart";

export default function StockPage() {
   const {
      data: stockData,
      isLoading,
      isError,
      error,
   } = useMarketData("PSX", "TPL");

   return (
      <div className="animate-fade-in">
         <Header title="Stocks" />

         <div className="mx-auto w-full max-w-[1600px] px-4 py-6">
            {isLoading && <p>Loading market data...</p>}

            {isError && <p className="text-red-500">Error: {error?.message}</p>}

            {!isLoading && !isError && stockData && (
               <StockChart
                  data={stockData.data}
                  symbol={stockData.symbol}
                  exchange={stockData.exchange}
                  height={600}
               />
            )}
         </div>
      </div>
   );
}
