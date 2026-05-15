import React from "react";
import PortfolioGrid from "./components/PortfolioGrid";
import Header from "../components/Header";

export default function PortfolioPage() {
   return (
      <div className="animate-fade-in">
         <Header title="Portfolios" />

         <PortfolioGrid />
      </div>
   );
}
