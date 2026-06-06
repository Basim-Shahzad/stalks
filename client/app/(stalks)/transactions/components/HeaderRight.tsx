"use client";

import { useState } from "react";
import { SlidersHorizontal, Plus } from "lucide-react";
import { Button, Popover, PopoverTrigger, PopoverContent } from "@heroui/react";
import FiltersModal from "./FiltersModal";
import { usePortfolios } from "@/lib/queries/portfolioQueries";
import { useTransactionFilters } from "@/lib/hooks/useTransactionFilters";

const ghostCls =
   "h-6 min-w-0 px-2.5 rounded bg-[#1c1d1f] border border-[#2e3033] text-[#a0a0a0] " +
   "hover:bg-[#222426] hover:text-white hover:border-[#3a3d40] uppercase gap-2 transition-all duration-100";

type HeaderRightProps = {
   setIsAddTransactionModalOpen: (open: boolean) => void;
}

const HeaderRight = ({ setIsAddTransactionModalOpen }: HeaderRightProps) => {
   const [isFilterModalOpen, setIsFilterModalOpen] = useState<boolean>(false);
   const { data: portfolios } = usePortfolios();
   const { filters, activeCount, setFilters, clearFilters } = useTransactionFilters();

   return (
      <div className="flex items-center gap-1.5">
         <Popover
            isOpen={isFilterModalOpen}
            onOpenChange={(open) => setIsFilterModalOpen(open)}
         >
            <PopoverTrigger>
               <Button variant="ghost" className={ghostCls}>
                  <SlidersHorizontal className="w-2.5 h-2.5 shrink-0" />
                  Filter
                  {activeCount > 0 && (
                     <span className="flex items-center justify-center w-3.5 h-3.5 rounded-full bg-[#00ff87] text-[#070707] text-[9px] font-bold leading-none">
                        {activeCount}
                     </span>
                  )}
               </Button>
            </PopoverTrigger>
            <PopoverContent className="bg-[#111213] border border-[#2e3033] p-0 rounded-xl shadow-none">
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

         <div className="w-px h-3.5 bg-[#2e3033] mx-0.5" />

         <Button
            variant="primary"
            className="h-6 min-w-0 px-2.5 rounded bg-[#00ff87] text-[#070707] hover:bg-[#00e87a] uppercase font-semibold gap-2 transition-all duration-100"
            onClick={() => setIsAddTransactionModalOpen(true)}
         >
            <Plus className="w-2.5 h-2.5 shrink-0" strokeWidth={2.5} />
            Add
         </Button>
      </div>
   );
};

export default HeaderRight;
