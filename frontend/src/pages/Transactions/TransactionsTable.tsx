import React, { useMemo, useState } from "react";
import {
   useReactTable,
   getCoreRowModel,
   getSortedRowModel,
   getFilteredRowModel,
   getPaginationRowModel,
   flexRender,
   createColumnHelper,
   type SortingState,
   type ColumnFiltersState,
} from "@tanstack/react-table";
import { useTransactions } from "../../hooks/useTransactions";
import type { TradeTransaction } from "../../types";

const columnHelper = createColumnHelper<TradeTransaction>();

const fmt = (n: number) =>
   n === 0 ? "—" : n.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const TransactionsTable = () => {
   const { isLoading, transactions } = useTransactions();
   const [sorting, setSorting] = useState<SortingState>([]);
   const [columnFilters, setColumnFilters] = useState<ColumnFiltersState>([]);
   const [globalFilter, setGlobalFilter] = useState("");

   const columns = useMemo(
      () => [
         columnHelper.accessor("date", {
            header: "Date",
            cell: (info) => (
               <span className="whitespace-nowrap text-slate-600 text-xs font-medium">{info.getValue()}</span>
            ),
         }),
         columnHelper.accessor("symbol", {
            header: "Symbol",
            cell: (info) => (
               <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-indigo-100 text-indigo-800">
                  {info.getValue()}
               </span>
            ),
         }),
         columnHelper.accessor("company", {
            header: "Company",
            cell: (info) => (
               <span
                  className="text-slate-800 text-sm font-medium truncate max-w-[180px] block"
                  title={info.getValue()}>
                  {info.getValue()}
               </span>
            ),
         }),
         columnHelper.accessor("sector", {
            header: "Sector",
            cell: (info) => (
               <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium bg-slate-100 text-slate-600">
                  {info.getValue()}
               </span>
            ),
         }),
         columnHelper.accessor("buy", {
            header: "Buy",
            meta: { align: "right" },
            cell: (info) => (
               <span
                  className={`text-sm tabular-nums ${info.getValue() > 0 ? "text-emerald-700 font-medium" : "text-slate-400"}`}>
                  {fmt(info.getValue())}
               </span>
            ),
         }),
         columnHelper.accessor("sell", {
            header: "Sell",
            meta: { align: "right" },
            cell: (info) => (
               <span
                  className={`text-sm tabular-nums ${info.getValue() > 0 ? "text-rose-600 font-medium" : "text-slate-400"}`}>
                  {fmt(info.getValue())}
               </span>
            ),
         }),
         columnHelper.accessor("rate", {
            header: "Rate",
            meta: { align: "right" },
            cell: (info) => <span className="text-sm tabular-nums text-slate-700">{fmt(info.getValue())}</span>,
         }),
         columnHelper.accessor("commission", {
            header: "Comm.",
            meta: { align: "right" },
            cell: (info) => <span className="text-sm tabular-nums text-slate-500">{fmt(info.getValue())}</span>,
         }),
         columnHelper.accessor("taxes", {
            header: "Taxes",
            meta: { align: "right" },
            cell: (info) => <span className="text-sm tabular-nums text-slate-500">{fmt(info.getValue())}</span>,
         }),
         columnHelper.accessor("charges", {
            header: "Charges",
            meta: { align: "right" },
            cell: (info) => <span className="text-sm tabular-nums text-slate-500">{fmt(info.getValue())}</span>,
         }),
         columnHelper.accessor("total_amount", {
            header: "Total",
            meta: { align: "right" },
            cell: (info) => (
               <span className="text-sm tabular-nums font-semibold text-indigo-700">{fmt(info.getValue())}</span>
            ),
         }),
      ],
      [],
   );

   const data = useMemo(() => transactions ?? [], [transactions]);

   const table = useReactTable<TradeTransaction>({
      data,
      columns,
      state: { sorting, columnFilters, globalFilter },
      onSortingChange: setSorting,
      onColumnFiltersChange: setColumnFilters,
      onGlobalFilterChange: setGlobalFilter,
      getCoreRowModel: getCoreRowModel(),
      getSortedRowModel: getSortedRowModel(),
      getFilteredRowModel: getFilteredRowModel(),
      getPaginationRowModel: getPaginationRowModel(),
      initialState: { pagination: { pageSize: 20 } },
   });

   const totalAmount = useMemo(
      () => table.getFilteredRowModel().rows.reduce((sum, row) => sum + row.original.total_amount, 0),
      // eslint-disable-next-line react-hooks/exhaustive-deps
      [table.getFilteredRowModel().rows],
   );

   return (
      <section className="w-full space-y-4">
         {/* Toolbar */}
         <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div className="flex items-center gap-2">
               <h2 className="text-base font-semibold text-slate-800">Transactions</h2>
               <span className="text-xs font-medium px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 border border-indigo-100">
                  {table.getFilteredRowModel().rows.length}
               </span>
            </div>
            <input
               type="text"
               placeholder="Search symbol, company, sector…"
               value={globalFilter}
               onChange={(e) => setGlobalFilter(e.target.value)}
               className="
            w-full sm:w-64 text-sm px-3 py-1.5 rounded-lg
            border border-slate-200 bg-white text-slate-800 placeholder:text-slate-400
            focus:outline-none focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400
            transition
          "
            />
         </div>

         {/* Table wrapper */}
         <div className="rounded-xl border border-slate-200 bg-white overflow-hidden">
            <div className="overflow-x-auto">
               {isLoading ? (
                  <div className="flex items-center justify-center py-16 text-slate-400 text-sm gap-2">
                     <svg className="animate-spin w-4 h-4 text-indigo-500" viewBox="0 0 24 24" fill="none">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                     </svg>
                     Loading transactions…
                  </div>
               ) : table.getRowModel().rows.length === 0 ? (
                  <div className="flex flex-col items-center justify-center py-16 gap-2 text-slate-400">
                     <svg className="w-8 h-8 opacity-40" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                           strokeLinecap="round"
                           strokeLinejoin="round"
                           strokeWidth={1.5}
                           d="M9 17v-6h13M9 11V5H3v6m0 6h6m6 0h3"
                        />
                     </svg>
                     <span className="text-sm">No transactions found</span>
                  </div>
               ) : (
                  <table className="w-full text-sm border-collapse">
                     <thead>
                        {table.getHeaderGroups().map((hg) => (
                           <tr key={hg.id} className="bg-slate-50 border-b border-slate-200">
                              {hg.headers.map((header) => {
                                 const isRightAligned = (header.column.columnDef.meta as any)?.align === "right";
                                 return (
                                    <th
                                       key={header.id}
                                       onClick={header.column.getToggleSortingHandler()}
                                       className={`
                            px-4 py-2.5 text-xs font-semibold uppercase tracking-wide text-slate-500
                            select-none whitespace-nowrap
                            ${isRightAligned ? "text-right" : "text-left"}
                            ${header.column.getCanSort() ? "cursor-pointer hover:text-indigo-600 transition-colors" : ""}
                          `}>
                                       <span className="inline-flex items-center gap-1">
                                          {flexRender(header.column.columnDef.header, header.getContext())}
                                          {header.column.getCanSort() && (
                                             <SortIcon direction={header.column.getIsSorted()} />
                                          )}
                                       </span>
                                    </th>
                                 );
                              })}
                           </tr>
                        ))}
                     </thead>

                     <tbody>
                        {table.getRowModel().rows.map((row, idx) => (
                           <tr
                              key={row.id}
                              className={`
                      border-b border-slate-100 last:border-0
                      hover:bg-indigo-50/40 transition-colors
                      ${idx % 2 === 0 ? "bg-white" : "bg-slate-50/60"}
                    `}>
                              {row.getVisibleCells().map((cell) => {
                                 const isRightAligned = (cell.column.columnDef.meta as any)?.align === "right";
                                 return (
                                    <td
                                       key={cell.id}
                                       className={`px-4 py-2.5 ${isRightAligned ? "text-right" : "text-left"}`}>
                                       {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                    </td>
                                 );
                              })}
                           </tr>
                        ))}
                     </tbody>

                     {/* Footer totals row */}
                     <tfoot>
                        <tr className="bg-indigo-50/60 border-t-2 border-indigo-200">
                           <td
                              colSpan={columns.length - 1}
                              className="px-4 py-2.5 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                              Total ({table.getFilteredRowModel().rows.length} trades)
                           </td>
                           <td className="px-4 py-2.5 text-right text-sm font-bold text-indigo-800 tabular-nums">
                              {fmt(totalAmount)}
                           </td>
                        </tr>
                     </tfoot>
                  </table>
               )}
            </div>
         </div>

         {/* Pagination */}
         {!isLoading && table.getPageCount() > 1 && (
            <div className="flex items-center justify-between text-sm text-slate-500">
               <span>
                  Page <span className="font-medium text-slate-700">{table.getState().pagination.pageIndex + 1}</span>{" "}
                  of <span className="font-medium text-slate-700">{table.getPageCount()}</span>
               </span>
               <div className="flex items-center gap-1">
                  <PaginationBtn
                     onClick={() => table.setPageIndex(0)}
                     disabled={!table.getCanPreviousPage()}
                     label="«"
                  />
                  <PaginationBtn
                     onClick={() => table.previousPage()}
                     disabled={!table.getCanPreviousPage()}
                     label="‹"
                  />
                  <PaginationBtn onClick={() => table.nextPage()} disabled={!table.getCanNextPage()} label="›" />
                  <PaginationBtn
                     onClick={() => table.setPageIndex(table.getPageCount() - 1)}
                     disabled={!table.getCanNextPage()}
                     label="»"
                  />
               </div>
            </div>
         )}
      </section>
   );
};

/* ─── Sub-components ─────────────────────────────── */

const SortIcon = ({ direction }: { direction: false | "asc" | "desc" }) => (
   <span className="text-[10px] leading-none">
      {direction === "asc" ? "▲" : direction === "desc" ? "▼" : <span className="opacity-30">⇅</span>}
   </span>
);

const PaginationBtn = ({ onClick, disabled, label }: { onClick: () => void; disabled: boolean; label: string }) => (
   <button
      onClick={onClick}
      disabled={disabled}
      className="
      w-8 h-8 flex items-center justify-center rounded-lg text-sm
      border border-slate-200 bg-white text-slate-600
      hover:bg-indigo-50 hover:border-indigo-300 hover:text-indigo-700
      disabled:opacity-30 disabled:cursor-not-allowed
      transition
    ">
      {label}
   </button>
);

export default TransactionsTable;
