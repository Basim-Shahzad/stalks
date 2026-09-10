import Header from "@/features/layout/components/Header";
import PortfolioGrid from "@/features/portfolios/components/PortfolioGrid";

export default function PortfolioPage() {
   return (
      <div className="animate-fade-in">
         <Header title="Portfolios" />

         <PortfolioGrid />
      </div>
   );
}
