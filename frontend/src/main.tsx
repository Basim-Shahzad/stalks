import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { createBrowserRouter, RouterProvider, Outlet } from "react-router-dom";
import "./index.css";
import App from "./App";
import Navbar from "./components/Navbar";
import { TransactionsProvider } from "./contexts/TransactionHistoryContext";
// import Transactions from "./pages/Transactions/Transactions";
// import Portfolio from "./pages/Portfolio/Portfolio";
import Login from "./pages/Auth/Login";
import Signup from "./pages/Auth/Signup";
import Product from "./pages/Product/Product";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// import Stocks from "./pages/Stocks";

import { SettingsProvider } from "./contexts/SettingsContext";

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
         { path: "product", element: <Product /> },
         // { path: "stocks", element: <Stocks /> },
         // { path: "transactions", element: <Transactions /> },
         // { path: "portfolio", element: <Portfolio /> },
      ],
   },
   { path: "login", element: <Login /> },
   { path: "signup", element: <Signup /> },
]);

/* Render */
createRoot(document.getElementById("root")!).render(
   <QueryClientProvider client={queryClient}>
      <TransactionsProvider>
         <SettingsProvider>
            <ReactQueryDevtools client={queryClient} />
            <RouterProvider router={router} />
         </SettingsProvider>
      </TransactionsProvider>
   </QueryClientProvider>,
);
