"use client";

import { useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { toast } from "sonner";
import { Transaction, TransactionSide } from "../types";
import { usePortfolios } from "@/features/portfolios/hooks";
import { queryClient } from "@/app/providers";
import { useTransactionApi } from "../api";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
   Select,
   SelectContent,
   SelectItem,
   SelectTrigger,
   SelectValue,
} from "@/components/ui/select";

export default function AddTransactionsModal({
   isOpen,
   onOpenChange,
   portfolioId,
}: {
   isOpen: boolean;
   onOpenChange: (open: boolean) => void;
   portfolioId?: string;
}) {
   const [data, setData] = useState<Partial<Transaction>>({
      side: "BUY",
      transactionDate: new Date().toISOString().split("T")[0],
      symbol: "",
      quantity: undefined,
      rate: undefined,
      commission: undefined,
      taxes: undefined,
      charges: undefined,
   });

   const { data: portfolios } = usePortfolios();
   const [pId, setPId] = useState<string>(portfolioId ?? portfolios?.[0]?.id ?? "");
   const [selectedType, setSelectedType] = useState<TransactionSide>("BUY");

   const { mutate: createTransaction, isPending } = useMutation({
      mutationFn: () => {
         return useTransactionApi.create(data, pId ?? "");
      },
      onSuccess() {
         toast.success("Transaction created successfully");
         queryClient.invalidateQueries({ queryKey: ["transactions"] });
      },
      onError(err: any) {
         const serverMessage = err.response?.data?.detail;
         toast.error(serverMessage ?? "Failed to create transaction");
      },
   });

   const transactionSides: TransactionSide[] = useMemo(
      () => ["BUY", "SELL", "DEPOSIT", "WITHDRAW", "INCOME", "FEE"],
      [],
   );

   const isPositiveSide = (side: TransactionSide) => ["BUY", "DEPOSIT", "INCOME"].includes(side);

   const getChipStyles = (side: TransactionSide, isSelected: boolean) => {
      const activeBase = "border-2 opacity-100 scale-102 shadow-[0_0_12px_color-mix(in_srgb,var(--primary)_15%,transparent)]";
      const inactiveBase = "opacity-50 hover:opacity-90 scale-100 border border-border";

      if (isSelected) {
         return `${activeBase} bg-card border-primary text-primary`;
      }

      return isPositiveSide(side) ? `${inactiveBase} text-positive bg-card` : `${inactiveBase} text-negative bg-card`;
   };

   return (
      <Dialog open={isOpen} onOpenChange={onOpenChange}>
         <DialogContent className="bg-card border border-border rounded-xl shadow-2xl overflow-hidden text-foreground sm:max-w-md p-0">
            <DialogHeader className="pt-6 px-6 pb-3 border-b border-border">
               <DialogTitle className="text-lg font-semibold tracking-wide text-foreground">
                  Create a Transaction
               </DialogTitle>
            </DialogHeader>

            <div className="px-6 py-5 gap-5 flex flex-col overflow-y-auto max-h-[70vh] scrollbar-none [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
               <div className="flex flex-col gap-1.5">
                  <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                     Transaction Type
                  </span>
                  <div className="flex flex-wrap gap-2 p-1.5 bg-muted rounded-lg border border-border justify-start">
                     {transactionSides.map((side) => (
                        <button
                           type="button"
                           key={side}
                           className={`cursor-pointer font-bold text-[11px] tracking-wider transition-all duration-150 px-2.5 h-7 rounded-md ${getChipStyles(side, selectedType === side)}`}
                           onClick={() => {
                              setSelectedType(side);
                              setData({ ...data, side });
                           }}
                        >
                           {side}
                        </button>
                     ))}
                  </div>
               </div>

               {/* Core Matrix Grid */}
               <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="flex flex-col gap-1.5">
                     <Label htmlFor="tx-date" className="text-xs font-medium text-muted-foreground">
                        Transaction Date
                     </Label>
                     <Input
                        id="tx-date"
                        className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full text-sm"
                        type="date"
                        value={data.transactionDate}
                        onChange={(e) => setData({ ...data, transactionDate: e.target.value })}
                     />
                  </div>

                  <div className="flex flex-col gap-1.5">
                     <Label htmlFor="company-symbol" className="text-xs font-medium text-muted-foreground">
                        Company Symbol
                     </Label>
                     <Input
                        id="company-symbol"
                        className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full text-sm uppercase"
                        placeholder="e.g. AAPL"
                        value={data.symbol}
                        onChange={(e) => setData({ ...data, symbol: e.target.value.toUpperCase() })}
                     />
                  </div>
               </div>

               {/* Portfolio Select */}
               <div className="flex flex-col gap-1.5">
                  <Label className="text-xs font-medium text-muted-foreground">Portfolio</Label>
                  <Select value={portfolioId ?? pId} onValueChange={(v) => v && setPId(v)}>
                     <SelectTrigger className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground focus:border-primary transition-all w-full text-sm">
                        <SelectValue placeholder="Select a portfolio" />
                     </SelectTrigger>
                     <SelectContent className="bg-muted border border-border rounded-lg shadow-xl">
                        {portfolios?.map((p) => (
                           <SelectItem key={p.id} value={p.id}>
                              {p.name}
                           </SelectItem>
                        ))}
                     </SelectContent>
                  </Select>
               </div>

               <div className="grid grid-cols-2 gap-4 border-t border-border pt-4">
                  <div className="flex flex-col gap-1.5">
                     <Label className="text-xs font-medium text-muted-foreground">Quantity</Label>
                     <Input
                        className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full text-sm"
                        type="number"
                        placeholder="0.00"
                        value={data.quantity ?? ""}
                        onChange={(e) =>
                           setData({ ...data, quantity: e.target.value ? Number(e.target.value) : undefined })
                        }
                     />
                  </div>
                  <div className="flex flex-col gap-1.5">
                     <Label className="text-xs font-medium text-muted-foreground">Rate</Label>
                     <Input
                        className="bg-muted border border-border rounded-lg px-3 py-2 text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full text-sm"
                        type="number"
                        placeholder="0.00"
                        value={data.rate ?? ""}
                        onChange={(e) => setData({ ...data, rate: e.target.value ? Number(e.target.value) : undefined })}
                     />
                  </div>
               </div>

               <div className="grid grid-cols-3 gap-3 border-t border-border pt-4">
                  <div className="flex flex-col gap-1.5">
                     <Label className="text-[11px] font-medium text-muted-foreground">Commission</Label>
                     <Input
                        className="bg-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full"
                        type="number"
                        placeholder="0"
                        value={data.commission ?? ""}
                        onChange={(e) =>
                           setData({ ...data, commission: e.target.value ? Number(e.target.value) : undefined })
                        }
                     />
                  </div>
                  <div className="flex flex-col gap-1.5">
                     <Label className="text-[11px] font-medium text-muted-foreground">Taxes</Label>
                     <Input
                        className="bg-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full"
                        type="number"
                        placeholder="0"
                        value={data.taxes ?? ""}
                        onChange={(e) => setData({ ...data, taxes: e.target.value ? Number(e.target.value) : undefined })}
                     />
                  </div>
                  <div className="flex flex-col gap-1.5">
                     <Label className="text-[11px] font-medium text-muted-foreground">Charges</Label>
                     <Input
                        className="bg-muted border border-border rounded-lg px-2.5 py-1.5 text-xs text-foreground placeholder:text-muted-foreground/60 focus-visible:border-primary focus-visible:ring-primary/20 transition-all outline-none w-full"
                        type="number"
                        placeholder="0"
                        value={data.charges ?? ""}
                        onChange={(e) =>
                           setData({ ...data, charges: e.target.value ? Number(e.target.value) : undefined })
                        }
                     />
                  </div>
               </div>
            </div>

            <DialogFooter className="px-6 pb-6">
               <Button
                  onClick={() => createTransaction()}
                  disabled={isPending}
                  className="bg-primary hover:bg-primary/90 text-primary-foreground font-semibold px-6 h-9 rounded-lg transition-colors text-sm shadow-md active:scale-[0.98]"
               >
                  {isPending ? "Adding..." : "Add Transaction"}
               </Button>
            </DialogFooter>
         </DialogContent>
      </Dialog>
   );
}
