import AppShell from "@/features/layout/components/AppShell";

export default function Layout({ children }: { children: React.ReactNode }) {
   return <AppShell>{children}</AppShell>;
}
