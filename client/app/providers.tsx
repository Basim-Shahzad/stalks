"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect } from "react";
import { useRouter } from 'next/navigation';
import { useAuth } from "@/features/auth/api";
import { useAuthStore } from "@/features/auth/store";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { Toaster } from "@/components/ui/sonner";
import { TransactionsCreatePdfProvider } from "@/features/transactions/context/TransactionsCreatePdfContext";

let authInitialized = false;

function AuthInitializer() {
   const router = useRouter()
   useEffect(() => {
      if (authInitialized) return;
      authInitialized = true;

      useAuth.me().catch(() => {
         useAuthStore.getState().setAuthInitialized(null);
      });
      router.push("/portfolios")
   }, []);
   return null;
}

export const queryClient = new QueryClient({
   defaultOptions: {
      queries: {
         staleTime: 10 * 60 * 1000,
         refetchOnWindowFocus: false,
         refetchOnMount: false,
      },
   },
});

export default function Providers({ children }: { children: ReactNode }) {
   return (
      <QueryClientProvider client={queryClient}>
         <AuthInitializer />
         <Toaster />
         <TransactionsCreatePdfProvider>{children}</TransactionsCreatePdfProvider>
         <ReactQueryDevtools />
      </QueryClientProvider>
   );
}
