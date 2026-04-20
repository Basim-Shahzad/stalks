import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import "./index.css";
import App from "./App";
import Navbar from "./components/Navbar";
import { TransactionsProvider } from "./contexts/TransactionHistoryContext";
import Transactions from "./pages/Transactions/Transactions";
import Portfolio from "./pages/Portfolio";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import Stocks from "./pages/Stocks";

import "@mantine/core/styles.css";
import { MantineProvider, createTheme } from "@mantine/core";

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

const theme = createTheme({
   /** Customizations here **/
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
         { path: "transactions", element: <Transactions /> },
         { path: "portfolio", element: <Portfolio /> },
      ],
   },
]);

/* Render */
createRoot(document.getElementById("root")!).render(
   <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} defaultColorScheme="light">
         <TransactionsProvider>
            <ReactQueryDevtools client={queryClient} />
            <RouterProvider router={router} />
         </TransactionsProvider>
      </MantineProvider>
   </QueryClientProvider>,
);
