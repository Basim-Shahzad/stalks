"use client";

import { useState, useEffect } from "react";
import { Search, Bell, Plus, ChevronDown, Menu } from "lucide-react";

type HeaderProps = {
   title: string;
};

const Header: React.FC<HeaderProps> = ({ title }) => {
   return (
      <header className="w-full px-8 py-4 flex items-center justify-between border-b border-b-white/5">
         <h1 className="text-xl" >{title}</h1>
         <div className="flex items-center gap-2">
            <Plus className="text-white/50 hover:text-white cursor-pointer w-5" />
         </div>
      </header>
   );
};

export default Header;
