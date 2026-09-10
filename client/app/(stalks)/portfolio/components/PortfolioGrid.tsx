"use client";

import PortfolioCard from "./PortfolioCard";
import { Skeleton } from "@/components/ui/skeleton";
import { usePortfolios } from "@/lib/queries/portfolioQueries";

const PortfolioGrid = () => {
   const { data, isLoading, isError } = usePortfolios();

   return (
      <main className="mx-8 my-4">
         {isError && (
            <div className="w-full h-64 text-destructive flex items-center justify-center">
               <h1 className="">There was an error fetching your portfolios</h1>
            </div>
         )}

         {isLoading && (
            <div className="grid grid-cols-3 gap-4">
               {/* Change h-full to a fixed height like h-48 */}
               <Skeleton className="h-64 w-full rounded-2xl bg-primary/10" />
               <Skeleton className="h-64 w-full rounded-2xl bg-primary/10" />
               <Skeleton className="h-64 w-full rounded-2xl bg-primary/10" />
            </div>
         )}

         <section className="grid grid-cols-3 gap-4 ">
            {data?.map((portfolio) => (
               <PortfolioCard key={portfolio.id} portfolio={portfolio} />
            ))}
         </section>
      </main>
   );
};

export default PortfolioGrid;
