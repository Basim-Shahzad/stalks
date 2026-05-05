import { useState, useRef, useEffect, useCallback } from "react";

// ─── Types ────────────────────────────────────────────────────────────────────

interface Candle {
   open: number;
   close: number;
   high: number;
   low: number;
   volume: number;
   time: number;
}

interface Tooltip {
   x: number;
   y: number;
   candle: Candle;
   isUp: boolean;
   date: string;
}

interface Dims {
   w: number;
   h: number;
}

// ─── Dummy Data ───────────────────────────────────────────────────────────────

function generateCandles(count = 120): Candle[] {
   const candles: Candle[] = [];
   let price = 42000;
   const now = Date.now();

   for (let i = count - 1; i >= 0; i--) {
      const open = price;
      const change = (Math.random() - 0.48) * price * 0.025;
      const close = Math.max(open + change, open * 0.97);
      const high = Math.max(open, close) + Math.random() * Math.abs(change) * 1.5;
      const low = Math.min(open, close) - Math.random() * Math.abs(change) * 1.5;
      const volume = Math.random() * 100 + 20;
      candles.push({ open, close, high, low, volume, time: now - i * 60000 * 15 });
      price = close;
   }

   return candles;
}

const DUMMY_CANDLES = generateCandles(120);

// ─── Component ────────────────────────────────────────────────────────────────

interface CandlestickChartProps {
   candles?: Candle[];
}

