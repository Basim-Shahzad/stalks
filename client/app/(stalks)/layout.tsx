import Header from "./components/Header";
import Sidebar from "./components/Sidebar";

export default function Layout({ children }: { children: React.ReactNode }) {
   return (
      <div className="flex min-h-screen bg-[#070707] text-white">
         <aside className="w-[250px] h-screen fixed top-0 left-0 z-20">
            <Sidebar />
         </aside>
         <main className="flex-1 bg-[#0F1010] rounded-3xl ml-[260px] mr-[16px] my-[10px] flex flex-col border border-white/5">
            {/* <header className="w-full h-17">
               <Header />
            </header> */}
            {children}
            {/* <div className="h-full w-full bg-red-500"></div> */}
         </main>
      </div>
   );
}
