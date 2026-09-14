"use client";

import { useMemo, useState } from "react";
import {
   useReactTable,
   getCoreRowModel,
   getSortedRowModel,
   type SortingState,
   type ColumnDef,
   type VisibilityState,
   flexRender,
} from "@tanstack/react-table";
import { useTransactions } from "../hooks/useTransactions";
import { useTransactionFilters } from "../hooks/useTransactionFilters";
import type { Transaction, TransactionSide } from "../types";
import { Spinner } from "@/components/ui/spinner";
import { ColumnsMenu } from "./columns-menu";

// ─── Side badge config ────────────────────────────────────────────────────────

const SIDE_CONFIG: Record<
   TransactionSide,
   { icon: string; color: string; bg: string; border: string }
> = {
   BUY: {
      icon: "↗",
      color: "var(--primary)",
      bg: "color-mix(in srgb, var(--primary) 12%, var(--background))",
      border: "var(--primary)",
   },
   SELL: {
      icon: "↙",
      color: "var(--destructive)",
      bg: "color-mix(in srgb, var(--destructive) 12%, var(--background))",
      border: "var(--destructive)",
   },
   DEPOSIT: {
      icon: "↓",
      color: "var(--info)",
      bg: "color-mix(in srgb, var(--info) 12%, var(--background))",
      border: "var(--info)",
   },
   WITHDRAW: {
      icon: "↑",
      color: "var(--warning)",
      bg: "color-mix(in srgb, var(--warning) 12%, var(--background))",
      border: "var(--warning)",
   },
   INCOME: {
      icon: "$",
      color: "var(--chart-5)",
      bg: "color-mix(in srgb, var(--chart-5) 12%, var(--background))",
      border: "var(--chart-5)",
   },
   FEE: {
      icon: "%",
      color: "var(--muted-foreground)",
      bg: "var(--card)",
      border: "var(--border)",
   },
};

const fmt = {
   number: (n: number) =>
      new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 }).format(n),
   date: (s: string) =>
      new Date(s).toLocaleDateString("en-US", {
         month: "short",
         day: "2-digit",
         year: "numeric",
      }),
};

// ─── Column definitions ───────────────────────────────────────────────────────

const COLUMNS: ColumnDef<Transaction>[] = [
   {
      id: "transactionDate",
      accessorKey: "transactionDate",
      header: "DATE",
      sortingFn: (a, b) =>
         new Date(a.original.transactionDate).getTime() -
         new Date(b.original.transactionDate).getTime(),
      cell: ({ getValue }) => (
         <span className="text-[11px] tracking-[0.03em] tabular-nums text-[var(--muted-foreground)]">
            {fmt.date(getValue<string>())}
         </span>
      ),
   },
   {
      id: "symbol",
      accessorKey: "symbol",
      header: "SYMBOL",
      cell: ({ getValue }) => (
         <span className="text-[13px] font-semibold tracking-[0.05em] text-[var(--foreground)]">
            {getValue<string>()}
         </span>
      ),
   },
   {
      id: "side",
      accessorKey: "side",
      header: "SIDE",
      cell: ({ getValue }) => {
         const side = getValue<TransactionSide>();
         const cfg = SIDE_CONFIG[side];
         return (
            <span
               className="inline-flex items-center gap-1 rounded-[20px] px-2 py-0.5 text-[10px] font-semibold tracking-[0.08em]"
               style={{
                  background: cfg.bg,
                  color: cfg.color,
                  border: `0.5px solid ${cfg.border}`,
               }}
            >
               {cfg.icon} {side}
            </span>
         );
      },
   },
   {
      id: "quantity",
      accessorKey: "quantity",
      header: "QTY",
      cell: ({ getValue }) => (
         <span className="text-[12px] tabular-nums text-[var(--foreground)]">
            {fmt.number(getValue<number>())}
         </span>
      ),
   },
   {
      id: "rate",
      accessorKey: "rate",
      header: "RATE",
      cell: ({ getValue }) => (
         <span className="text-[12px] tabular-nums text-[var(--foreground)]">
            {getValue<number>()}
         </span>
      ),
   },
   {
      id: "commission",
      accessorKey: "commission",
      header: "COMMISSION",
      enableSorting: false,
      cell: ({ getValue }) => (
         <span className="text-[12px] tabular-nums text-[var(--muted-foreground)]">
            {getValue<number>()}
         </span>
      ),
   },
   {
      id: "totalAmount",
      accessorFn: (row) => {
         const isNegative = ["SELL", "WITHDRAW", "FEE"].includes(row.side);
         const magnitude = row.rate * row.quantity;
         return isNegative ? -magnitude : magnitude;
      },
      header: "TOTAL",
      cell: ({ getValue }) => {
         const val = getValue<number>();
         const isPositive = val > 0;
         const isNegative = val < 0;
         return (
            <span
               className="text-[13px] font-semibold tabular-nums"
               style={{
                  color: isPositive
                     ? "var(--primary)"
                     : isNegative
                       ? "var(--destructive)"
                       : "var(--foreground)",
               }}
            >
               {isNegative ? "−" : isPositive ? "+" : ""}
               {Math.abs(val)}
            </span>
         );
      },
   },
];

