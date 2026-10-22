"use client";

import React, { useEffect, useState } from "react";
import CandlestickChart from "./CandlestickChart";
import "./Hero.css";

// ── Hero ──────────────────────────────────────────────────────────────────────
const Hero = () => {
   const [mounted, setMounted] = useState(false);
   useEffect(() => {
      const t = setTimeout(() => setMounted(true), 60);
      return () => clearTimeout(t);
   }, []);

   return (
      // ── Hero wrapper ──
      <div
         className="hero-root relative overflow-hidden flex flex-col"
         style={{ fontFamily: "'DM Sans', sans-serif", background: "var(--bg)" }}>
         {/* atmosphere */}
         <div className="hero-glow" />
         <div className="hero-grid" />

         {/* ── main content ── */}
         <div className="relative z-[5] flex flex-col items-center px-6 pt-[72px]">
            {/* eyebrow */}
            <div className="anim-eyebrow inline-flex items-center gap-[7px] border border-[rgba(34,208,122,0.25)] bg-[rgba(34,208,122,0.06)] rounded-full px-[14px] py-[5px] pl-[9px] text-xs font-medium text-[#22d07a] mb-7">
               <div className="eyebrow-dot" />
               <span>Early Access 🚀</span>
            </div>

            {/* headline */}
            <h1 className="anim-headline hero-headline text-center max-w-[820px] mb-[22px]">
               Stalk the Stock.
               <br />
               <em className="not-italic tracking-tighter text-[#22d07a]">Before it moves.</em>
            </h1>

            {/* sub */}
            <p className="anim-sub hero-sub text-center max-w-[520px] leading-[1.65] font-normal mb-9">
               All your portfolio tracking in one place. Smart buy/sell signals powered by proven strategies.
            </p>

            {/* CTAs */}
            <div className="anim-cta flex flex-wrap items-center gap-[14px] mb-16 max-sm:flex-col max-sm:w-full">
               <button className="btn-hero max-sm:w-full max-sm:text-center">Start for free</button>
               <button className="btn-hero-ghost max-sm:w-full max-sm:justify-center">
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                     <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.2" />
                     <path d="M6.5 5.5L10.5 8L6.5 10.5V5.5Z" fill="currentColor" />
                  </svg>
                  Watch Demo
               </button>
            </div>

            {/* chart */}
            <div className="anim-chart w-full max-w-[980px]">
               <div className="chart-frame">
                  {/* top bar */}
                  <div className="flex items-center justify-between px-[18px] py-3 border-b border-white/[0.07] bg-white/[0.015] flex-wrap gap-2">
                     <div className="flex items-center gap-[10px]">
                        {/* traffic lights */}
                        <div className="flex gap-[5px]">
                           <div className="w-[10px] h-[10px] rounded-full bg-[#ff5f57]" />
                           <div className="w-[10px] h-[10px] rounded-full bg-[#febc2e]" />
                           <div className="w-[10px] h-[10px] rounded-full bg-[#28c840]" />
                        </div>
                        <span className="text-[13px] font-semibold tracking-[0.02em] text-[var(--text)]">NVDA</span>
                        <span className="text-[13px] font-medium tabular-nums text-[#22d07a]">$875.40</span>
                        <span className="text-[11px] font-semibold bg-[rgba(34,208,122,0.12)] text-[#22d07a] px-2 py-[2px] rounded-full">
                           +5.61%
                        </span>
                     </div>

                     {/* timeframe pills — hidden on very small screens */}
                     <div className="flex gap-1 max-[480px]:hidden">
                        {["1m", "5m", "15m", "1H", "4H", "1D"].map((tf, i) => (
                           <button key={tf} className={`tf-pill${i === 3 ? " active" : ""}`}>
                              {tf}
                           </button>
                        ))}
                     </div>
                  </div>

                  {/* chart body */}
                  <div className="h-[340px] max-md:h-[220px] max-[480px]:h-[180px]">
                     <CandlestickChart />
                  </div>
               </div>
            </div>
         </div>
      </div>
   );
};

export default Hero;
