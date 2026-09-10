"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import {
   Dialog,
   DialogClose,
   DialogContent,
   DialogFooter,
   DialogHeader,
   DialogTitle,
} from "@/components/ui/dialog";
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
import { queryClient } from "@/app/providers";
import { useCreatePortfolio } from "../hooks";
import { Portfolio } from "../types";

const EXCHANGES: Portfolio["exchange"][] = ["PSX"];
const CURRENCIES: Portfolio["currency"][] = ["PKR"];
const BROKERS: Portfolio["broker"][] = ["AKD", "MMK"];

const initialForm: Partial<Portfolio> = {
   name: "",
   description: "",
   exchange: "PSX",
   currency: "PKR",
   broker: undefined,
};

const PortfolioCreateForm = () => {
   const [open, setOpen] = useState(false);
   const [form, setForm] = useState<Partial<Portfolio>>(initialForm);
   const {
      mutate: createPortfolio,
      isPending,
      error,
      reset,
   } = useCreatePortfolio();

   const handleOpenChange = (nextOpen: boolean) => {
      setOpen(nextOpen);
      if (!nextOpen) {
         setForm(initialForm);
         reset();
      }
   };

   const handleSubmit = (e: React.FormEvent) => {
      e.preventDefault();
      if (!form.name?.trim() || !form.broker) return;

      createPortfolio(form, {
         onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["portfolios"] });
            handleOpenChange(false);
         },
      });
   };

   return (
      <Dialog open={open} onOpenChange={handleOpenChange}>
         <Button
            variant="ghost"
            size="icon"
            onClick={() => handleOpenChange(true)}
            aria-label="Create portfolio"
         >
            <Plus className="w-5 h-5 opacity-75 hover:opacity-100 transition-opacity duration-200" />
         </Button>
         <DialogContent>
            <DialogHeader>
               <DialogTitle>Create Portfolio</DialogTitle>
            </DialogHeader>

            <form onSubmit={handleSubmit} className="flex flex-col gap-4">
               <div className="flex flex-col gap-1.5">
                  <Label htmlFor="portfolio-name">Name</Label>
                  <Input
                     id="portfolio-name"
                     placeholder="e.g. Retirement Fund"
                     value={form.name ?? ""}
                     onChange={(e) =>
                        setForm((f) => ({ ...f, name: e.target.value }))
                     }
                     autoFocus
                     required
                  />
               </div>

               <div className="flex flex-col gap-1.5">
                  <Label htmlFor="portfolio-description">Description</Label>
                  <Input
                     id="portfolio-description"
                     placeholder="Optional description"
                     value={form.description ?? ""}
                     onChange={(e) =>
                        setForm((f) => ({ ...f, description: e.target.value }))
                     }
                  />
               </div>

               <div className="grid grid-cols-3 gap-3">
                  <div className="flex flex-col gap-1.5">
                     <Label>Exchange</Label>
                     <Select
                        value={form.exchange}
                        onValueChange={(value) =>
                           setForm((f) => ({
                              ...f,
                              exchange: value as Portfolio["exchange"],
                           }))
                        }
                     >
                        <SelectTrigger className="w-full">
                           <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                           {EXCHANGES.map((exchange) => (
                              <SelectItem key={exchange} value={exchange}>
                                 {exchange}
                              </SelectItem>
                           ))}
                        </SelectContent>
                     </Select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                     <Label>Currency</Label>
                     <Select
                        value={form.currency}
                        onValueChange={(value) =>
                           setForm((f) => ({
                              ...f,
                              currency: value as Portfolio["currency"],
                           }))
                        }
                     >
                        <SelectTrigger className="w-full">
                           <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                           {CURRENCIES.map((currency) => (
                              <SelectItem key={currency} value={currency}>
                                 {currency}
                              </SelectItem>
                           ))}
                        </SelectContent>
                     </Select>
                  </div>

                  <div className="flex flex-col gap-1.5">
                     <Label>Broker</Label>
                     <Select
                        value={form.broker}
                        onValueChange={(value) =>
                           setForm((f) => ({
                              ...f,
                              broker: value as Portfolio["broker"],
                           }))
                        }
                     >
                        <SelectTrigger className="w-full">
                           <SelectValue placeholder="Select" />
                        </SelectTrigger>
                        <SelectContent>
                           {BROKERS.map((broker) => (
                              <SelectItem key={broker} value={broker}>
                                 {broker}
                              </SelectItem>
                           ))}
                        </SelectContent>
                     </Select>
                  </div>
               </div>

               {error && (
                  <p className="text-sm text-destructive">
                     Failed to create portfolio. Please try again.
                  </p>
               )}

               <DialogFooter>
                  <DialogClose
                     render={<Button type="button" variant="outline" />}
                  >
                     Cancel
                  </DialogClose>
                  <Button
                     type="submit"
                     disabled={isPending || !form.name?.trim() || !form.broker}
                  >
                     {isPending ? "Creating..." : "Create Portfolio"}
                  </Button>
               </DialogFooter>
            </form>
         </DialogContent>
      </Dialog>
   );
};

export default PortfolioCreateForm;
