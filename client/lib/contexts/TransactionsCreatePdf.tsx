"use client";

import React, { createContext, useContext, useState, ReactNode, useEffect } from "react";
import api from "@/services/api.service";
import { toast } from "sonner";
import { queryClient } from "@/app/providers";

interface TransactionsCreatePdfContextType {
   jobId: any;
   setJobId: React.Dispatch<React.SetStateAction<any>>;
   status: any;
   setStatus: React.Dispatch<React.SetStateAction<any>>;
   pollStatus: (jobId: string) => Promise<void>;
}

export type JobStatus = "PENDING" | "IN_PROGRESS" | "COMPLETED" | "FAILED";

const TransactionsCreatePdfContext = createContext<TransactionsCreatePdfContextType | undefined>(undefined);

export function TransactionsCreatePdfProvider({ children }: { children: ReactNode }) {
   const [jobId, setJobId] = useState<any>(null);
   const [status, setStatus] = useState<any>(null);

   async function pollStatus(jobId: string): Promise<void> {
      return new Promise((resolve, reject) => {
         const interval = setInterval(async () => {
            try {
               const res = await api.get(`/jobs/status/${jobId}`);
               const data = res.data;

               setStatus(data.status);

               if (data.status === "COMPLETED") {
                  clearInterval(interval);
                  queryClient.invalidateQueries({ queryKey: ["transactions"] });
                  resolve();
               } else if (data.status === "FAILED") {
                  clearInterval(interval);
                  reject(new Error(data.error_message || "Job failed"));
               }
            } catch (err) {
               clearInterval(interval);
               reject(err);
            }
         }, 2000);
      });
   }

   useEffect(() => {
      if (jobId !== null) {
         toast.promise(pollStatus(jobId), {
            error: "Failed to process file",
            loading: "Processing file...",
            success: "Transactions created successfully!",
         });
      }
   }, [jobId]);

   return (
      <TransactionsCreatePdfContext.Provider value={{ jobId, setJobId, status, setStatus, pollStatus }}>
         {children}
      </TransactionsCreatePdfContext.Provider>
   );
}

export function useTransactionsCreatePdf() {
   const context = useContext(TransactionsCreatePdfContext);
   if (context === undefined) {
      throw new Error("useTransactionsCreatePdf must be used within a TransactionsCreatePdfProvider");
   }
   return context;
}
