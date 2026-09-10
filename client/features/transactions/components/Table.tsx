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

// ─── Side badge config ────────────────────────────────────────────────────────

const SIDE_CONFIG: Record<TransactionSide, { icon: string; color: string; bg: string; border: string }> = {
   BUY: { icon: "↗", color: "var(--primary)", bg: "color-mix(in srgb, var(--primary) 12%, var(--background))", border: "var(--primary)" },
   SELL: { icon: "↙", color: "var(--destructive)", bg: "color-mix(in srgb, var(--destructive) 12%, var(--background))", border: "var(--destructive)" },
   DEPOSIT: { icon: "↓", color: "var(--info)", bg: "color-mix(in srgb, var(--info) 12%, var(--background))", border: "var(--info)" },
   WITHDRAW: { icon: "↑", color: "var(--warning)", bg: "color-mix(in srgb, var(--warning) 12%, var(--background))", border: "var(--warning)" },
   INCOME: { icon: "$", color: "var(--chart-5)", bg: "color-mix(in srgb, var(--chart-5) 12%, var(--background))", border: "var(--chart-5)" },
   FEE: { icon: "%", color: "var(--muted-foreground)", bg: "var(--card)", border: "var(--border)" },
};

const fmt = {
   currency: (n: number) =>
      new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", minimumFractionDigits: 2 }).format(n),
   number: (n: number) => new Intl.NumberFormat("en-US", { maximumFractionDigits: 6 }).format(n),
   date: (s: string) => new Date(s).toLocaleDateString("en-US", { month: "short", day: "2-digit", year: "numeric" }),
};

// ─── Column definitions ───────────────────────────────────────────────────────

