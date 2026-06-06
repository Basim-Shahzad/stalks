"use client";

import { useEffect, useMemo, useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { Transaction, TransactionSide } from "@/types/transactions.types";
import { usePortfolios } from "@/lib/queries/portfolioQueries";
import { queryClient } from "@/app/providers";
import { useTransactionApi } from "@/hooks/useTransactionApi";
import { Modal, Button, Input, Label, Select, ListBox, Chip, toast, type Key } from "@heroui/react";

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
   const [pId, setPId] = useState<Key | null>(portfolioId ?? portfolios?.[0]?.id ?? "");
   const [selectedType, setSelectedType] = useState<TransactionSide>("BUY");

   const { mutate: createTransaction, isPending } = useMutation({
      mutationFn: () => {
         return useTransactionApi.create(data, pId?.toString() ?? "");
      },
      onSuccess(data) {
         toast.success("Transaction created successfully");
         queryClient.invalidateQueries({ queryKey: ["transactions"] });
      },
      onError(err: any) {
         const serverMessage = err.response?.data?.detail;
         toast.danger(serverMessage ?? "Failed to create transaction");
      }
   })

   const transactionSides: TransactionSide[] = useMemo(
      () => ["BUY", "SELL", "DEPOSIT", "WITHDRAW", "INCOME", "FEE"],
      [],
   );

   // Custom theme active matching
   const getChipStyles = (side: TransactionSide, isSelected: boolean) => {
      const activeBase = "border-2 opacity-100 scale-102 shadow-[0_0_12px_rgba(0,255,135,0.15)]";
      const inactiveBase = "opacity-50 hover:opacity-90 scale-100 border border-[#2e3033]";

      const isPositive = ["BUY", "DEPOSIT", "INCOME"].includes(side);

      if (isSelected) {
         return `${activeBase} bg-[#161718] border-[#00ff87] text-[#00ff87]`;
      }

      return isPositive ? `${inactiveBase} text-green-500 bg-[#111213]` : `${inactiveBase} text-red-400 bg-[#111213]`;
   };

   return (
      <Modal.Backdrop isOpen={isOpen} onOpenChange={onOpenChange}>
         <Modal.Container size="md">
            <Modal.Dialog className="bg-[#070707] border border-[#2e3033] rounded-xl shadow-2xl overflow-hidden text-white">
               <Modal.CloseTrigger className="absolute right-4 top-4 text-[#888888] hover:text-white transition-colors" />

               <Modal.Header className="pt-6 px-6 pb-3 border-b border-[#2e3033]">
                  <Modal.Heading className="text-lg font-semibold tracking-wide text-white">
                     Create a Transaction
                  </Modal.Heading>
               </Modal.Header>

               <Modal.Body className="px-6 py-5 gap-5 flex flex-col overflow-y-auto scrollbar-none [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
                  <div className="flex flex-col gap-1.5">
                     <span className="text-xs font-semibold text-[#888888] uppercase tracking-wider">
                        Transaction Type
                     </span>
                     <div className="flex flex-wrap gap-2 p-1.5 bg-[#111213] rounded-lg border border-[#2e3033] justify-start">
                        {transactionSides.map((side) => (
                           <Chip
                              className={`cursor-pointer font-bold text-[11px] tracking-wider transition-all duration-150 px-2.5 h-7 rounded-md ${getChipStyles(side, selectedType === side)}`}
                              key={side}
                              onClick={() => {
                                 setSelectedType(side);
                                 setData({ ...data, side });
                              }}
                           >
                              {side}
                           </Chip>
                        ))}
                     </div>
                  </div>

                  {/* Core Matrix Grid */}
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                     <div className="flex flex-col gap-1.5">
                        <Label htmlFor="tx-date" className="text-xs font-medium text-[#a0a0a0]">
                           Transaction Date
                        </Label>
                        <Input
                           id="tx-date"
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-3 py-2 text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full text-sm"
                           type="date"
                           value={data.transactionDate}
                           onChange={(e) => setData({ ...data, transactionDate: e.target.value })}
                        />
                     </div>

                     <div className="flex flex-col gap-1.5">
                        <Label htmlFor="company-symbol" className="text-xs font-medium text-[#a0a0a0]">
                           Company Symbol
                        </Label>
                        <Input
                           id="company-symbol"
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-3 py-2 text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full text-sm uppercase"
                           placeholder="e.g. AAPL"
                           value={data.symbol}
                           onChange={(e) => setData({ ...data, symbol: e.target.value.toUpperCase() })}
                        />
                     </div>
                  </div>

                  {/* Portfolio Select */}
                  <div className="flex flex-col gap-1.5">
                     <Select
                        className="w-full"
                        placeholder="Select a portfolio"
                        value={portfolioId ?? pId}
                        onChange={(e) => setPId(e)}
                     >
                        <Label className="text-xs font-medium text-[#a0a0a0]">Portfolio</Label>
                        <Select.Trigger className="bg-[#111213] border border-[#2e3033] rounded-lg px-3 py-2 text-white focus:border-[#00ff87] transition-all flex items-center justify-between w-full text-sm">
                           <Select.Value className="text-[#a0a0a0]" />
                           <Select.Indicator className="text-[#888888]" />
                        </Select.Trigger>
                        <Select.Popover className="bg-[#111213] border border-[#2e3033] rounded-lg shadow-xl p-1 mt-1">
                           <ListBox className="gap-0.5">
                              {portfolios &&
                                 portfolios?.map((p) => (
                                    <ListBox.Item
                                       key={p.id}
                                       id={p.id}
                                       textValue={p.name}
                                       className="px-3 py-2 rounded-md text-[#a0a0a0] hover:bg-[#1c1d1f] hover:text-white cursor-pointer transition-colors flex items-center justify-between text-sm"
                                    >
                                       {p.name}
                                       <ListBox.ItemIndicator className="text-[#00ff87]" />
                                    </ListBox.Item>
                                 ))}
                           </ListBox>
                        </Select.Popover>
                     </Select>
                  </div>

                  <div className="grid grid-cols-2 gap-4 border-t border-[#2e3033] pt-4">
                     <div className="flex flex-col gap-1.5">
                        <Label className="text-xs font-medium text-[#a0a0a0]">Quantity</Label>
                        <Input
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-3 py-2 text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full text-sm"
                           type="number"
                           placeholder="0.00"
                           value={data.quantity ?? ""}
                           onChange={(e) =>
                              setData({ ...data, quantity: e.target.value ? Number(e.target.value) : undefined })
                           }
                        />
                     </div>
                     <div className="flex flex-col gap-1.5">
                        <Label className="text-xs font-medium text-[#a0a0a0]">Rate</Label>
                        <Input
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-3 py-2 text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full text-sm"
                           type="number"
                           placeholder="0.00"
                           value={data.rate ?? ""}
                           onChange={(e) =>
                              setData({ ...data, rate: e.target.value ? Number(e.target.value) : undefined })
                           }
                        />
                     </div>
                  </div>

                  <div className="grid grid-cols-3 gap-3 border-t border-[#2e3033] pt-4">
                     <div className="flex flex-col gap-1.5">
                        <Label className="text-[11px] font-medium text-[#888888]">Commission</Label>
                        <Input
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full"
                           type="number"
                           placeholder="0"
                           value={data.commission ?? ""}
                           onChange={(e) =>
                              setData({ ...data, commission: e.target.value ? Number(e.target.value) : undefined })
                           }
                        />
                     </div>
                     <div className="flex flex-col gap-1.5">
                        <Label className="text-[11px] font-medium text-[#888888]">Taxes</Label>
                        <Input
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full"
                           type="number"
                           placeholder="0"
                           value={data.taxes ?? ""}
                           onChange={(e) =>
                              setData({ ...data, taxes: e.target.value ? Number(e.target.value) : undefined })
                           }
                        />
                     </div>
                     <div className="flex flex-col gap-1.5">
                        <Label className="text-[11px] font-medium text-[#888888]">Charges</Label>
                        <Input
                           className="bg-[#111213] border border-[#2e3033] rounded-lg px-2.5 py-1.5 text-xs text-white placeholder-[#444444] focus-within:border-[#00ff87] focus:ring-green-500/20 transition-all outline-none w-full"
                           type="number"
                           placeholder="0"
                           value={data.charges ?? ""}
                           onChange={(e) =>
                              setData({ ...data, charges: e.target.value ? Number(e.target.value) : undefined })
                           }
                        />
                     </div>
                  </div>
               </Modal.Body>

               <Modal.Footer className="">
                  <Button
                     slot="close"
                     onClick={() => createTransaction()}
                     className="bg-[#00ff87] hover:bg-[#00e176] text-[#070707] font-semibold px-6 h-9 rounded-lg transition-colors text-sm shadow-md active:scale-[0.98]"
                  >
                     {isPending ? "Adding..." : "Add Transaction"}
                  </Button>
               </Modal.Footer>
            </Modal.Dialog>
         </Modal.Container>
      </Modal.Backdrop>
   );
}
