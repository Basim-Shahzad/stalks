"use client";

import { useState } from "react";
import Header from "../components/Header";
import CandlestickChart, { OHLCV } from "@/components/CandleStickChart";
import { useMarketData } from "@/lib/queries/marketQueries";

export default function StocksPage() {
   const [isVolume, setIsVolume] = useState<boolean>(false);
   const { data: res, isLoading, isError, error } = useMarketData("PSX", "SAZEW", 365);

   return (
      <div className="animate-fade-in">
         <Header title="Stocks" />

         <div>
            <input type="checkbox" checked={isVolume} onChange={(e) => setIsVolume(e.target.checked)} />
            <label>Volume</label>
         </div>

         <div className="flex justify-center">
            <div style={{ width: "80%", height: 600 }}>
               <CandlestickChart
                  data={res?.data?.data as OHLCV[]}
                  symbol="PSX:HBL"
                  showVolume={isVolume}
                  upColor="#26a69a"
                  downColor="#ef5350"
                  backgroundColor="#0b0e11"
               />

               {isLoading && <p>Loading...</p>}
               {isError && <p>Error: {error?.message}</p>}
            </div>
         </div>
      </div>
   );
}