export default function CandlestickChart({ candles = DUMMY_CANDLES }: CandlestickChartProps) {
   const canvasRef = useRef<HTMLCanvasElement>(null);
   const containerRef = useRef<HTMLDivElement>(null);

   const [dims, setDims] = useState<Dims>({ w: 800, h: 500 });
   const [offset, setOffset] = useState(0);
   const [zoom, setZoom] = useState(1);
   const [tooltip, setTooltip] = useState<Tooltip | null>(null);
   const [isDragging, setIsDragging] = useState(false);
   const isHoveredRef = useRef(false);

   const dragStart = useRef<{ x: number; offset: number } | null>(null);
   const offsetRef = useRef(0);
   const zoomRef = useRef(1);
   const dimsRef = useRef(dims);
   const touchRef = useRef<{
      touches?: number;
      offset?: number;
      dist?: number | null;
      zoomStart?: number;
   }>({});

   useEffect(() => {
      offsetRef.current = offset;
   }, [offset]);
   useEffect(() => {
      zoomRef.current = zoom;
   }, [zoom]);
   useEffect(() => {
      dimsRef.current = dims;
   }, [dims]);

   // ── Resize Observer ──────────────────────────────────────────────────────
   useEffect(() => {
      const el = containerRef.current;
      if (!el) return;
      const ro = new ResizeObserver((entries) => {
         const { width, height } = entries[0].contentRect;
         setDims({ w: width, h: height });
      });
      ro.observe(el);
      return () => ro.disconnect();
   }, []);

   // ── Wheel — native listener so preventDefault actually blocks page scroll ─
   useEffect(() => {
      const el = containerRef.current;
      if (!el) return;

      const onWheel = (e: WheelEvent) => {
         if (!isHoveredRef.current) return;
         e.preventDefault();
         e.stopPropagation();

         const { w } = dimsRef.current;
         const factor = e.deltaY < 0 ? 1.1 : 0.91;
         const rect = el.getBoundingClientRect();
         const mx = e.clientX - rect.left;
         const oldZoom = zoomRef.current;
         const newZoom = Math.min(8, Math.max(0.3, oldZoom * factor));

         const candleWOld = Math.max(2, (w / candles.length) * oldZoom);
         const candleWNew = Math.max(2, (w / candles.length) * newZoom);
         const ratio = candleWNew / candleWOld;
         const newOff = mx - (mx - offsetRef.current) * ratio;

         zoomRef.current = newZoom;
         offsetRef.current = newOff;
         setZoom(newZoom);
         setOffset(newOff);
      };

      // { passive: false } is required to allow preventDefault
      el.addEventListener("wheel", onWheel, { passive: false });
      return () => el.removeEventListener("wheel", onWheel);
   }, [candles]);

   // ── Draw ─────────────────────────────────────────────────────────────────
   const draw = useCallback(() => {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const dpr = window.devicePixelRatio || 1;
      const { w, h } = dims;

      canvas.width = w * dpr;
      canvas.height = h * dpr;
      canvas.style.width = `${w}px`;
      canvas.style.height = `${h}px`;

      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.scale(dpr, dpr);

      const off = offsetRef.current;
      const zm = zoomRef.current;

      // Responsive padding
      const isMobile = w < 480;
      const pad = {
         top: isMobile ? 10 : 18,
         bottom: isMobile ? 20 : 32,
         right: isMobile ? 42 : 54,
      };
      const chartH = h - pad.top - pad.bottom;
      const chartW = w - pad.right;
      const candleW = Math.max(2, (chartW / candles.length) * zm);

      // Visible range
      const startIdx = Math.max(0, Math.floor(-off / candleW));
      const endIdx = Math.min(candles.length - 1, Math.ceil((chartW - off) / candleW));
      const visible = candles.slice(startIdx, endIdx + 1);
      if (!visible.length) return;

      const maxP = Math.max(...visible.map((c) => c.high));
      const minP = Math.min(...visible.map((c) => c.low));
      const range = maxP - minP || 1;
      const pricePad = range * 0.06;

      const toY = (p: number) => pad.top + chartH - ((p - (minP - pricePad)) / (range + pricePad * 2)) * chartH;
      const toX = (idx: number) => off + idx * candleW + candleW / 2;

      // Background
      ctx.fillStyle = "#000000";
      ctx.fillRect(0, 0, w, h);

      // Grid
      const levels = isMobile ? 4 : 6;
      for (let i = 0; i <= levels; i++) {
         const y = pad.top + (chartH / levels) * i;
         const p = maxP + pricePad - (i / levels) * (range + pricePad * 2);

         ctx.strokeStyle = "#0e111a";
         ctx.lineWidth = 1;
         ctx.beginPath();
         ctx.moveTo(0, y);
         ctx.lineTo(chartW, y);
         ctx.stroke();

         ctx.fillStyle = "#283050";
         ctx.font = `${isMobile ? 9 : 10}px monospace`;
         ctx.textAlign = "left";
         ctx.fillText(p.toFixed(0), chartW + 4, y + 4);
      }

      // Candles
      visible.forEach((c, i) => {
         const idx = startIdx + i;
         const x = toX(idx);
         const isUp = c.close >= c.open;
         const color = isUp ? "#26a69a" : "#ef5350";
         const bodyTop = toY(Math.max(c.open, c.close));
         const bodyBot = toY(Math.min(c.open, c.close));
         const bodyH = Math.max(1, bodyBot - bodyTop);
         const wickX = Math.round(x);
         const bw = Math.max(1, candleW * 0.65);

         ctx.strokeStyle = color;
         ctx.lineWidth = Math.max(1, candleW * 0.08);
         ctx.beginPath();
         ctx.moveTo(wickX, toY(c.high));
         ctx.lineTo(wickX, toY(c.low));
         ctx.stroke();

         ctx.fillStyle = isUp ? "rgba(38,166,154,0.85)" : "rgba(239,83,80,0.85)";
         ctx.fillRect(Math.round(x - bw / 2), bodyTop, Math.round(bw), bodyH);

         ctx.strokeStyle = color;
         ctx.lineWidth = 0.5;
         ctx.strokeRect(Math.round(x - bw / 2), bodyTop, Math.round(bw), bodyH);
      });
   }, [dims, candles]);

   useEffect(() => {
      draw();
   }, [draw, offset, zoom, dims]);

   // ── Mouse Events ─────────────────────────────────────────────────────────
   const handleMouseDown = useCallback((e: React.MouseEvent) => {
      setIsDragging(true);
      dragStart.current = { x: e.clientX, offset: offsetRef.current };
   }, []);

   const handleMouseMove = useCallback(
      (e: React.MouseEvent) => {
         if (isDragging && dragStart.current) {
            const dx = e.clientX - dragStart.current.x;
            let newOff = dragStart.current.offset + dx;
            const candleW = Math.max(2, (dims.w / candles.length) * zoomRef.current);
            const maxOff = candleW * 10;
            const minOff = -(candles.length * candleW - dims.w * 0.3);
            newOff = Math.min(maxOff, Math.max(minOff, newOff));
            setOffset(newOff);
         }

         const rect = canvasRef.current?.getBoundingClientRect();
         if (!rect) return;
         const mx = e.clientX - rect.left;
         const candleW = Math.max(2, (dims.w / candles.length) * zoomRef.current);
         const idx = Math.round((mx - offsetRef.current) / candleW);
         const c = candles[idx];

         if (c && idx >= 0 && idx < candles.length) {
            const isUp = c.close >= c.open;
            setTooltip({
               x: Math.min(mx + 12, dims.w - 150),
               y: Math.max(e.clientY - rect.top - 80, 10),
               candle: c,
               isUp,
               date: new Date(c.time).toLocaleString("en-US", {
                  month: "short",
                  day: "numeric",
                  hour: "2-digit",
                  minute: "2-digit",
               }),
            });
         } else {
            setTooltip(null);
         }
      },
      [isDragging, dims, candles],
   );

   const handleMouseUp = useCallback(() => {
      setIsDragging(false);
      dragStart.current = null;
   }, []);

   const handleMouseEnter = useCallback(() => {
      isHoveredRef.current = true;
   }, []);

   const handleMouseLeave = useCallback(() => {
      isHoveredRef.current = false;
      setIsDragging(false);
      dragStart.current = null;
      setTooltip(null);
   }, []);

   // ── Touch Events ─────────────────────────────────────────────────────────
   const handleTouchStart = useCallback((e: React.TouchEvent) => {
      if (e.touches.length === 1) {
         touchRef.current = {
            touches: e.touches[0].clientX,
            offset: offsetRef.current,
            dist: null,
         };
      } else if (e.touches.length === 2) {
         const dx = e.touches[0].clientX - e.touches[1].clientX;
         const dy = e.touches[0].clientY - e.touches[1].clientY;
         touchRef.current.dist = Math.sqrt(dx * dx + dy * dy);
         touchRef.current.zoomStart = zoomRef.current;
      }
   }, []);

   const handleTouchMove = useCallback(
      (e: React.TouchEvent) => {
         e.preventDefault();
         if (e.touches.length === 1 && touchRef.current.touches != null) {
            const dx = e.touches[0].clientX - touchRef.current.touches;
            let newOff = (touchRef.current.offset ?? 0) + dx;
            const candleW = Math.max(2, (dims.w / candles.length) * zoomRef.current);
            newOff = Math.min(candleW * 10, Math.max(-(candles.length * candleW - dims.w * 0.3), newOff));
            setOffset(newOff);
         } else if (e.touches.length === 2 && touchRef.current.dist) {
            const dx = e.touches[0].clientX - e.touches[1].clientX;
            const dy = e.touches[0].clientY - e.touches[1].clientY;
            const newDist = Math.sqrt(dx * dx + dy * dy);
            const factor = newDist / touchRef.current.dist;
            setZoom(Math.min(8, Math.max(0.3, (touchRef.current.zoomStart ?? 1) * factor)));
         }
      },
      [dims, candles],
   );

   // ── Render ────────────────────────────────────────────────────────────────
   return (
      <div
         ref={containerRef}
         style={{
            width: "100%",
            height: "100%",
            minHeight: 200,
            position: "relative",
            overflow: "hidden",
            borderRadius: 8,
            background: "#000000",
            cursor: isDragging ? "grabbing" : "grab",
            userSelect: "none",
            touchAction: "none",
         }}
         onMouseDown={handleMouseDown}
         onMouseMove={handleMouseMove}
         onMouseUp={handleMouseUp}
         onMouseEnter={handleMouseEnter}
         onMouseLeave={handleMouseLeave}
         onTouchStart={handleTouchStart}
         onTouchMove={handleTouchMove}
         onTouchEnd={() => {
            touchRef.current = {};
         }}>
         <canvas ref={canvasRef} style={{ display: "block" }} />
      </div>
   );
}
