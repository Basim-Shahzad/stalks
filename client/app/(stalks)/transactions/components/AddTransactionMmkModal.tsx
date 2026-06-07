"use client";

import React, { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { usePortfolios } from "@/lib/queries/portfolioQueries";
import { useTransactionApi } from "@/hooks/useTransactionApi";
import { useTransactionsCreatePdf } from "@/lib/contexts/TransactionsCreatePdf";

type AddTransactionMmkModalProps = {
   open: boolean;
   setOpen: (open: boolean) => void;
};

const AddTransactionMmkModal: React.FC<AddTransactionMmkModalProps> = ({ open, setOpen }) => {
   const [pId, setPId] = useState<string | null>(null);
   const [file, setFile] = useState<File | null>(null);

   const { setJobId, pollStatus } = useTransactionsCreatePdf();

   const { data: portfolios } = usePortfolios();

   const { mutate, isPending } = useMutation({
      mutationFn: ({ file, pId }: { file: File; pId: string }) => useTransactionApi.createFromMmkPdf(file, pId),
      onSuccess: (data) => {
         setJobId(data.job_id);
         pollStatus(data.job_id);
         setFile(null);
         setPId(null);
         setOpen(false);
      },
   });

   function handleUpload(file: File, pId: string) {
      if (!file) return;
      if (!pId) return;

      if (file.type !== "application/pdf") {
         alert("Please select a PDF file.");
      }

      mutate({ file, pId });
   }

   if (!open) return null;

   return (
      <div
         onClick={() => setOpen(false)}
         className="fixed inset-0 z-50 flex items-center justify-center bg-[#070707]/80 backdrop-blur-sm"
      >
         <div
            onClick={(e) => e.stopPropagation()}
            className="w-1/4 h-1/2 min-w-[320px] min-h-[400px] flex flex-col justify-between bg-[#111213] border border-[#2e3033] rounded-lg p-5 shadow-2xl"
         >
            {/* Header */}
            <div>
               <h1 className="select-none text-xs font-semibold uppercase tracking-wider text-white mb-6">
                  Add Transaction{" "}
                  <span
                     className="text-[#00ff87] underline decoration-dotted cursor-help"
                     title="MMK Transaction Statement FOR PSX ONLY"
                  >
                     PDF
                  </span>
               </h1>

               <div className="space-y-4">
                  {/* Portfolio Dropdown */}
                  <div className="flex flex-col gap-1.5">
                     <label className="text-[10px] font-medium uppercase tracking-wider text-[#888888]">
                        Select Portfolio
                     </label>
                     <select
                        value={pId || ""}
                        onChange={(e) => setPId(e.target.value || null)}
                        className="w-full bg-[#161718] border border-[#2e3033] text-sm text-white rounded px-3 py-2 outline-none cursor-pointer focus:border-[#00ff87] transition-colors appearance-none"
                     >
                        <option value="" className="text-[#888888]">
                           Choose a portfolio...
                        </option>
                        {portfolios
                           ?.filter((p) => p.exchange === "PSX")
                           .map((p) => (
                              <option key={p.id} value={p.id} className="bg-[#161718]">
                                 {p.name}
                              </option>
                           ))}
                     </select>
                  </div>

                  {/* File Upload */}
                  <div className="flex flex-col gap-1.5">
                     <label className="text-[10px] font-medium uppercase tracking-wider text-[#888888]">
                        Statement File
                     </label>
                     <div className="relative flex items-center justify-center border border-dashed border-[#2e3033] hover:border-[#444444] rounded bg-[#1c1d1f] p-4 transition-colors group cursor-pointer">
                        <input
                           type="file"
                           onChange={(e) => setFile(e.target.files?.[0] || null)}
                           accept=".pdf"
                           className="absolute inset-0 opacity-0 cursor-pointer z-10"
                        />
                        <span className="text-xs text-[#a0a0a0] truncate group-hover:text-white transition-colors">
                           {file ? file.name : "Click to upload MMK PDF"}
                        </span>
                     </div>
                  </div>
               </div>
            </div>

            {/* Action Button */}
            <button
               disabled={!pId || !file || isPending}
               onClick={() => handleUpload(file!, pId!)}
               className="w-full bg-[#00ff87] hover:bg-[#00e074] disabled:bg-[#161718] text-black disabled:text-[#444444] font-medium text-xs uppercase tracking-wider py-2.5 rounded border border-transparent disabled:border-[#2e3033] transition-all duration-150 active:scale-[0.99]"
            >
               {isPending ? "Uploading..." : "Upload & Process"}
            </button>
         </div>
      </div>
   );
};

export default AddTransactionMmkModal;