const COLUMNS: ColumnDef<Transaction>[] = [
   {
      id: "transactionDate",
      accessorKey: "transactionDate",
      header: "DATE",
      sortingFn: (a, b) =>
         new Date(a.original.transactionDate).getTime() - new Date(b.original.transactionDate).getTime(),
      cell: ({ getValue }) => (
         <span
            style={{ color: "var(--muted-foreground)", fontSize: "11px", fontVariantNumeric: "tabular-nums", letterSpacing: "0.03em" }}
         >
            {fmt.date(getValue<string>())}
         </span>
      ),
   },
   {
      id: "symbol",
      accessorKey: "symbol",
      header: "SYMBOL",
      cell: ({ getValue }) => (
         <span style={{ color: "var(--foreground)", fontWeight: 600, fontSize: "13px", letterSpacing: "0.05em" }}>
            {getValue<string>()}
         </span>
      ),
   },
   {
      id: "company",
      accessorKey: "company",
      header: "COMPANY",
      cell: ({ getValue }) => (
         <span
            style={{
               color: "var(--muted-foreground)",
               fontSize: "12px",
               maxWidth: "160px",
               display: "block",
               overflow: "hidden",
               textOverflow: "ellipsis",
               whiteSpace: "nowrap",
            }}
         >
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
               style={{
                  display: "inline-flex",
                  alignItems: "center",
                  gap: "4px",
                  padding: "2px 8px",
                  borderRadius: "20px",
                  fontSize: "10px",
                  fontWeight: 600,
                  letterSpacing: "0.08em",
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
         <span style={{ color: "var(--foreground)", fontSize: "12px", fontVariantNumeric: "tabular-nums" }}>
            {fmt.number(getValue<number>())}
         </span>
      ),
   },
   {
      id: "rate",
      accessorKey: "rate",
      header: "RATE",
      cell: ({ getValue }) => (
         <span style={{ color: "var(--foreground)", fontSize: "12px", fontVariantNumeric: "tabular-nums" }}>
            {fmt.currency(getValue<number>())}
         </span>
      ),
   },
   {
      id: "commission",
      accessorKey: "commission",
      header: "COMMISSION",
      enableSorting: false,
      cell: ({ getValue }) => (
         <span style={{ color: "var(--muted-foreground)", fontSize: "12px", fontVariantNumeric: "tabular-nums" }}>
            {fmt.currency(getValue<number>())}
         </span>
      ),
   },
   {
      id: "totalAmount",
      accessorKey: "totalAmount",
      header: "TOTAL",
      cell: ({ row }) => {
         const side = row.original.side;
         const isPositive = ["BUY", "DEPOSIT", "INCOME"].includes(side);
         const isNegative = ["SELL", "WITHDRAW", "FEE"].includes(side);
         // const val = getValue<number>();
         const val = row.original.rate * row.original.quantity;
         return (
            <span
               style={{
                  color: isPositive ? "var(--primary)" : isNegative ? "var(--destructive)" : "var(--foreground)",
                  fontSize: "13px",
                  fontWeight: 600,
                  fontVariantNumeric: "tabular-nums",
               }}
            >
               {isNegative ? "−" : isPositive ? "+" : ""}
               {fmt.currency(Math.abs(val))}
            </span>
         );
      },
   },
];

const COLUMN_LABELS: Record<string, string> = {
   transactionDate: "Date",
   symbol: "Symbol",
   company: "Company",
   side: "Side",
   quantity: "Qty",
   rate: "Rate",
   commission: "Commission",
   totalAmount: "Total",
};

// ─── Component ────────────────────────────────────────────────────────────────

const TransactionsTable = () => {
   const { filters } = useTransactionFilters();
   const { data: transactions = [], isLoading, isError } = useTransactions(filters);

   const [sorting, setSorting] = useState<SortingState>([{ id: "transactionDate", desc: true }]);
   const [columnVisibility, setColumnVisibility] = useState<VisibilityState>({});
   const [showColumnToggle, setShowColumnToggle] = useState(false);

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
         <div className="flex items-center justify-center py-16" style={{ color: "var(--destructive)", fontSize: "13px" }}>
            Failed to load transactions.
         </div>
      );
   }

   const rows = table.getRowModel().rows;

   return (
      <div style={{ borderRadius: "12px", border: "0.5px solid var(--border)", overflow: "hidden", background: "var(--card)" }}>
         {/* Toolbar */}
         <div
            className="flex items-center justify-between px-4 py-2.5"
            style={{ borderBottom: "0.5px solid var(--border-subtle)", background: "var(--card)" }}
         >
            <span style={{ color: "var(--foreground)", opacity: 0.6, fontSize: "11px", letterSpacing: "0.05em" }}>
               {rows.length} TRANSACTION{rows.length !== 1 ? "S" : ""}
            </span>

            {/* Column toggle */}
            <div style={{ position: "relative" }}>
               <button
                  onClick={() => setShowColumnToggle((v) => !v)}
                  style={{
                     background: showColumnToggle ? "var(--secondary)" : "transparent",
                     border: "0.5px solid",
                     borderColor: showColumnToggle ? "var(--border)" : "var(--border)",
                     borderRadius: "6px",
                     padding: "3px 10px",
                     fontSize: "10px",
                     fontWeight: 500,
                     letterSpacing: "0.08em",
                     color: showColumnToggle ? "var(--foreground)" : "var(--foreground)",
                     cursor: "pointer",
                     transition: "all 0.15s ease",
                  }}
               >
                  COLUMNS
               </button>

               {showColumnToggle && (
                  <div
                     style={{
                        position: "absolute",
                        right: 0,
                        top: "calc(100% + 6px)",
                        zIndex: 50,
                        background: "var(--card)",
                        border: "0.5px solid var(--border)",
                        borderRadius: "10px",
                        padding: "8px",
                        minWidth: "160px",
                        boxShadow: "0 8px 24px rgba(0,0,0,0.5)",
                     }}
                  >
                     <div
                        style={{
                           color: "var(--foreground)",
                           opacity: 0.7,
                           fontSize: "9px",
                           letterSpacing: "0.12em",
                           padding: "4px 8px 8px",
                           borderBottom: "0.5px solid var(--border-subtle)",
                           marginBottom: "6px",
                        }}
                     >
                        TOGGLE COLUMNS
                     </div>
                     {table.getAllLeafColumns().map((col) => (
                        <label
                           key={col.id}
                           style={{
                              display: "flex",
                              alignItems: "center",
                              gap: "8px",
                              padding: "5px 8px",
                              borderRadius: "6px",
                              cursor: "pointer",
                              fontSize: "12px",
                              color: col.getIsVisible() ? "var(--foreground)" : "var(--muted-foreground)",
                              transition: "background 0.1s ease",
                           }}
                           onMouseEnter={(e) => (e.currentTarget.style.background = "var(--border-subtle)")}
                           onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                           <input
                              type="checkbox"
                              checked={col.getIsVisible()}
                              onChange={col.getToggleVisibilityHandler()}
                              style={{ accentColor: "var(--primary)", width: "12px", height: "12px" }}
                           />
                           {COLUMN_LABELS[col.id] ?? col.id}
                        </label>
                     ))}
                  </div>
               )}
            </div>
         </div>

         {/* Table */}
         <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
               <thead>
                  {table.getHeaderGroups().map((hg) => (
                     <tr key={hg.id} style={{ borderBottom: "0.5px solid var(--border)", background: "var(--card)" }}>
                        {hg.headers.map((header) => {
                           const sorted = header.column.getIsSorted();
                           const canSort = header.column.getCanSort();
                           return (
                              <th
                                 key={header.id}
                                 onClick={canSort ? header.column.getToggleSortingHandler() : undefined}
                                 style={{
                                    padding: "10px 16px",
                                    textAlign: "left",
                                    fontSize: "10px",
                                    fontWeight: 500,
                                    letterSpacing: "0.1em",
                                    color: sorted ? "var(--primary)" : "var(--foreground)",
                                    cursor: canSort ? "pointer" : "default",
                                    userSelect: "none",
                                    whiteSpace: "nowrap",
                                    transition: "color 0.15s ease",
                                 }}
                              >
                                 {flexRender(header.column.columnDef.header, header.getContext())}
                                 {sorted === "asc" ? (
                                    " ↑"
                                 ) : sorted === "desc" ? (
                                    " ↓"
                                 ) : canSort ? (
                                    <span style={{ opacity: 0.2, marginLeft: "4px" }}>↕</span>
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
                           style={{
                              padding: "48px 16px",
                              textAlign: "center",
                              color: "var(--muted-foreground)",
                              fontSize: "12px",
                              letterSpacing: "0.05em",
                           }}
                        >
                           NO TRANSACTIONS FOUND
                        </td>
                     </tr>
                  ) : (
                     rows.map((row) => (
                        <tr
                           key={row.id}
                           style={{ borderBottom: "0.5px solid var(--border-subtle)", transition: "background 0.1s ease" }}
                           onMouseEnter={(e) => (e.currentTarget.style.background = "var(--card)")}
                           onMouseLeave={(e) => (e.currentTarget.style.background = "transparent")}
                        >
                           {row.getVisibleCells().map((cell) => (
                              <td key={cell.id} style={{ padding: "10px 16px", verticalAlign: "middle" }}>
                                 {flexRender(cell.column.columnDef.cell, cell.getContext())}
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
