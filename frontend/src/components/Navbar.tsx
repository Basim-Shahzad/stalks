import { Link } from "react-router-dom";
import Settings from "./Settings";

const Navbar = () => {
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

         <Settings />
      </nav>
   );
};

export default Navbar;
