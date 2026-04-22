import { useState } from "react";
import { Group, Drawer, Button, LoadingOverlay } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { isSellTime } from "../../helpers";
import { useTransactions } from "../../hooks/useTransactions";
import { useStocks } from "../../hooks/useStocks";
import { exportToCSV } from "../../services/csvBasket.service";

const BuyAndSell = () => {
   const [opened, { open, close }] = useDisclosure(false);
   const { isLoading, transactions } = useTransactions();
   const [increasePerc, setIncreasePerc] = useState<number>(1.3);
   const { data: dataStocks, isLoading: stocksLoading } = useStocks(false);

   if (stocksLoading || !dataStocks) {
      return (
         <Group justify="center">
            <Button size="md" loading onClick={open}>
               SELL
            </Button>
            <Button loading size="md">
               BUY
            </Button>
         </Group>
      )
   }

   const sellableStocks =
      transactions?.flatMap((t) => {
         const volume = Math.round((t.buy || 0) * 0.25);

         return (dataStocks?.stocks || [])
            .filter((s) => t.symbol === s.symbol && s.price >= t.rate * increasePerc)
            .map((s) => {
               const sellPrice = Number((s.price * 0.95).toFixed(2));
               // Calculate profit as a number for the comparison
               const profit = Number((sellPrice * volume - t.rate * volume).toFixed(2));
               const boughtAt = t.rate

               if (profit < 200) return null;

               return {
                  Account: 110310,
                  Symbol: s.symbol,
                  "Order Side": "SELL",
                  Volume: volume,
                  Price: sellPrice,
                  "Order Type": "SLO",
                  "Limit Price": sellPrice,

                  // statistics
                  profit: profit,
                  boughtAt: boughtAt,
                  currentPrice: s.price,
                  currentStock: transactions.filter(trans => trans.symbol === t.symbol).reduce((acc, curr) => acc + curr.buy, 0)

               };
            })
            .filter((item) => item !== null);
      }) || [];

   let isCalculating = !sellableStocks?.length;

   return (
      <div>
         <Drawer opened={opened} size="xl" onClose={close} title="SELL" style={{ whiteSpace: "pre-line" }}>
            <LoadingOverlay visible={isLoading || isCalculating} zIndex={1000} overlayProps={{ radius: "sm" }} />
            <Button size="compact-xl" onClick={() => exportToCSV(sellableStocks)}>
               Download CSV
            </Button>
            <div className="mt-4">
               <table className="min-w-full border-collapse border border-gray-300">
                  <thead>
                     <tr className="bg-gray-100">
                        <th className="border border-gray-300 px-3 py-2 text-left font-bold">STATEMENT</th>
                        <th className="border border-gray-300 px-3 py-2 text-left font-bold">Realized Profit</th>
                        <th className="border border-gray-300 px-3 py-2 text-left font-bold">Bought At</th>
                        <th className="border border-gray-300 px-3 py-2 text-left font-bold">Current Price</th>
                        <th className="border border-gray-300 px-3 py-2 text-left font-bold">Current in Stock</th>
                     </tr>
                  </thead>
                  <tbody>
                     {sellableStocks.map((s, i) => (
                        <tr key={i}>
                           <td className="border border-gray-300 px-2 py-2">
                              SELL {s.Volume} OF {s.Symbol} AT {s.Price}
                           </td>
                           <td className="border border-gray-300 px-2 py-1">{s.profit}</td>
                           <td className="border border-gray-300 px-2 py-1">{s.boughtAt}</td>
                           <td className="border border-gray-300 px-2 py-1">{s.currentPrice}</td>
                           <td className="border border-gray-300 px-2 py-1">{s.currentStock}</td>
                        </tr>
                     ))}
                  </tbody>
               </table>
            </div>
         </Drawer>

         <Group justify="center">
            <Button size="md" loading={isLoading || !dataStocks} onClick={open}>
               SELL
            </Button>
            <Button disabled size="md">
               BUY
            </Button>
         </Group>
      </div>
   );
};

export default BuyAndSell;
