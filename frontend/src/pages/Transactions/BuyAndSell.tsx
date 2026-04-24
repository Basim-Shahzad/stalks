import { Group, Drawer, Button, LoadingOverlay, Text } from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { useTransactions } from "../../hooks/useTransactions";
import { useSettings } from "../../hooks/useSettings";
import { useStocks } from "../../hooks/useStocks";
import { exportToCSV } from "../../services/csvBasket.service";

const BuyAndSell = () => {
   const [opened, { open, close }] = useDisclosure(false);
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
               // Calculate profit as a number for the comparison
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

                  // statistics
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
         <Drawer
            opened={opened}
            size="xl"
            onClose={close}
            title={
               <Text fw={60} size="xl" style={{ letterSpacing: "1px" }}>
                  SELL
               </Text>
            }
            style={{ whiteSpace: "pre-line" }}>
            <LoadingOverlay visible={isLoading} zIndex={1000} overlayProps={{ radius: "sm" }} />
            <Button size="compact-xl" onClick={() => exportToCSV(sellableStocks as any)}>
               Download CSV
            </Button>
            <div className="mt-6 overflow-hidden rounded-xl border border-gray-200 shadow-sm">
               <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                     <tr>
                        {["Statement", "Realized Profit", "Bought At", "Current Price", "In Stock"].map((header) => (
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
                        sellableStocks.map((s, i) => (
                           <tr key={i} className="hover:bg-gray-50 transition-colors">
                              <td className="whitespace-nowrap px-6 py-4 text-sm font-medium text-blue-600">
                                 SELL <span className="text-gray-900">{s.Volume}</span> OF {s.Symbol} AT {s.Price}
                              </td>
                              <td
                                 className={`whitespace-nowrap px-6 py-4 text-sm font-bold ${s.profit >= 0 ? "text-green-600" : "text-red-600"}`}>
                                 {s.profit >= 0 ? `+${s.profit}` : s.profit}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">{s.boughtAt}</td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-900 font-semibold">
                                 {s.currentPrice}
                              </td>
                              <td className="whitespace-nowrap px-6 py-4 text-sm text-gray-600">{s.currentStock}</td>
                           </tr>
                        ))
                     ) : (
                        <tr>
                           <td colSpan={5} className="px-6 py-12 text-center">
                              <div className="flex flex-col items-center justify-center">
                                 <span className="text-gray-400 text-4xl mb-2">📊</span>
                                 <p className="text-lg font-medium text-gray-500">No stocks match your criteria</p>
                              </div>
                           </td>
                        </tr>
                     )}
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
