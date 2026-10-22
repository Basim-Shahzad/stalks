"use client";

import { useState, useRef } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useAuthStore } from "@/features/auth/store";
import ProductMegaMenu from "./ProductMegaMenu";

const NAV_ITEMS = [
   { label: "Product", isMega: true },
   { label: "Pricing", path: "/pricing" },
   { label: "Demo", path: "/demo" },
   { label: "Contact", path: "/contact" },
];

const getInitial = (name?: string) => name?.trim()[0]?.toUpperCase() ?? "";

const Navbar = () => {
   const router = useRouter();
   const user = useAuthStore((state) => state.user);
   const isInitialized = useAuthStore((state) => state.isInitialized);
   const pathname = usePathname();
   const [isMenuOpen, setIsMenuOpen] = useState(false);
   const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

   const openMenu = () => {
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      setIsMenuOpen(true);
   };

   const closeMenu = () => {
      timeoutRef.current = setTimeout(() => setIsMenuOpen(false), 100);
   };

   return (
      <nav className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-border bg-background/95 px-6 font-sans backdrop-blur-md">
         <div className="flex items-center">
            <Link href="/" className="flex items-center gap-3 transition-transform active:scale-95">
               <div className="relative">
                  <div className="absolute -inset-1 rounded-lg bg-primary/20 blur-sm"></div>
                  <Image src="/logo.png" width={32} height={32} alt="Logo" />
               </div>
               <span className="text-[22px] font-medium tracking-tight text-foreground">Stalks</span>
            </Link>
         </div>

         <div className="flex items-center gap-8">
            <div className="hidden items-center gap-1 md:flex">
               {NAV_ITEMS.map((link) => {
                  const isActive = pathname === link.path;
                  const baseStyles = `relative rounded-full px-4 py-1.5 text-[13px] font-medium transition-all duration-300 ${
                     isActive ? "text-primary" : "text-muted-foreground hover:text-foreground hover:bg-accent/30"
                  }`;

                  if (link.isMega) {
                     return (
                        <div key={link.label} className="relative" onMouseEnter={openMenu} onMouseLeave={closeMenu}>
                           <button className={`${baseStyles} cursor-pointer flex items-center gap-1`}>
                              {link.label}
                           </button>

                           {isMenuOpen && <ProductMegaMenu />}
                        </div>
                     );
                  }

                  return (
                     <Button
                        key={link.path}
                        variant="ghost"
                        className={baseStyles}
                        onClick={() => router.push(link.path!)}>
                        {link.label}
                     </Button>
                  );
               })}
            </div>

            <div className="h-5 w-px bg-border" />

            <div className="flex min-w-[140px] items-center justify-end gap-5">
               {!isInitialized ? null : user ? (
                  <>
                     <Link
                        href="/portfolios"
                        className="relative group overflow-hidden rounded-full bg-foreground px-5 py-2 text-[13px] font-bold text-background transition-all active:scale-95">
                        <span className="relative z-10">Open Stalks</span>
                        <div className="absolute inset-0 translate-y-full bg-primary transition-transform duration-300 group-hover:translate-y-0" />
                     </Link>
                     <Avatar title={user.name}>
                        <AvatarFallback className="bg-primary text-primary-foreground">
                           {getInitial(user.name)}
                        </AvatarFallback>
                     </Avatar>
                  </>
               ) : (
                  <>
                     <Link
                        href="/login"
                        className="text-[13px] font-semibold text-muted-foreground hover:text-foreground">
                        Log in
                     </Link>
                     <Link
                        href="/signup"
                        className="relative group overflow-hidden rounded-full bg-foreground px-5 py-2 text-[13px] font-bold text-background transition-all active:scale-95">
                        <span className="relative z-10">Get started</span>
                        <div className="absolute inset-0 translate-y-full bg-primary transition-transform duration-300 group-hover:translate-y-0" />
                     </Link>
                  </>
               )}
            </div>
         </div>
      </nav>
   );
};

export default Navbar;
