import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import "./index.css";
import App from "./App";
import Navbar from "./components/Navbar";
import { TransactionHistoryProvider } from "./contexts/TransactionHistoryContext";
import TransactionHistory from "./pages/TransactionHistory";
import Portfolio from "./pages/Portfolio";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Stocks from "./pages/Stocks";

const queryClient = new QueryClient({
   defaultOptions: {
      queries: {
         staleTime: 1000 * 60 * 5,
         refetchOnMount: false,
         refetchOnWindowFocus: false,
         refetchOnReconnect: false,
      },
   },
});

function Layout() {
   return (
      <>
         <Navbar />
         <Outlet />
      </>
   );
}

/* Router */
const router = createBrowserRouter([
   {
      path: "/",
      element: <Layout />,
      children: [
         { index: true, element: <App /> },
         { path: "stocks", element: <Stocks /> },
         { path: "transaction-history", element: <TransactionHistory /> },
         { path: "portfolio", element: <Portfolio /> },
      ],
   },
]);

/* Render */
createRoot(document.getElementById("root")!).render(
   <StrictMode>
      <QueryClientProvider client={queryClient}>
         <TransactionHistoryProvider>
            <RouterProvider router={router} />
         </TransactionHistoryProvider>
      </QueryClientProvider>
   </StrictMode>,
);
