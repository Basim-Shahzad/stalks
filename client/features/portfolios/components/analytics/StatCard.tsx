import React from "react";
import { Skeleton } from "@/components/ui/skeleton";

interface StatCardProps {
   title: string | undefined;
   stat: number | undefined;
   isSkeleton: boolean;
}

export const StatCard: React.FC<StatCardProps> = ({ title, stat, isSkeleton }) => {
   return (
      <div className="relative select-none overflow-hidden rounded-2xl border border-primary/20 bg-background p-6 transition-all duration-300 hover:border-primary/40 hover:shadow-[0_0_20px_var(--primary)]/10">
         <div className="absolute inset-0 bg-primary/10 pointer-events-none" />

         <div className="relative z-10 flex flex-col gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
               {title}
            </span>

            <span className="text-3xl font-bold font-mono tracking-tight text-foreground">
               {isSkeleton ? (
                  <Skeleton className="h-8 w-full bg-primary/10" />
               ) : (
                  stat?.toFixed(2)
               )}
            </span>
         </div>
      </div>
   );
};
