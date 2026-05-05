import React, { useEffect, useState } from "react";
import CandlestickChart from "./CandleStickChart";

// ── Hero ──────────────────────────────────────────────────────────────────────
const Hero = () => {
   const [mounted, setMounted] = useState(false);
   useEffect(() => {
      const t = setTimeout(() => setMounted(true), 60);
      return () => clearTimeout(t);
   }, []);

   return (
      <>
         <style>{`
        @import url('https://fonts.googleapis.com/css2?family=Instrument+Serif:ital@0;1&family=DM+Sans:wght@300;400;500;600&display=swap');


        :root {
          --bg:        #05070d;
          --surface:   #0b0f1a;
          --border:    rgba(255,255,255,0.07);
          --border-hi: rgba(255,255,255,0.14);
          --green:     #22d07a;
          --green-dim: rgba(34,208,122,0.12);
          --red:       #f04b5a;
          --text:      #e8eaf2;
          --muted:     #5a607a;
          --accent:    #3b82f6;
        }

        body { background: var(--bg); color: var(--text); }

        /* ── background atmosphere ── */
        .hero-glow {
          position: absolute;
          inset: 0;
          pointer-events: none;
          z-index: 0;
        }
        .hero-glow::before {
          content: '';
          position: absolute;
          top: -10%;
          left: 50%;
          transform: translateX(-50%);
          width: 900px;
          height: 600px;
          background: radial-gradient(ellipse at center,
            rgba(34,208,122,0.08) 0%,
            rgba(59,130,26,0.05) 40%,
            transparent 70%);
          filter: blur(60px);
        }
        .hero-glow::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          height: 40%;
          background: linear-gradient(to top, var(--bg), transparent);
        }

        .hero-grid {
          position: absolute;
          inset: 0;
          z-index: 0;
          background-image:
            linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
          background-size: 60px 60px;
          mask-image: radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%);
        }

        /* ── eyebrow dot pulse ── */
        .eyebrow-dot {
          width: 6px; height: 6px;
          border-radius: 50%;
          background: var(--green);
          box-shadow: 0 0 6px var(--green);
          animation: pulse 2s ease-in-out infinite;
        }
        @keyframes pulse {
          0%,100% { opacity: 1; }
          50%      { opacity: 0.4; }
        }

        /* ── animations ── */
        @keyframes fadeUp {
          to { opacity: 1; transform: translateY(0); }
        }

        /* ── animated elements ── */
        .anim-eyebrow {
          opacity: 0;
          transform: translateY(10px);
          animation: fadeUp 0.6s ease forwards;
          animation-delay: 0.1s;
        }
        .anim-headline {
          opacity: 0;
          transform: translateY(14px);
          animation: fadeUp 0.7s ease forwards;
          animation-delay: 0.2s;
        }
        .anim-sub {
          opacity: 0;
          transform: translateY(12px);
          animation: fadeUp 0.7s ease forwards;
          animation-delay: 0.35s;
        }
        .anim-cta {
          opacity: 0;
          transform: translateY(10px);
          animation: fadeUp 0.6s ease forwards;
          animation-delay: 0.5s;
        }
        .anim-chart {
          opacity: 0;
          transform: translateY(24px);
          animation: fadeUp 0.9s ease forwards;
          animation-delay: 0.65s;
        }
        .stat-pill {
          opacity: 0;
          transform: translateY(8px);
          animation: fadeUp 0.6s ease forwards;
        }
        .anim-social {
          opacity: 0;
          animation: fadeUp 0.6s ease forwards;
          animation-delay: 1.1s;
        }

        /* ── chart frame glow + fade ── */
        .chart-frame {
          position: relative;
          border: 1px solid var(--border-hi);
          border-radius: 16px;
          overflow: hidden;
          background: #080a0e;
          box-shadow:
            0 0 0 1px rgba(255,255,255,0.04),
            0 32px 80px rgba(0,0,0,0.6),
            0 0 60px rgba(34,208,122,0.04);
        }
        .chart-frame::after {
          content: '';
          position: absolute;
          bottom: 0; left: 0; right: 0;
          height: 60px;
          background: linear-gradient(to top, #080a0e, transparent);
          pointer-events: none;
        }

        /* ── tf-pill active ── */
        .tf-pill {
          font-size: 11px;
          font-weight: 500;
          color: var(--muted);
          padding: 3px 9px;
          border-radius: 6px;
          cursor: pointer;
          transition: background 0.15s, color 0.15s;
          border: none;
          background: none;
          font-family: 'DM Sans', sans-serif;
        }
        .tf-pill:hover { background: rgba(255,255,255,0.06); color: var(--text); }
        .tf-pill.active {
          background: rgba(34,208,122,0.1);
          color: var(--green);
        }

        /* ── buttons ── */
        .btn-hero {
          background: var(--green);
          border: none;
          color: #000;
          font-family: 'DM Sans', sans-serif;
          font-size: 15px;
          font-weight: 600;
          padding: 14px 32px;
          border-radius: 10px;
          cursor: pointer;
          transition: opacity 0.2s, transform 0.15s, box-shadow 0.2s;
          box-shadow: 0 0 28px rgba(34,208,122,0.25);
        }
        .btn-hero:hover {
          opacity: 0.9;
          transform: translateY(-2px);
          box-shadow: 0 4px 36px rgba(34,208,122,0.35);
        }
        .btn-hero-ghost {
          background: none;
          border: 1px solid var(--border-hi);
          color: var(--text);
          font-family: 'DM Sans', sans-serif;
          font-size: 15px;
          font-weight: 500;
          padding: 14px 28px;
          border-radius: 10px;
          cursor: pointer;
          transition: background 0.2s, border-color 0.2s, transform 0.15s;
          display: flex;
          align-items: center;
          gap: 8px;
        }
        .btn-hero-ghost:hover {
          background: rgba(255,255,255,0.04);
          border-color: rgba(255,255,255,0.2);
          transform: translateY(-1px);
        }

        /* ── responsive ── */
        @media (max-width: 768px) {
          .hero-content { padding: 48px 16px 40px; }
          .chart-inner { height: 220px; }
          .stats-row { gap: 8px; }
          .stat-pill { padding: 7px 12px; }
        }
        @media (max-width: 480px) {
          .hero-cta-row { flex-direction: column; width: 100%; }
          .btn-hero, .btn-hero-ghost { width: 100%; justify-content: center; }
          .chart-topbar-right { display: none; }
          .chart-inner { height: 180px; }
        }
      `}</style>

         {/* ── Hero wrapper ── */}
         <div
            className="relative overflow-hidden flex flex-col"
            style={{ fontFamily: "'DM Sans', sans-serif", background: "var(--bg)" }}>
            {/* atmosphere */}
            <div className="hero-glow" />
            <div className="hero-grid" />

            {/* ── main content ── */}
            <div className="hero-content relative z-[5] flex flex-col items-center px-6 pt-[72px]">
               <div className="anim-eyebrow inline-flex items-center gap-[7px] border border-[rgba(34,208,122,0.25)] bg-[rgba(34,208,122,0.06)] rounded-full px-[14px] py-[5px] pl-[9px] text-xs font-medium text-[#22d07a] mb-7">
                  <div className="eyebrow-dot" />
                  <span>Early Access 🚀</span>
               </div>

               {/* headline */}
               <h1
                  className="anim-headline text-center max-w-[820px] mb-[22px]"
                  style={{
                     fontFamily: "'Instrument Serif', serif",
                     fontSize: "clamp(42px, 7vw, 82px)",
                     lineHeight: 1.05,
                     letterSpacing: "-0.03em",
                     color: "var(--text)",
                  }}>
                  Stalk the Stock.
                  <br />
                  <em className="not-italic tracking-tighter" style={{ color: "var(--green)" }}>
                     Before it moves.
                  </em>
               </h1>

               {/* sub */}
               <p
                  className="anim-sub text-center max-w-[520px] leading-[1.65] font-normal mb-9"
                  style={{
                     fontSize: "clamp(15px, 1.8vw, 18px)",
                     color: "var(--muted)",
                  }}>
                  All your portfolio tracking in one place. Smart buy/sell signals powered by proven strategies.
               </p>

               {/* CTAs */}
               <div className="anim-cta hero-cta-row flex items-center gap-[14px] mb-16">
                  <button className="btn-hero">Start for free</button>
                  <button className="btn-hero-ghost">
                     <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <circle cx="8" cy="8" r="7" stroke="currentColor" strokeWidth="1.2" />
                        <path d="M6.5 5.5L10.5 8L6.5 10.5V5.5Z" fill="currentColor" />
                     </svg>
                     Watch Demo
                  </button>
               </div>

               {/* chart */}
               <div className="anim-chart chart-shell w-full max-w-[980px]">
                  <div className="chart-frame">
                     {/* top bar */}
                     <div className="flex items-center justify-between px-[18px] py-3 border-b border-white/[0.07] bg-white/[0.015] flex-wrap gap-2">
                        <div className="flex items-center gap-[10px]">
                           <div className="flex gap-[5px]">
                              <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#ff5f57" }} />
                              <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#febc2e" }} />
                              <div className="w-[10px] h-[10px] rounded-full" style={{ background: "#28c840" }} />
                           </div>
                           <span
                              className="text-[13px] font-semibold tracking-[0.02em]"
                              style={{ color: "var(--text)" }}>
                              NVDA
                           </span>
                           <span className="text-[13px] font-medium tabular-nums text-[#22d07a]">$875.40</span>
                           <span className="text-[11px] font-semibold bg-[rgba(34,208,122,0.12)] text-[#22d07a] px-2 py-[2px] rounded-full">
                              +5.61%
                           </span>
                        </div>
                        <div className="chart-topbar-right flex gap-1">
                           {["1m", "5m", "15m", "1H", "4H", "1D"].map((tf, i) => (
                              <button key={tf} className={`tf-pill${i === 3 ? " active" : ""}`}>
                                 {tf}
                              </button>
                           ))}
                        </div>
                     </div>
                     <div className="chart-inner" style={{ height: 340 }}>
                        <CandlestickChart />
                     </div>
                  </div>
               </div>
            </div>
         </div>
      </>
   );
};

export default Hero;
