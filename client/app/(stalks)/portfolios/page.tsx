import Header from "@/features/layout/components/Header";
import PortfolioGrid from "@/features/portfolios/components/PortfolioGrid";
import PortfolioCreateForm from "@/features/portfolios/components/PortfolioCreateForm";

export default function PortfolioPage() {
   return (
      <div className="animate-fade-in">
         <Header title="Portfolios" right={<PortfolioCreateForm />} />

         <PortfolioGrid />
      </div>
   );
}
