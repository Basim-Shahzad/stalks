"use client";

import { useState, useRef, useEffect } from "react";
import { Plus, ChevronDown } from "lucide-react";

type DropdownButtonProps = {
   label: string;
   items: { label: string; onClick: () => void }[];
   onClick: (b: boolean) => void;
   size?: number;
};

export function DropdownButton({ label, items, onClick }: DropdownButtonProps) {
   const [open, setOpen] = useState(false);
   const ref = useRef<HTMLDivElement>(null);

   useEffect(() => {
      const handler = (e: MouseEvent) => {
         if (ref.current && !ref.current.contains(e.target as Node)) {
            setOpen(false);
         }
      };
      document.addEventListener("mousedown", handler);
      return () => document.removeEventListener("mousedown", handler);
   }, []);

   return (
      <div ref={ref} className="relative flex items-center">
         <div className="flex items-center cursor-pointer bg-[#00ff87] text-[#070707] h-6 rounded uppercase font-semibold transition-all duration-100">
            <button className="flex items-center gap-1 px-2 h-full cursor-pointer" onClick={() => onClick(true)}>
               <Plus className="w-3 h-3 shrink-0" />
               {label}
            </button>

            <div className="w-px h-4 bg-[#070707]/20" />

            <button className="flex items-center px-1 h-full cursor-pointer" onClick={() => setOpen((v) => !v)}>
               <ChevronDown className="w-3 h-3 shrink-0" />
            </button>
         </div>

         {open && (
            <div className="absolute top-full left-[-100] mt-2 min-w-full text-[#00ff87] bg-[#070707] rounded shadow-lg z-50 overflow-hidden">
               {items.map((item, i) => (
                  <button
                     key={i}
                     className="flex w-full items-center px-4 py-2 text-xs uppercase font-semibold whitespace-nowrap cursor-pointer hover:bg-[#00ff87]/10 transition-all duration-100"
                     onClick={() => {
                        item.onClick();
                        setOpen(false);
                     }}
                  >
                     {item.label}
                  </button>
               ))}
            </div>
         )}
      </div>
   );
}
