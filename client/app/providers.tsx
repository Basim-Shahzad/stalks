"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactNode, useEffect } from "react";
import { useAuth } from "@/hooks/useAuth";
import { useAuthStore } from "@/stores/useAuthStore";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastProvider } from "@heroui/react";
import { TransactionsCreatePdfProvider } from "@/lib/contexts/TransactionsCreatePdf";

let authInitialized = false;

function AuthInitializer() {
   useEffect(() => {
      if (authInitialized) return;
      authInitialized = true;

      useAuth.me().catch(() => {
         useAuthStore.getState().setAuthInitialized(null);
      });
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
         <ToastProvider />
         <TransactionsCreatePdfProvider>{children}</TransactionsCreatePdfProvider>
         <ReactQueryDevtools />
      </QueryClientProvider>
   );
}
