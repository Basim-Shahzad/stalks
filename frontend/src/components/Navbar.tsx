import { useState, useRef } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Button } from "@heroui/react";
import ProductMegaMenu from "../pages/Product/components/ProductMegaMenu";

const NAV_ITEMS = [
   { label: "Product", isMega: true },
   { label: "Pricing", path: "/pricing" },
   { label: "Demo", path: "/demo" },
   { label: "Contact", path: "/contact" },
];

const Navbar = () => {
   const location = useLocation();
   const navigate = useNavigate();
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
      <nav className="sticky top-0 z-50 flex h-16 w-full items-center justify-between border-b border-white/6 bg-black/95 px-6 font-sans backdrop-blur-md">
         <div className="flex items-center">
            <Link to="/" className="flex items-center gap-3 transition-transform active:scale-95">
               <div className="relative">
                  <div className="absolute -inset-1 rounded-lg bg-[#22d07a]/20 blur-sm"></div>
                  <img src="/logo.png" className="relative w-8 rounded-lg" alt="Logo" />
               </div>
               <span className="text-[22px] font-medium tracking-tight text-white">Stalks</span>
            </Link>
         </div>

         <div className="flex items-center gap-8">
            <div className="hidden items-center gap-1 md:flex">
               {NAV_ITEMS.map((link) => {
                  const isActive = location.pathname === link.path;
                  const baseStyles = `relative rounded-full px-4 py-1.5 text-[13px] font-medium transition-all duration-300 ${
                     isActive ? "text-[#22d07a]" : "text-[#8a8f9f] hover:text-white hover:bg-white/3"
                  }`;

                  if (link.isMega) {
                     return (
                        <div
                           key={link.label}
                           className="relative"
                           onMouseEnter={openMenu}
                           onMouseLeave={closeMenu}
                        >
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
                        onPress={() => navigate(link.path!)}
                     >
                        {link.label}
                     </Button>
                  );
               })}
            </div>

            <div className="h-5 w-px bg-white/8" />

            <div className="flex items-center gap-5">
               <Link to="/login" className="text-[13px] font-semibold text-[#8a8f9f] hover:text-white">
                  Log in
               </Link>
               <Link
                  to="/signup"
                  className="relative group overflow-hidden rounded-full bg-white px-5 py-2 text-[13px] font-bold text-black transition-all active:scale-95"
               >
                  <span className="relative z-10">Get started</span>
                  <div className="absolute inset-0 translate-y-full bg-[#22d07a] transition-transform duration-300 group-hover:translate-y-0" />
               </Link>
            </div>
         </div>
      </nav>
   );
};

export default Navbar;