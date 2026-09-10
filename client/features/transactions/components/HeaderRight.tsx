"use client";

import { useState } from "react";
import { SlidersHorizontal } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Popover, PopoverTrigger, PopoverContent } from "@/components/ui/popover";
import FiltersModal from "./FiltersModal";
import { usePortfolios } from "@/features/portfolios/hooks";
import { useTransactionFilters } from "../hooks/useTransactionFilters";
import { DropdownButton } from "./action-menu";
import AddTransactionMmkModal from "./AddTransactionMmkModal";

const ghostCls =
   "h-6 min-w-0 px-2.5 rounded bg-secondary border border-border text-muted-foreground " +
   "hover:bg-accent hover:text-foreground hover:border-border uppercase gap-2 transition-all duration-100";

type HeaderRightProps = {
   setIsAddTransactionModalOpen: (open: boolean) => void;
};

const HeaderRight = ({ setIsAddTransactionModalOpen }: HeaderRightProps) => {
   const [isFilterModalOpen, setIsFilterModalOpen] = useState<boolean>(false);
   const [isCreateTransactionMmkModalOpen, setIsCreateTransactionMmkModalOpen] = useState<boolean>(false);
   const { data: portfolios } = usePortfolios();
   const { filters, activeCount, setFilters, clearFilters } = useTransactionFilters();

  

   return (
      <div className="flex items-center gap-1.5">
         <Popover open={isFilterModalOpen} onOpenChange={(open) => setIsFilterModalOpen(open)}>
            <PopoverTrigger render={<Button variant="ghost" className={ghostCls} />}>
               <SlidersHorizontal className="w-2.5 h-2.5 shrink-0" />
               Filter
               {activeCount > 0 && (
                  <span className="flex items-center justify-center w-3.5 h-3.5 rounded-full bg-primary text-primary-foreground text-[9px] font-bold leading-none">
                     {activeCount}
                  </span>
               )}
            </PopoverTrigger>
            <PopoverContent className="bg-card border border-border p-0 rounded-xl shadow-none w-auto">
               <FiltersModal
                  portfolios={portfolios ?? []}
                  filters={filters}
                  onApply={(f) => {
                     setFilters(f);
                     setIsFilterModalOpen(false);
                  }}
                  onClear={clearFilters}
                  onClose={() => setIsFilterModalOpen(false)}
               />
            </PopoverContent>
         </Popover>

         <div className="w-px h-3.5 bg-border mx-0.5" />

         <DropdownButton
            label="Add"
            onClick={setIsAddTransactionModalOpen}
            items={[
               { label: "Add MMK Transactions PDF", onClick: () => setIsCreateTransactionMmkModalOpen(true) },
               { label: "Add Transactions CSV", onClick: () => console.log("PDF") },
            ]}
         />

         {isCreateTransactionMmkModalOpen && (
            <AddTransactionMmkModal
               open={isCreateTransactionMmkModalOpen}
               setOpen={setIsCreateTransactionMmkModalOpen}
            />
         )}
      </div>
   );
};

export default HeaderRight;
