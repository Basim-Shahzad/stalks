import React, { useState } from "react";
import { Link } from "react-router-dom";
import Settings from "./Settings";
import { useDisclosure } from "@mantine/hooks";

const Navbar = () => {
   const [isSettingsOpen, setIsSettingsOpen] = useState<boolean>(false);
   const [opened, { open, close }] = useDisclosure(false);

   return (
      <nav className="w-full h-16 border-b border-slate-200 bg-white/80 backdrop-blur-md flex items-center px-8 justify-between sticky top-0 z-50">
         <Link to={"/"} className="text-slate-900 font-bold tracking-tight text-lg">
            Atif Shahzad <span className="text-indigo-600">Stock Portfolio</span>
         </Link>
         <div className="flex gap-10 text-sm font-semibold text-slate-500">
            <Link to="stocks" className="hover:text-indigo-600 transition-colors">
               Stocks
            </Link>
            <Link to="portfolio" className="hover:text-indigo-600 transition-colors">
               Portfolio
            </Link>
            <Link to="transactions" className="hover:text-indigo-600 transition-colors">
               Transactions
            </Link>
         </div>
         <button
            onClick={open}
            className="text-white flex items-center gap-2 text-sm font-bold rounded-lg transition-all">
            <svg
               xmlns="http://www.w3.org/2000/svg"
               width="28"
               height="28"
               viewBox="0 0 24 24"
               fill="none"
               stroke="currentColor"
               strokeWidth="2"
               strokeLinecap="round"
               strokeLinejoin="round"
               className="lucide hover:fill-[#4F39F6] cursor-pointer text-[#4F39F6] lucide-settings-icon lucide-settings">
               <path d="M9.671 4.136a2.34 2.34 0 0 1 4.659 0 2.34 2.34 0 0 0 3.319 1.915 2.34 2.34 0 0 1 2.33 4.033 2.34 2.34 0 0 0 0 3.831 2.34 2.34 0 0 1-2.33 4.033 2.34 2.34 0 0 0-3.319 1.915 2.34 2.34 0 0 1-4.659 0 2.34 2.34 0 0 0-3.32-1.915 2.34 2.34 0 0 1-2.33-4.033 2.34 2.34 0 0 0 0-3.831A2.34 2.34 0 0 1 6.35 6.051a2.34 2.34 0 0 0 3.319-1.915" />
               <circle cx="12" cy="12" r="3" />
            </svg>
         </button>

         <Settings opened={opened} close={close} />
      </nav>
   );
};

export default Navbar;
