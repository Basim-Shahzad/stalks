"use client";

import { Plus, ChevronDown } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
   DropdownMenu,
   DropdownMenuContent,
   DropdownMenuItem,
   DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "cn";

type DropdownButtonProps = {
   label: string;
   items: { label: string; onClick: () => void; disabled?: boolean }[];
   onClick: () => void;
   className?: string;
};

export function DropdownButton({ label, items, onClick, className }: DropdownButtonProps) {
   return (
      <div className="flex items-center rounded-lg">
         <Button
            className={cn("rounded-r-none pr-2.5", className)}
            onClick={onClick}
         >
            <Plus className="size-3.5" />
            {label}
         </Button>

         <div className="self-stretch bg-primary-foreground/20" />

         <DropdownMenu>
            <DropdownMenuTrigger
               render={
                  <Button
                     className={cn("rounded-l-none px-1.5", className)}
                     aria-label="More add options"
                  />
               }
            >
               <ChevronDown className="size-3.5" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="bg-primary w-max text-black" >
               {items.map((item) => (
                  <DropdownMenuItem
                     key={item.label}
                     disabled={item.disabled}
                     onClick={item.onClick}
                     className=""
                  >
                     {item.label}
                  </DropdownMenuItem>
               ))}
            </DropdownMenuContent>
         </DropdownMenu>
      </div>
   );
}
