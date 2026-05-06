import { useMemo, useState } from "react";
import { useTransactions } from "../../hooks/useTransactions";
import { useSettings } from "../../hooks/useSettings";
import { useStocks } from "../../hooks/useStocks";
import { Modal, Spinner, ModalHeader, ModalBody, ModalFooter, ModalContainer, Button } from "@heroui/react";
import { exportToCSV } from "../../services/csvBasket.service";

interface SellableStock {
   Account: number;
   Symbol: string;
   "Order Side": "SELL";
   Volume: number;
   Price: number;
   "Order Type": "SLO";
   "Limit Price": number;
   profit: number;
   boughtAt: number;
   currentPrice: number;
   currentStock: number;
}

const BuyAndSell = () => {
   const { isLoading, transactions } = useTransactions();
   const { increaseByPercInSell } = useSettings();
   const [shouldFetchStocks, setShouldFetchStocks] = useState(false);
   const { isLoading: isLoadingStock, data: dataStocks } = useStocks(false, 1, 10, shouldFetchStocks);

   const stockMap = useMemo(() => {
      if (!dataStocks?.stocks) return new Map();

      const map = new Map();
      dataStocks.stocks.forEach((s) => map.set(s.symbol, s));
      return map;
   }, [dataStocks]);

   const holdingsMap = useMemo(() => {
      if (!transactions) return new Map();

      const map = new Map();

      transactions.forEach((t) => {
         map.set(t.symbol, (map.get(t.symbol) || 0) + (t.buy || 0));
      });

      return map;
   }, [transactions]);

   const sellableStocks = useMemo<SellableStock[]>(() => {
      if (!transactions || !dataStocks?.stocks) return [];

      return transactions.flatMap((t) => {
         const stock = stockMap.get(t.symbol);
         if (!stock) return [];

         const volume = Math.round((t.buy || 0) * 0.25);
         if (volume <= 0) return [];

         const threshold = t.rate * increaseByPercInSell;
         if (stock.price < threshold) return [];

         const sellPrice = Number((stock.price * 0.95).toFixed(2));
         const profit = Number((sellPrice * volume - t.rate * volume).toFixed(2));
         if (profit < 200) return [];

         return [
            {
               Account: 110310,
               Symbol: stock.symbol,
               "Order Side": "SELL",
               Volume: volume,
               Price: sellPrice,
               "Order Type": "SLO",
               "Limit Price": sellPrice,
               profit,
               boughtAt: t.rate,
               currentPrice: stock.price,
               currentStock: holdingsMap.get(t.symbol) || 0,
            },
         ];
      });
   }, [transactions, stockMap, holdingsMap, increaseByPercInSell]);

   return (
      <div>
         <div className="flex justify-center gap-4">
            <div>
               <Modal>
                  <Button className="bg-blue-600 text-white" size="md" onClick={() => setShouldFetchStocks(true)} >
                     SELL
                  </Button>
                  <Modal.Backdrop>
                     <ModalContainer size="cover">
                        <Modal.Dialog>
                           <ModalHeader>SELL ORDERS</ModalHeader>

                           <ModalBody>
                              {isLoading || isLoadingStock && (
                                 <div className="absolute inset-0 z-50 flex items-center justify-center bg-white/60 backdrop-blur-sm">
                                    <Spinner size="lg" />
                                 </div>
                              )}

                              <div className="mb-4">
                                 <Button
                                    className="bg-blue-600 text-white"
                                    isDisabled={sellableStocks.length === 0}
                                    onClick={() => exportToCSV(sellableStocks as any)}>
                                    ↓ Download CSV
                                 </Button>
                              </div>

                              <div className="overflow-hidden rounded-xl border border-gray-200 shadow-sm">
                                 <table className="min-w-full divide-y divide-gray-200">
                                    <thead className="bg-gray-50">
                                       <tr>
                                          {[
                                             "Statement",
                                             "Realized Profit",
                                             "Bought At",
                                             "Current Price",
                                             "In Stock",
                                          ].map((header) => (
                                             <th
                                                key={header}
                                                className="px-6 py-3 text-left text-xs font-semibold uppercase tracking-wider text-gray-500">
                                                {header}
                                             </th>
                                          ))}
                                       </tr>
                                    </thead>

                                    <tbody className="divide-y divide-gray-200 bg-white">
                                       {sellableStocks.length > 0 ? (
                                          sellableStocks.map((s) => (
                                             <tr
                                                key={`${s.Symbol}-${s.boughtAt}-${s.Price}`}
                                                className="transition-colors hover:bg-gray-50">
                                                <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-blue-600">
                                                   SELL <span className="text-gray-900">{s.Volume}</span> OF {s.Symbol}{" "}
                                                   AT {s.Price}
                                                </td>

                                                <td
                                                   className={`whitespace-nowrap px-6 py-4 text-sm font-bold ${
                                                      s.profit >= 0 ? "text-green-600" : "text-red-600"
                                                   }`}>
                                                   {s.profit >= 0 ? `+${s.profit}` : s.profit}
                                                </td>

                                                <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">
                                                   {s.boughtAt}
                                                </td>

                                                <td className="whitespace-nowrap px-6 py-4 text-sm font-semibold text-gray-900">
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
                                                <div className="flex flex-col items-center justify-center gap-2">
                                                   <span className="text-4xl">📊</span>
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
                           </ModalBody>

                           <ModalFooter>
                              <Button slot="close" variant="secondary">
                                 Close
                              </Button>
                           </ModalFooter>
                        </Modal.Dialog>
                     </ModalContainer>
                  </Modal.Backdrop>
               </Modal>
            </div>

            <Button isDisabled size="md">
               BUY
            </Button>
         </div>
      </div>
   );
};

export default BuyAndSell;
