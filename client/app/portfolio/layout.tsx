import Header from "./components/Header";
import Sidebar from "./components/Sidebar";

export default function Layout({ children }: { children: React.ReactNode }) {
   return (
      <div className="flex min-h-screen bg-black">
         <aside className="w-[250px] h-screen fixed top-0 left-0 z-20">
            <Sidebar />
         </aside>
         <main className="flex-1 ml-[250px] min-h-screen flex flex-col">
            <header className="w-full">
               <Header />
            </header>
            <div className="h-full w-full">{children}</div>
         </main>
      </div>
   );
}
