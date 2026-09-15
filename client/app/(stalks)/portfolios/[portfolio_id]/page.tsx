import PortfolioDetail from "@/features/portfolios/components/PortfolioDetail";

export default function PortfolioDetailRoute({ params }: { params: Promise<{ portfolio_id: string }> }) {
   return <PortfolioDetail params={params} />;
}
