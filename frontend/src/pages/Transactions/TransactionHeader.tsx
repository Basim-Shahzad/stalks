import { useState } from "react";
import { useTransactionsFromPDF } from "../../hooks/useTransactionsFromPDF";

const TransactionsHeader = () => {
   const [file, setFile] = useState<File | null>(null);
   const { mutate, data, isPending, error, isSuccess } = useTransactionsFromPDF();

   const handleUpload = () => {
      if (!file) return;
      mutate(file);
      if (isSuccess) {
         setFile(null);
      }
   };

   return (
      <header className="bg-white rounded-2xl border border-slate-200 shadow-sm p-0.5 w-max flex ">
         <div className="relative group">
            <input
               type="file"
               title="Upload a PDF of Munir Khanani Transactions"
               accept=".pdf"
               onChange={(e) => setFile(e.target.files?.[0] || null)}
               className="block w-full text-sm text-slate-500  file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100 transition-all cursor-pointer border border-dashed border-slate-300 rounded-xl p-4 hover:border-indigo-400"
            />
         </div>

         <button
            onClick={handleUpload}
            disabled={isPending || !file}
            className="bg-indigo-600 px-12 text-white font-bold rounded-xl hover:bg-indigo-700 disabled:bg-slate-200 disabled:text-slate-400 disabled:cursor-not-allowed transition-all shadow-lg shadow-indigo-100 active:scale-[0.98]">
            {isPending ? "Processing..." : "Upload"}
         </button>

         {error && (
            <div className="p-3 bg-rose-50 border border-rose-100 rounded-lg text-rose-600 text-xs font-medium text-center">
               Error processing document. Please try again.
            </div>
         )}

         {isSuccess && (
            <div className="p-3 bg-green-50 border border-green-100 rounded-lg text-green-600 text-xs font-medium text-center">
               Successfully uploaded the PDF.
            </div>
         )}
      </header>
   );
};

export default TransactionsHeader;
