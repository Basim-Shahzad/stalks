"use client";

import {
   Dialog,
   DialogContent,
   DialogHeader,
   DialogTitle,
   DialogTrigger,
} from "@/components/ui/dialog";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import type { Table } from "@tanstack/react-table";
import type { Transaction } from "../types";

const COLUMN_LABELS: Record<string, string> = {
   transactionDate: "Date",
   symbol: "Symbol",
   company: "Company",
   side: "Side",
   quantity: "Qty",
   rate: "Rate",
   commission: "Commission",
   totalAmount: "Total",
};

interface ColumnsMenuProps {
   table: Table<Transaction>;
}

export const ColumnsMenu = ({ table }: ColumnsMenuProps) => {
   return (
      <Dialog>
         <DialogTrigger>
            <Button
               variant="outline"
               size="sm"
               className="h-auto rounded-md border-[0.5px] border-[var(--border)] px-2.5 py-[3px] text-[10px] font-medium tracking-[0.08em] text-[var(--foreground)]"
            >
               COLUMNS
            </Button>
         </DialogTrigger>

         <DialogContent className="min-w-[160px] max-w-xs rounded-[10px] border-[0.5px] border-[var(--border)] bg-[var(--card)] p-2 shadow-[0_8px_24px_rgba(0,0,0,0.5)]">
            <DialogHeader>
               <DialogTitle className="border-b-[0.5px] border-[var(--border-subtle)] px-2 pb-2 pt-1 text-[9px] font-normal tracking-[0.12em] text-[var(--foreground)] opacity-70">
                  TOGGLE COLUMNS
               </DialogTitle>
            </DialogHeader>

            {table.getAllLeafColumns().map((col) => (
               <Label
                  key={col.id}
                  htmlFor={`column-${col.id}`}
                  className={`flex cursor-pointer items-center gap-2 rounded-md px-2 py-[5px] text-[12px] font-normal transition-colors duration-100 ease-in-out hover:bg-[var(--border-subtle)] ${
                     col.getIsVisible()
                        ? "text-[var(--foreground)]"
                        : "text-[var(--muted-foreground)]"
                  }`}
               >
                  <Checkbox
                     id={`column-${col.id}`}
                     checked={col.getIsVisible()}
                     onCheckedChange={(checked) =>
                        col.toggleVisibility(Boolean(checked))
                     }
                     className="h-3 w-3 data-[state=checked]:bg-[var(--primary)] data-[state=checked]:border-[var(--primary)]"
                  />
                  {COLUMN_LABELS[col.id] ?? col.id}
               </Label>
            ))}
         </DialogContent>
      </Dialog>
   );
};
