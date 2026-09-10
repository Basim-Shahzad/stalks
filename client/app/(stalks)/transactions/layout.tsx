import TransactionsLayoutShell from "@/features/transactions/components/TransactionsLayoutShell";

export default function Layout({ children }: { children: React.ReactNode }) {
   return <TransactionsLayoutShell>{children}</TransactionsLayoutShell>;
}
