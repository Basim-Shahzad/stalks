import Papa from "papaparse";

interface csvHeaders {
   Account: number;
   Symbol: string;
   "Order Side": "SELL" | "BUY";
   Volume: number;
   Price: string;
   "Order Type": string;
   "Limit Price": number;
}

export const exportToCSV = (data: csvHeaders[]) => {

   const formattedData = data.map((s) => ({
      Account: s.Account,
      Symbol: s.Symbol,
      "Order Side": s["Order Side"],
      Volume: s.Volume,
      Price: s.Price,
      "Order Type": s["Order Type"],
      "Limit Price": s["Limit Price"],
   }));

   // 2. Convert to CSV string using PapaParse
   const csv = Papa.unparse(formattedData);

   // 3. Create a download link and trigger it
   const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
   const url = URL.createObjectURL(blob);
   const link = document.createElement("a");

   link.href = url;
   link.setAttribute("download", "custom_report.csv");
   link.click();

   // Cleanup
   URL.revokeObjectURL(url);
};
