import React from "react";
import {
   Button,
   Drawer,
   useOverlayState,
   Spinner,
} from "@heroui/react";
import { useTransactions } from "../../hooks/useTransactions";
import { useSettings } from "../../hooks/useSettings";
import { useStocks } from "../../hooks/useStocks";
import { exportToCSV } from "../../services/csvBasket.service";

const BuyAndSell = () => {
   const drawerState = useOverlayState();
   const { isLoading, transactions } = useTransactions();
   const { increaseByPercInSell } = useSettings();
   const { data: dataStocks } = useStocks(false);

   const sellableStocks =
      transactions?.flatMap((t) => {
         const volume = Math.round((t.buy || 0) * 0.25);

         return (dataStocks?.stocks || [])
            .filter((s) => t.symbol === s.symbol && s.price >= t.rate * increaseByPercInSell)
            .map((s) => {
               const sellPrice = Number((s.price * 0.95).toFixed(2));
               const profit = Number((sellPrice * volume - t.rate * volume).toFixed(2));
               const boughtAt = t.rate;

               if (profit < 200) return null;

               return {
                  Account: 110310,
                  Symbol: s.symbol,
                  "Order Side": "SELL",
                  Volume: volume,
                  Price: sellPrice,
                  "Order Type": "SLO",
                  "Limit Price": sellPrice,
                  profit: profit,
                  boughtAt: boughtAt,
                  currentPrice: s.price,
                  currentStock: transactions
                     .filter((trans) => trans.symbol === t.symbol)
                     .reduce((acc, curr) => acc + curr.buy, 0),
               };
            })
            .filter((item) => item !== null);
      }) || [];

   return (
      <div>
         {/* v3 Uses Compound Component Pattern */}
         <Drawer isOpen={drawerState.isOpen} onOpenChange={drawerState.setOpen} size="xl">
            <Drawer.Content>
               <Drawer.Header>
                  <span style={{ fontWeight: 600, fontSize: "1.25rem", letterSpacing: "1px" }}>SELL</span>
               </Drawer.Header>
               <Drawer.Body>
                  {isLoading && (
                     <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/50 backdrop-blur-sm">
                        <Spinner size="lg" />
                     </div>
                  )}

                  <Button
                     variant="solid"
                     className="bg-blue-600 text-white"
                     onClick={() => exportToCSV(sellableStocks as any)}>
                     Download CSV
                  </Button>

                  <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 shadow-sm">
                     <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                           <tr>
                              {["Statement", "Realized Profit", "Bought At", "Current Price", "In Stock"].map(
                                 (header) => (
                                    <th
                                       key={header}
                                       className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                       {header}
                                    </th>
                                 ),
                              )}
                           </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 bg-white">
                           {sellableStocks.length > 0 ? (
                              sellableStocks.map((s, i) => (
                                 <tr key={i} className="hover:bg-gray-50 transition-colors">
                                    <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-blue-600">
                                       SELL <span className="text-gray-900">{s.Volume}</span> OF {s.Symbol} AT {s.Price}
                                    </td>
                                    <td
                                       className={`whitespace-nowrap px-6 py-4 text-sm font-bold ${
                                          s.profit >= 0 ? "text-green-600" : "text-red-600"
                                       }`}>
                                       {s.profit >= 0 ? `+${s.profit}` : s.profit}
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">{s.boughtAt}</td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 font-semibold">
                                       {s.currentPrice}
                                    </td>
                                    <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                                       {s.currentStock}
                                    </td>
                                 </tr>
                              ))
                           ) : (
                              <tr>
                                 <td colSpan={5} className="px-6 py-12 text-center">
                                    <div className="flex flex-col items-center justify-center">
                                       <span className="text-gray-400 text-4xl mb-2">📊</span>
                                       <p className="text-lg font-medium text-gray-500">
                                          No stocks match your criteria
                                       </p>
                                    </div>
                                 </td>
                              </tr>
                           )}
                        </tbody>
                     </table>
                  </div>
               </Drawer.Body>
               <Drawer.Footer>
                  <Button variant="light" onClick={drawerState.close}>
                     Close
                  </Button>
               </Drawer.Footer>
            </Drawer.Content>
         </Drawer>

         <div className="flex justify-center gap-4">
            <Button
               className="bg-blue-600 text-white"
               size="md"
               isLoading={isLoading || !dataStocks}
               onClick={drawerState.open}>
               SELL
            </Button>
            <Button isDisabled size="md">
               BUY
            </Button>
         </div>
      </div>
   );
};

export default BuyAndSell;
