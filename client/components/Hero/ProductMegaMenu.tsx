import { ChartLine, Zap, Bell, Shield } from "lucide-react";

export default function ProductMegaMenu() {
   return (
      <div className="absolute left-1/2 top-full -translate-x-1/2 pt-3 z-50">
         {/* invisible bridge to prevent accidental mouseLeave */}
         <div className="absolute -top-3 left-0 h-3 w-full" />

         <div className="w-[520px] rounded-xl border border-white/8 bg-[#0c0e12] p-5 text-white shadow-2xl">
            {/* Arrow */}
            <div className="absolute -top-[5px] left-1/2 -translate-x-1/2 h-2.5 w-2.5 rotate-45 border-l border-t border-white/8 bg-[#0c0e12]" />

            <div className="grid grid-cols-2 gap-8">
               {/* Capabilities */}
               <div className="space-y-4">
                  <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#5a607a]">Capabilities</h4>
                  <div className="flex cursor-pointer gap-3 group">
                     <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#22d07a]/10 text-[#22d07a] group-hover:bg-[#22d07a]/20 transition-colors">
                        <ChartLine size={18} />
                     </div>
                     <div>
                        <p className="text-[13px] font-semibold text-[#e8eaf2]">Portfolio Tracker</p>
                        <p className="text-[11px] leading-relaxed text-[#8a8f9f]">Monitor holdings in one dashboard.</p>
                     </div>
                  </div>
                  <div className="flex cursor-pointer gap-3 group">
                     <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#22d07a]/10 text-[#22d07a] group-hover:bg-[#22d07a]/20 transition-colors">
                        <Zap size={18} />
                     </div>
                     <div>
                        <p className="text-[13px] font-semibold text-[#e8eaf2]">Strategy Builder</p>
                        <p className="text-[11px] leading-relaxed text-[#8a8f9f]">Create rules without code.</p>
                     </div>
                  </div>
               </div>

               {/* Automation */}
               <div className="space-y-4">
                  <h4 className="text-[10px] font-bold uppercase tracking-[0.15em] text-[#5a607a]">Automation</h4>
                  <div className="flex cursor-pointer gap-3 group">
                     <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#22d07a]/10 text-[#22d07a] group-hover:bg-[#22d07a]/20 transition-colors">
                        <Bell size={18} />
                     </div>
                     <div>
                        <p className="text-[13px] font-semibold text-[#e8eaf2]">Smart Triggers</p>
                        <p className="text-[11px] leading-relaxed text-[#8a8f9f]">Real-time buy/sell signals.</p>
                     </div>
                  </div>
                  <div className="flex cursor-pointer gap-3 group">
                     <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-[#22d07a]/10 text-[#22d07a] group-hover:bg-[#22d07a]/20 transition-colors">
                        <Shield size={18} />
                     </div>
                     <div>
                        <p className="text-[13px] font-semibold text-[#e8eaf2]">Market Scanner</p>
                        <p className="text-[11px] leading-relaxed text-[#8a8f9f]">Filter stocks by technicals.</p>
                     </div>
                  </div>
               </div>
            </div>

            <div className="mt-6 pt-4 border-t border-white/8 flex justify-between items-center">
               <button className="text-[13px] text-[#22d07a] font-medium hover:opacity-80 transition-opacity">
                  View All Features →
               </button>
               <span className="text-[10px] text-[#5a607a]">PSX Data Support (for now)</span>
            </div>
         </div>
      </div>
   );
}