// ─── Component ────────────────────────────────────────────────────────────────

const TransactionsTable = () => {
   const { filters } = useTransactionFilters();
   const {
      data: transactions = [],
      isLoading,
      isError,
   } = useTransactions(filters);

   const [sorting, setSorting] = useState<SortingState>([
      { id: "transactionDate", desc: true },
   ]);
   const [columnVisibility, setColumnVisibility] = useState<VisibilityState>(
      {},
   );

   const table = useReactTable({
      data: transactions,
      columns: COLUMNS,
      state: { sorting, columnVisibility },
      onSortingChange: setSorting,
      onColumnVisibilityChange: setColumnVisibility,
      getCoreRowModel: getCoreRowModel(),
      getSortedRowModel: getSortedRowModel(),
   });

   if (isLoading) {
      return (
         <div className="flex items-center justify-center py-16">
            <Spinner className="size-5" />
         </div>
      );
   }

   if (isError) {
      return (
         <div className="flex items-center justify-center py-16 text-[13px] text-[var(--destructive)]">
            Failed to load transactions.
         </div>
      );
   }

   const rows = table.getRowModel().rows;

   return (
      <div className="overflow-hidden rounded-xl border-[0.5px] border-[var(--border)] bg-[var(--card)]">
         {/* Toolbar */}
         <div className="flex items-center justify-between border-b-[0.5px] border-[var(--border-subtle)] bg-[var(--card)] px-4 py-2.5">
            <span className="text-[11px] tracking-[0.05em] text-[var(--foreground)] opacity-60">
               {rows.length} TRANSACTION{rows.length !== 1 ? "S" : ""}
            </span>

            {/* Column toggle */}
            <div className="relative">
               <ColumnsMenu table={table} />
            </div>
         </div>

         {/* Table */}
         <div className="overflow-x-auto">
            <table className="w-full border-collapse">
               <thead>
                  {table.getHeaderGroups().map((hg) => (
                     <tr
                        key={hg.id}
                        className="border-b-[0.5px] border-[var(--border)] bg-[var(--card)]"
                     >
                        {hg.headers.map((header) => {
                           const sorted = header.column.getIsSorted();
                           const canSort = header.column.getCanSort();
                           return (
                              <th
                                 key={header.id}
                                 onClick={
                                    canSort
                                       ? header.column.getToggleSortingHandler()
                                       : undefined
                                 }
                                 className={`select-none whitespace-nowrap px-4 py-2.5 text-left text-[10px] font-medium tracking-[0.1em] transition-colors duration-150 ease-in-out ${
                                    sorted
                                       ? "text-[var(--primary)]"
                                       : "text-[var(--foreground)]"
                                 } ${canSort ? "cursor-pointer" : "cursor-default"}`}
                              >
                                 {flexRender(
                                    header.column.columnDef.header,
                                    header.getContext(),
                                 )}
                                 {sorted === "asc" ? (
                                    " ↑"
                                 ) : sorted === "desc" ? (
                                    " ↓"
                                 ) : canSort ? (
                                    <span className="ml-1 opacity-20">↕</span>
                                 ) : null}
                              </th>
                           );
                        })}
                     </tr>
                  ))}
               </thead>
               <tbody>
                  {rows.length === 0 ? (
                     <tr>
                        <td
                           colSpan={table.getVisibleLeafColumns().length}
                           className="px-4 py-12 text-center text-[12px] tracking-[0.05em] text-[var(--muted-foreground)]"
                        >
                           NO TRANSACTIONS FOUND
                        </td>
                     </tr>
                  ) : (
                     rows.map((row) => (
                        <tr
                           key={row.id}
                           className="border-b-[0.5px] border-[var(--border-subtle)] transition-colors duration-100 ease-in-out hover:bg-[var(--card)]"
                        >
                           {row.getVisibleCells().map((cell) => (
                              <td
                                 key={cell.id}
                                 className="px-4 py-2.5 align-middle"
                              >
                                 {flexRender(
                                    cell.column.columnDef.cell,
                                    cell.getContext(),
                                 )}
                              </td>
                           ))}
                        </tr>
                     ))
                  )}
               </tbody>
            </table>
         </div>
      </div>
   );
};

export default TransactionsTable;
