"use client";

import React, { useState, useMemo } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { usePortfolios } from "@/features/portfolios/hooks";
import { useTransactionApi } from "../api";
import { useTransactionsCreatePdf } from "../context/TransactionsCreatePdfContext";
import {
   Dialog,
   DialogContent,
   DialogHeader,
   DialogTitle,
   DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
   Select,
   SelectContent,
   SelectItem,
   SelectTrigger,
   SelectValue,
} from "@/components/ui/select";

export type StatementBroker = "AKD" | "MMK";

const BROKER_COPY: Record<
   StatementBroker,
   { title: string; description: string; placeholder: string }
> = {
   AKD: {
      title: "Add AKD Statement",
      description: "AKD transaction statement, for PSX portfolios only.",
      placeholder: "Click to upload AKD PDF",
   },
   MMK: {
      title: "Add MMK Statement",
      description: "MMK transaction statement, for PSX portfolios only.",
      placeholder: "Click to upload MMK PDF",
   },
};

type UploadStatementModalProps = {
   open: boolean;
   setOpen: (open: boolean) => void;
   broker: StatementBroker;
};

const UploadStatementModal: React.FC<UploadStatementModalProps> = ({
   open,
   setOpen,
   broker,
}) => {
   const [pId, setPId] = useState<string | null>(null);
   const [file, setFile] = useState<File | null>(null);

   const { setJobId, pollStatus } = useTransactionsCreatePdf();

   const { data: portfolios } = usePortfolios();
   const eligiblePortfolios = useMemo(
      () => portfolios?.filter((p) => p.exchange === "PSX"),
      [portfolios],
   );

   const { mutate, isPending } = useMutation({
      mutationFn: ({ file, pId }: { file: File; pId: string }) =>
         useTransactionApi.createFromPdf(file, pId),
      onSuccess: (data) => {
         setJobId(data.job_id);
         pollStatus(data.job_id);
         setFile(null);
         setPId(null);
         setOpen(false);
      },
      onError(err: any) {
         const serverMessage = err.response?.data?.detail;
         toast.error(serverMessage ?? "Failed to upload statement");
      },
   });

   function handleUpload(file: File, pId: string) {
      if (!file) return;
      if (!pId) return;

      if (file.type !== "application/pdf") {
         toast.error("Please select a PDF file.");
         return;
      }

      mutate({ file, pId });
   }

   const { title, description, placeholder } = BROKER_COPY[broker];

   return (
      <Dialog open={open} onOpenChange={setOpen}>
         <DialogContent className="bg-card border border-border rounded-xl shadow-2xl overflow-hidden text-foreground sm:max-w-md p-0">
            <DialogHeader className="pt-6 px-6 pb-3 border-b border-border">
               <DialogTitle className="text-lg font-semibold tracking-wide text-foreground">
                  {title}
               </DialogTitle>
               <p className="text-xs text-muted-foreground">{description}</p>
            </DialogHeader>

            <div className="px-6 py-5 gap-5 flex flex-col">
               <div className="flex flex-col gap-1.5">
                  <Label className="text-xs font-medium text-muted-foreground">
                     Portfolio
                  </Label>
                  <Select
                     value={pId ?? undefined}
                     onValueChange={(v) => v && setPId(v)}
                  >
                     <SelectTrigger className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-all w-full text-sm">
                        <SelectValue placeholder="Select a portfolio">
                           {(value: string) =>
                              eligiblePortfolios?.find((p) => p.id === value)
                                 ?.name ?? "Select a portfolio"
                           }
                        </SelectValue>
                     </SelectTrigger>
                     <SelectContent className="bg-muted border border-border rounded-lg shadow-xl">
                        {eligiblePortfolios?.map((p) => (
                           <SelectItem key={p.id} value={p.id}>
                              {p.name}
                           </SelectItem>
                        ))}
                     </SelectContent>
                  </Select>
               </div>

               <div className="flex flex-col gap-1.5">
                  <Label className="text-xs font-medium text-muted-foreground">
                     Statement File
                  </Label>
                  <div className="relative flex items-center justify-center border border-dashed border-border hover:border-muted-foreground/40 rounded-lg bg-muted p-4 transition-colors group cursor-pointer">
                     <input
                        type="file"
                        onChange={(e) => setFile(e.target.files?.[0] || null)}
                        accept=".pdf"
                        className="absolute inset-0 opacity-0 cursor-pointer z-10"
                     />
                     <span className="text-xs text-muted-foreground truncate group-hover:text-foreground transition-colors">
                        {file ? file.name : placeholder}
                     </span>
                  </div>
               </div>
            </div>

            <DialogFooter className="px-6 pb-6">
               <Button
                  disabled={!pId || !file || isPending}
                  onClick={() => handleUpload(file!, pId!)}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6 h-9 rounded-lg transition-colors text-sm shadow-md active:scale-[0.98]"
               >
                  {isPending ? "Uploading..." : "Upload & Process"}
               </Button>
            </DialogFooter>
         </DialogContent>
      </Dialog>
   );
};

export default UploadStatementModal;
