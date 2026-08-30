"use client";

import React, { useRef, useEffect, useState, useCallback, useMemo } from "react";

/**
 * CandlestickChart
 * -----------------
 * A zero-dependency, canvas-rendered candlestick chart with:
 *  - Smooth zoom (wheel / pinch)
 *  - Drag-to-pan
 *  - Crosshair + OHLCV tooltip
 *  - Volume panel
 *  - High-DPI (retina) rendering
 *  - Virtualized drawing — only visible candles are ever painted,
 *    so it stays fast even with tens of thousands of bars.
 *
 * Drop this file into any React + TypeScript project. No external
 * charting library required.
 */

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface OHLCV {
   date: string; // ISO date string, e.g. "2023-05-22T00:00:00"
   open: number;
   high: number;
   low: number;
   close: number;
   volume: number;
}

interface ParsedCandle extends OHLCV {
   time: number; // epoch ms, parsed once up front
}

export interface CandlestickChartProps {
   data: OHLCV[];
   /** Pixel width. Defaults to 100% of parent via ResizeObserver. */
   width?: number;
   /** Pixel height. Defaults to 100% of parent via ResizeObserver. */
   height?: number;
   /** Ticker symbol / title shown top-left. */
   symbol?: string;
   /** Show the volume histogram panel beneath price. Default true. */
   showVolume?: boolean;
   /** Bullish (close >= open) candle color. */
   upColor?: string;
   /** Bearish (close < open) candle color. */
   downColor?: string;
   /** Background color. */
   backgroundColor?: string;
   /** Grid line color. */
   gridColor?: string;
   /** Text color. */
   textColor?: string;
   className?: string;
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

const clamp = (v: number, min: number, max: number) => Math.min(max, Math.max(min, v));

function formatDate(ms: number, rangeMs: number): string {
   const d = new Date(ms);
   // Choose label granularity based on the visible time range.
   if (rangeMs < 1000 * 60 * 60 * 24 * 3) {
      return d.toLocaleTimeString(undefined, {
         hour: "2-digit",
         minute: "2-digit",
      });
   }
   if (rangeMs < 1000 * 60 * 60 * 24 * 365) {
      return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
   }
   return d.toLocaleDateString(undefined, { month: "short", year: "numeric" });
}

function formatPrice(p: number): string {
   if (p >= 1000) return p.toFixed(1);
   if (p >= 1) return p.toFixed(2);
   return p.toFixed(4);
}

function formatVolume(v: number): string {
   if (v >= 1_000_000) return (v / 1_000_000).toFixed(2) + "M";
   if (v >= 1_000) return (v / 1_000).toFixed(1) + "K";
   return String(v);
}

function niceStep(rough: number): number {
   const pow = Math.pow(10, Math.floor(Math.log10(rough)));
   const candidates = [1, 2, 2.5, 5, 10];
   let best = pow;
   for (const c of candidates) {
      const step = c * pow;
      if (rough / step <= 8) {
         best = step;
         break;
      }
      best = step;
   }
   return best;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CandlestickChart({
   data,
   width,
   height,
   symbol = "",
   showVolume = true,
   upColor = "#26a69a",
   downColor = "#ef5350",
   backgroundColor = "#0b0e11",
   gridColor = "rgba(255,255,255,0.06)",
   textColor = "rgba(255,255,255,0.55)",
   className,
}: CandlestickChartProps) {
   const containerRef = useRef<HTMLDivElement>(null);
   const canvasRef = useRef<HTMLCanvasElement>(null);
   const rafRef = useRef<number | null>(null);

   const [size, setSize] = useState({ width: width ?? 800, height: height ?? 480 });

   // Parse + sort the incoming data once. This is the only O(n log n) work;
   // everything in the render loop afterward is O(visible candles).
   const candles: ParsedCandle[] = useMemo(() => {
      const parsed = data?.map((d) => ({ ...d, time: new Date(d.date).getTime() }));
      parsed?.sort((a, b) => a.time - b.time);
      return parsed;
   }, [data]);

   // View state: index range currently visible (fractional, for smooth zoom),
   // expressed as [startIndex, endIndex] into `candles`.
   const [view, setView] = useState<{ start: number; end: number }>(() => {
      const n = data?.length;
      const visible = Math.min(120, n);
      return { start: Math.max(0, n - visible), end: Math.max(1, n) };
   });

   // Re-clamp view whenever data changes (e.g. new ticker loaded).
   useEffect(() => {
      const n = candles?.length;
      const visible = Math.min(120, n);
      setView({ start: Math.max(0, n - visible), end: Math.max(1, n) });
   }, [candles?.length]);

   // Crosshair / hover state.
   const [hover, setHover] = useState<{ x: number; y: number } | null>(null);

   // Drag state (refs so we don't re-render on every mousemove).
   const dragRef = useRef<{
      dragging: boolean;
      startX: number;
      startView: { start: number; end: number };
   }>({ dragging: false, startX: 0, startView: { start: 0, end: 0 } });

   // -------------------------------------------------------------------------
   // Responsive sizing
   // -------------------------------------------------------------------------
   useEffect(() => {
      if (width && height) {
         setSize({ width, height });
         return;
      }
      const el = containerRef.current;
      if (!el) return;
      const ro = new ResizeObserver((entries) => {
         const entry = entries[0];
         if (!entry) return;
         const { width: w, height: h } = entry.contentRect;
         setSize({
            width: width ?? Math.max(200, Math.floor(w)),
            height: height ?? Math.max(200, Math.floor(h)),
         });
      });
      ro.observe(el);
      return () => ro.disconnect();
   }, [width, height]);

   // -------------------------------------------------------------------------
   // Layout constants
   // -------------------------------------------------------------------------
   const layout = useMemo(() => {
      const priceAxisWidth = 72;
      const timeAxisHeight = 28;
      const volumeHeight = showVolume ? Math.round(size.height * 0.18) : 0;
      const priceHeight = size.height - timeAxisHeight - volumeHeight;
      return {
         priceAxisWidth,
         timeAxisHeight,
         volumeHeight,
         priceHeight,
         plotWidth: size.width - priceAxisWidth,
         volumeTop: priceHeight,
      };
   }, [size, showVolume]);

   // -------------------------------------------------------------------------
   // Drawing
   // -------------------------------------------------------------------------
   const draw = useCallback(() => {
      const canvas = canvasRef.current;
      if (!canvas || candles?.length === 0) return;
      const dpr = window.devicePixelRatio || 1;
      const { width: w, height: h } = size;

      if (canvas.width !== w * dpr || canvas.height !== h * dpr) {
         canvas.width = w * dpr;
         canvas.height = h * dpr;
      }
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      ctx.save();
      ctx.scale(dpr, dpr);
      ctx.clearRect(0, 0, w, h);
      ctx.fillStyle = backgroundColor;
      ctx.fillRect(0, 0, w, h);

      const { priceAxisWidth, timeAxisHeight, priceHeight, volumeHeight, plotWidth, volumeTop } = layout;

      const start = clamp(Math.floor(view.start), 0, candles?.length - 1);
      const end = clamp(Math.ceil(view.end), start + 1, candles?.length);
      const visibleCount = end - start;
      const candleSlotWidth = plotWidth / (view.end - view.start);
      const bodyWidth = Math.max(1, candleSlotWidth * 0.62);

      // ---- Compute visible price + volume ranges ----
      let minPrice = Infinity;
      let maxPrice = -Infinity;
      let maxVolume = 0;
      for (let i = start; i < end; i++) {
         const c = candles[i];
         if (c.low < minPrice) minPrice = c.low;
         if (c.high > maxPrice) maxPrice = c.high;
         if (c.volume > maxVolume) maxVolume = c.volume;
      }
      if (!isFinite(minPrice) || !isFinite(maxPrice)) {
         ctx.restore();
         return;
      }
      const pricePadding = (maxPrice - minPrice) * 0.08 || maxPrice * 0.01 || 1;
      minPrice -= pricePadding;
      maxPrice += pricePadding;
      const priceRange = maxPrice - minPrice || 1;

      const xForIndex = (i: number) => (i - view.start) * candleSlotWidth;
      const yForPrice = (p: number) => priceHeight - ((p - minPrice) / priceRange) * priceHeight;
      const yForVolume = (v: number) => volumeTop + volumeHeight - (v / (maxVolume || 1)) * (volumeHeight * 0.92);

      // ---- Grid + price axis labels ----
      ctx.strokeStyle = gridColor;
      ctx.lineWidth = 1;
      ctx.fillStyle = textColor;
      ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
      ctx.textBaseline = "middle";

      const step = niceStep(priceRange / 5);
      const firstGridPrice = Math.ceil(minPrice / step) * step;
      for (let p = firstGridPrice; p <= maxPrice; p += step) {
         const y = yForPrice(p);
         ctx.beginPath();
         ctx.moveTo(0, y);
         ctx.lineTo(plotWidth, y);
         ctx.stroke();
         ctx.textAlign = "left";
         ctx.fillText(formatPrice(p), plotWidth + 8, y);
      }

      // Vertical (time) grid lines — aim for ~6 labels across the plot.
      const labelEvery = Math.max(1, Math.round(visibleCount / 6));
      ctx.textAlign = "center";
      const rangeMs = candles[end - 1].time - candles[Math.max(start, 0)].time || 1;
      for (let i = start; i < end; i += labelEvery) {
         const x = xForIndex(i) + candleSlotWidth / 2;
         ctx.beginPath();
         ctx.moveTo(x, 0);
         ctx.lineTo(x, priceHeight + volumeHeight);
         ctx.stroke();
         ctx.fillText(formatDate(candles[i].time, rangeMs), x, priceHeight + volumeHeight + timeAxisHeight / 2);
      }

      // ---- Volume bars ----
      if (showVolume) {
         for (let i = start; i < end; i++) {
            const c = candles[i];
            const x = xForIndex(i) + (candleSlotWidth - bodyWidth) / 2;
            const up = c.close >= c.open;
            ctx.fillStyle = up ? hexAlpha(upColor, 0.5) : hexAlpha(downColor, 0.5);
            const yTop = yForVolume(c.volume);
            ctx.fillRect(x, yTop, bodyWidth, volumeTop + volumeHeight - yTop);
         }
      }

      // ---- Candles ----
      for (let i = start; i < end; i++) {
         const c = candles[i];
         const xCenter = xForIndex(i) + candleSlotWidth / 2;
         const xLeft = xCenter - bodyWidth / 2;
         const up = c.close >= c.open;
         const color = up ? upColor : downColor;

         const yHigh = yForPrice(c.high);
         const yLow = yForPrice(c.low);
         const yOpen = yForPrice(c.open);
         const yClose = yForPrice(c.close);
         const yBodyTop = Math.min(yOpen, yClose);
         const yBodyBottom = Math.max(yOpen, yClose);

         ctx.strokeStyle = color;
         ctx.fillStyle = color;
         ctx.lineWidth = Math.max(1, Math.min(1.5, candleSlotWidth * 0.08));

         // Wick
         ctx.beginPath();
         ctx.moveTo(xCenter, yHigh);
         ctx.lineTo(xCenter, yLow);
         ctx.stroke();

         // Body
         const bodyH = Math.max(1, yBodyBottom - yBodyTop);
         ctx.fillRect(xLeft, yBodyTop, bodyWidth, bodyH);
      }

      // ---- Crosshair + tooltip ----
      if (hover && hover.x >= 0 && hover.x <= plotWidth) {
         const idx = clamp(Math.floor(view.start + hover.x / candleSlotWidth), 0, candles?.length - 1);
         const c = candles[idx];
         const xCenter = xForIndex(idx) + candleSlotWidth / 2;

         ctx.strokeStyle = "rgba(255,255,255,0.25)";
         ctx.setLineDash([3, 3]);
         ctx.lineWidth = 1;
         ctx.beginPath();
         ctx.moveTo(xCenter, 0);
         ctx.lineTo(xCenter, priceHeight + volumeHeight);
         ctx.stroke();
         ctx.beginPath();
         ctx.moveTo(0, hover.y);
         ctx.lineTo(plotWidth, hover.y);
         ctx.stroke();
         ctx.setLineDash([]);

         // Price label on axis at cursor height
         const hoveredPrice = minPrice + (1 - hover.y / priceHeight) * priceRange;
         ctx.fillStyle = "#1c2128";
         ctx.fillRect(plotWidth, hover.y - 10, priceAxisWidth, 20);
         ctx.fillStyle = "#e6e6e6";
         ctx.textAlign = "left";
         ctx.fillText(formatPrice(hoveredPrice), plotWidth + 8, hover.y);

         // OHLCV info box, top-left of plot
         const up = c.close >= c.open;
         const changeColor = up ? upColor : downColor;
         const boxLines = [
            `O ${formatPrice(c.open)}  H ${formatPrice(c.high)}  L ${formatPrice(c.low)}  C ${formatPrice(c.close)}`,
            `Vol ${formatVolume(c.volume)}   ${new Date(c.time).toLocaleString()}`,
         ];
         ctx.font = "12px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
         ctx.textAlign = "left";
         ctx.fillStyle = changeColor;
         ctx.fillText(boxLines[0], 12, 16);
         ctx.fillStyle = "rgba(255,255,255,0.5)";
         ctx.font = "11px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
         ctx.fillText(boxLines[1], 12, 34);
      } else {
         // Default header: symbol + latest OHLCV
         const last = candles[candles?.length - 1];
         const up = last.close >= last.open;
         ctx.font = "13px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
         ctx.textAlign = "left";
         ctx.fillStyle = "#e6e6e6";
         ctx.fillText(symbol, 12, 16);
         ctx.font = "12px -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
         ctx.fillStyle = up ? upColor : downColor;
         ctx.fillText(
            `O ${formatPrice(last.open)}  H ${formatPrice(last.high)}  L ${formatPrice(
               last.low,
            )}  C ${formatPrice(last.close)}`,
            12,
            34,
         );
      }

      ctx.restore();
   }, [
      candles,
      size,
      layout,
      view,
      hover,
      upColor,
      downColor,
      backgroundColor,
      gridColor,
      textColor,
      showVolume,
      symbol,
   ]);

   // Schedule a draw on a rAF so rapid wheel/drag events coalesce to one
   // paint per frame.
   const scheduleDraw = useCallback(() => {
      if (rafRef.current != null) return;
      rafRef.current = requestAnimationFrame(() => {
         rafRef.current = null;
         draw();
      });
   }, [draw]);

   useEffect(() => {
      scheduleDraw();
   }, [scheduleDraw]);

   // -------------------------------------------------------------------------
   // Interaction: wheel to zoom, drag to pan
   // -------------------------------------------------------------------------
   const onWheel = useCallback(
      (e: React.WheelEvent<HTMLCanvasElement>) => {
         e.preventDefault();
         const canvas = canvasRef.current;
         if (!canvas) return;
         const rect = canvas.getBoundingClientRect();
         const cursorX = e.clientX - rect.left;

         setView((prev) => {
            const span = prev.end - prev.start;
            const zoomFactor = Math.exp(e.deltaY * 0.0015);
            const minSpan = 8;
            const maxSpan = candles?.length;
            let newSpan = clamp(span * zoomFactor, minSpan, maxSpan);

            // Keep the point under the cursor stationary while zooming.
            const plotWidth = layout.plotWidth;
            const cursorRatio = clamp(cursorX / plotWidth, 0, 1);
            const cursorIndex = prev.start + cursorRatio * span;

            let newStart = cursorIndex - cursorRatio * newSpan;
            let newEnd = newStart + newSpan;

            if (newStart < 0) {
               newEnd -= newStart;
               newStart = 0;
            }
            if (newEnd > candles?.length) {
               newStart -= newEnd - candles?.length;
               newEnd = candles?.length;
            }
            newStart = Math.max(0, newStart);

            return { start: newStart, end: newEnd };
         });
      },
      [candles?.length, layout.plotWidth],
   );

   const onPointerDown = useCallback(
      (e: React.PointerEvent<HTMLCanvasElement>) => {
         (e.target as HTMLElement).setPointerCapture(e.pointerId);
         dragRef.current = { dragging: true, startX: e.clientX, startView: view };
      },
      [view],
   );

   const onPointerMove = useCallback(
      (e: React.PointerEvent<HTMLCanvasElement>) => {
         const canvas = canvasRef.current;
         if (!canvas) return;
         const rect = canvas.getBoundingClientRect();
         const x = e.clientX - rect.left;
         const y = e.clientY - rect.top;
         setHover({ x, y });

         if (dragRef.current.dragging) {
            const span = dragRef.current.startView.end - dragRef.current.startView.start;
            const dx = e.clientX - dragRef.current.startX;
            const candlesPerPixel = span / layout.plotWidth;
            const shift = -dx * candlesPerPixel;

            let newStart = dragRef.current.startView.start + shift;
            let newEnd = dragRef.current.startView.end + shift;

            if (newStart < 0) {
               newEnd -= newStart;
               newStart = 0;
            }
            if (newEnd > candles?.length) {
               newStart -= newEnd - candles?.length;
               newEnd = candles?.length;
            }
            newStart = Math.max(0, newStart);

            setView({ start: newStart, end: newEnd });
         }
      },
      [candles?.length, layout.plotWidth],
   );

   const endDrag = useCallback(() => {
      dragRef.current.dragging = false;
   }, []);

   const onPointerLeave = useCallback(() => {
      setHover(null);
      endDrag();
   }, [endDrag]);

   // Double-click resets zoom to default (last 120 candles or all if fewer).
   const onDoubleClick = useCallback(() => {
      const n = candles?.length;
      const visible = Math.min(120, n);
      setView({ start: Math.max(0, n - visible), end: n });
   }, [candles?.length]);

   // -------------------------------------------------------------------------
   // Render
   // -------------------------------------------------------------------------
   return (
      <div
         ref={containerRef}
         className={className}
         style={{
            width: width ? width : "100%",
            height: height ? height : "100%",
            position: "relative",
            background: backgroundColor,
            borderRadius: 8,
            overflow: "hidden",
            userSelect: "none",
         }}
      >
         <canvas
            ref={canvasRef}
            style={{
               width: size.width,
               height: size.height,
               display: "block",
               cursor: dragRef.current.dragging ? "grabbing" : "grab",
               touchAction: "none",
            }}
            onWheel={onWheel}
            onPointerDown={onPointerDown}
            onPointerMove={onPointerMove}
            onPointerUp={endDrag}
            onPointerLeave={onPointerLeave}
            onDoubleClick={onDoubleClick}
         />
      </div>
   );
}

// ---------------------------------------------------------------------------
// Color utility: hex -> rgba with alpha, used for translucent volume bars.
// ---------------------------------------------------------------------------
function hexAlpha(hex: string, alpha: number): string {
   const h = hex.replace("#", "");
   const bigint = parseInt(
      h?.length === 3
         ? h
              .split("")
              .map((c) => c + c)
              .join("")
         : h,
      16,
   );
   const r = (bigint >> 16) & 255;
   const g = (bigint >> 8) & 255;
   const b = bigint & 255;
   return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}
