import React from "react";
import Papa from "papaparse";
import { useTransactionHistory } from "../contexts/TransactionHistoryContext";
import type { StockRow } from "../types";

const TransactionHistory = () => {
   const { setTransactionsHistory, transactionsHistory } = useTransactionHistory()

   const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      Papa.parse<StockRow>(file, {
         header: true,
         skipEmptyLines: true,
         complete: (results) => {
            console.log("Parsed CSV Data:", results.data);
            setTransactionsHistory(results.data);
         },
         error: (error: Error) => {
            alert("Error parsing CSV: " + error.message);
         },
      });
   };

   return (
      <div className="p-8 bg-slate-50 min-h-screen font-sans text-slate-900">
         <div className="">

            <header className="flex items-center justify-between mb-8">
               <input
                  type="file"
                  accept=".csv"
                  onChange={handleFileChange}
                  className="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-md file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-all cursor-pointer"
               />
            </header>

            {transactionsHistory.length > 0 && (
               <div className="overflow-hidden bg-white border border-slate-200 rounded-xl shadow-sm">
                  <table className="w-full text-left border-collapse">
                     <thead>
                        <tr className="bg-slate-50 border-b border-slate-200">
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">Date</th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                              Symbol
                           </th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                              Company
                           </th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">
                              Buy Qty
                           </th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">
                              Rate
                           </th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500 text-right">
                              Total
                           </th>
                           <th className="px-6 py-4 text-xs font-bold uppercase tracking-wider text-slate-500">
                              Sector
                           </th>
                        </tr>
                     </thead>
                     <tbody className="divide-y divide-slate-100">
                        {transactionsHistory.map((row, index) => (
                           <tr key={index} className="hover:bg-indigo-50/30 transition-colors">
                              <td className="px-6 py-4 text-sm text-slate-600">{row.Date}</td>
                              <td className="px-6 py-4 text-sm font-mono font-bold text-indigo-600">{row.Symbol}</td>
                              <td className="px-6 py-4 text-sm text-slate-800 font-medium">{row.Company}</td>
                              <td className="px-6 py-4 text-sm text-slate-600 text-right">{row.Buy}</td>
                              <td className="px-6 py-4 text-sm text-slate-600 text-right">{row.Rate}</td>
                              <td className="px-6 py-4 text-sm font-semibold text-slate-900 text-right">
                                 {row["Total Amount"]}
                              </td>
                              <td className="px-6 py-4 text-sm">
                                 <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-700 border border-slate-200">
                                    {row.Sector}
                                 </span>
                              </td>
                           </tr>
                        ))}
                     </tbody>
                  </table>
               </div>
            )}
         </div>
      </div>
   );
};

export default TransactionHistory;
