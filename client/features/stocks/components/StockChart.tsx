"use client";

import {
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";

import {
  createChart,
  ColorType,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  LineStyle,
  type IChartApi,
  type UTCTimestamp,
} from "lightweight-charts";

type StockCandle = {
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
};

type StockChartProps = {
  data: StockCandle[];
  symbol?: string;
  exchange?: string;
  height?: number;
  className?: string;
};

type ChartTheme = {
  background: string;
  textColor: string;
  gridColor: string;
  borderColor: string;
  crosshairColor: string;
};

const themes: Record<"light" | "dark", ChartTheme> = {
  light: {
    background: "#ffffff",
    textColor: "#64748b",
    gridColor: "#f1f5f9",
    borderColor: "#e2e8f0",
    crosshairColor: "#94a3b8",
  },
  dark: {
    background: "#111827",
    textColor: "#94a3b8",
    gridColor: "#1f2937",
    borderColor: "#374151",
    crosshairColor: "#6b7280",
  },
};

export default function StockChart({
  data,
  symbol = "TPL",
  exchange = "PSX",
  height = 600,
  className = "",
}: StockChartProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const [isDark, setIsDark] = useState(true);
  const [showVolume, setShowVolume] = useState(true);
  const [chartType, setChartType] = useState<"candles" | "line">(
    "candles"
  );

  const theme = isDark ? themes.dark : themes.light;

  const sortedData = useMemo(() => {
    return [...data]
      .filter(
        (item) =>
          item.date &&
          Number.isFinite(item.open) &&
          Number.isFinite(item.high) &&
          Number.isFinite(item.low) &&
          Number.isFinite(item.close) &&
          Number.isFinite(item.volume)
      )
      .sort(
        (a, b) =>
          new Date(a.date).getTime() -
          new Date(b.date).getTime()
      );
  }, [data]);

  const summary = useMemo(() => {
    if (!sortedData.length) return null;

    const first = sortedData[0];
    const latest = sortedData[sortedData.length - 1];

    const change = latest.close - first.close;

    const changePercent =
      first.close !== 0
        ? (change / first.close) * 100
        : 0;

    return {
      open: latest.open,
      high: latest.high,
      low: latest.low,
      close: latest.close,
      change,
      changePercent,
      volume: latest.volume,
    };
  }, [sortedData]);

  useEffect(() => {
    if (!containerRef.current || !sortedData.length) return;

    const container = containerRef.current;

    const chart = createChart(container, {
      width: container.clientWidth,
      height,

      layout: {
        background: {
          type: ColorType.Solid,
          color: theme.background,
        },
        textColor: theme.textColor,
        attributionLogo: false,
      },

      grid: {
        vertLines: {
          color: theme.gridColor,
        },
        horzLines: {
          color: theme.gridColor,
        },
      },

      crosshair: {
        mode: 1,

        vertLine: {
          color: theme.crosshairColor,
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: isDark
            ? "#374151"
            : "#334155",
        },

        horzLine: {
          color: theme.crosshairColor,
          width: 1,
          style: LineStyle.Dashed,
          labelBackgroundColor: isDark
            ? "#374151"
            : "#334155",
        },
      },

      rightPriceScale: {
        borderColor: theme.borderColor,
        scaleMargins: {
          top: 0.1,
          bottom: showVolume ? 0.3 : 0.1,
        },
      },

      timeScale: {
        borderColor: theme.borderColor,
        timeVisible: false,
        rightOffset: 5,
        barSpacing: 8,
      },

      localization: {
        priceFormatter: (price: number) =>
          price.toLocaleString("en-US", {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2,
          }),
      },
    });

    chartRef.current = chart;

    const candleData = sortedData.map((item) => ({
      time: toTimestamp(item.date),
      open: item.open,
      high: item.high,
      low: item.low,
      close: item.close,
    }));

    const lineData = sortedData.map((item) => ({
      time: toTimestamp(item.date),
      value: item.close,
    }));

    // Add price series
    if (chartType === "candles") {
      const series = chart.addSeries(CandlestickSeries, {
        upColor: "#22c55e",
        downColor: "#ef4444",
        borderUpColor: "#22c55e",
        borderDownColor: "#ef4444",
        wickUpColor: "#22c55e",
        wickDownColor: "#ef4444",
        priceLineVisible: true,
        lastValueVisible: true,
      });

      series.setData(candleData);

      if (summary) {
        series.createPriceLine({
          price: summary.close,
          color:
            summary.change >= 0
              ? "#22c55e"
              : "#ef4444",
          lineWidth: 1,
          lineStyle: LineStyle.Dashed,
          axisLabelVisible: true,
          title: "Last",
        });
      }
    } else {
      const series = chart.addSeries(LineSeries, {
        color: "#3b82f6",
        lineWidth: 2,
        priceLineVisible: true,
        lastValueVisible: true,
      });

      series.setData(lineData);
    }

    // Add volume
    if (showVolume) {
      const volumeSeries = chart.addSeries(HistogramSeries, {
        priceFormat: {
          type: "volume",
        },
        priceScaleId: "",
        lastValueVisible: false,
        priceLineVisible: false,
      });

      volumeSeries.priceScale().applyOptions({
        scaleMargins: {
          top: 0.8,
          bottom: 0,
        },
      });

      volumeSeries.setData(
        sortedData.map((item) => ({
          time: toTimestamp(item.date),
          value: item.volume,
          color:
            item.close >= item.open
              ? "rgba(34, 197, 94, 0.45)"
              : "rgba(239, 68, 68, 0.45)",
        }))
      );
    }

    chart.timeScale().fitContent();

    const resizeObserver = new ResizeObserver(() => {
      chart.applyOptions({
        width: container.clientWidth,
      });
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [
    sortedData,
    theme,
    height,
    showVolume,
    chartType,
    isDark,
    summary,
  ]);

  if (!sortedData.length) {
    return (
      <div
        className={`flex h-96 items-center justify-center rounded-xl border border-border text-muted-foreground ${className}`}
      >
        No market data available.
      </div>
    );
  }

  return (
    <div
      className={`overflow-hidden rounded-xl border border-border bg-background ${className}`}
    >
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-border p-4">
        <div>
          <div className="flex items-center gap-2">
            <h2 className="text-xl font-semibold">
              {symbol}
            </h2>

            <span className="rounded bg-muted px-2 py-1 text-xs text-muted-foreground">
              {exchange}
            </span>
          </div>

          {summary && (
            <div className="mt-1 flex items-baseline gap-3">
              <span className="text-2xl font-bold">
                {summary.close.toFixed(2)}
              </span>

              <span
                className={
                  summary.change >= 0
                    ? "text-sm text-green-500"
                    : "text-sm text-red-500"
                }
              >
                {summary.change >= 0 ? "+" : ""}
                {summary.change.toFixed(2)} (
                {summary.changePercent.toFixed(2)}%)
              </span>
            </div>
          )}
        </div>

        {/* Controls */}
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() =>
              setChartType((current) =>
                current === "candles" ? "line" : "candles"
              )
            }
            className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
          >
            {chartType === "candles" ? "Line" : "Candles"}
          </button>

          <button
            onClick={() => setShowVolume((current) => !current)}
            className={`rounded-md border border-border px-3 py-2 text-sm hover:bg-muted ${
              showVolume ? "bg-muted" : ""
            }`}
          >
            Volume
          </button>

          <button
            onClick={() => setIsDark((current) => !current)}
            className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
            aria-label="Toggle chart theme"
          >
            {isDark ? "Light" : "Dark"}
          </button>

          <button
            onClick={() => chartRef.current?.timeScale().fitContent()}
            className="rounded-md border border-border px-3 py-2 text-sm hover:bg-muted"
          >
            Fit
          </button>
        </div>
      </div>

      {/* OHLC Summary */}
      {summary && (
        <div className="flex flex-wrap gap-x-6 gap-y-2 border-b border-border px-4 py-3 text-sm">
          <span>
            O: <strong>{summary.open.toFixed(2)}</strong>
          </span>

          <span className="text-green-500">
            H: <strong>{summary.high.toFixed(2)}</strong>
          </span>

          <span className="text-red-500">
            L: <strong>{summary.low.toFixed(2)}</strong>
          </span>

          <span>
            C: <strong>{summary.close.toFixed(2)}</strong>
          </span>

          <span className="text-muted-foreground">
            Vol: {formatVolume(summary.volume)}
          </span>
        </div>
      )}

      {/* Chart */}
      <div
        ref={containerRef}
        style={{
          width: "100%",
          height,
        }}
      />

      {/* Footer */}
      <div className="border-t border-border px-4 py-2 text-xs text-muted-foreground">
        {sortedData.length} trading sessions
      </div>
    </div>
  );
}

function toTimestamp(date: string): UTCTimestamp {
  const timestamp = Math.floor(
    new Date(`${date}T00:00:00Z`).getTime() / 1000
  );

  return timestamp as UTCTimestamp;
}

function formatVolume(volume: number) {
  if (volume >= 1_000_000) {
    return `${(volume / 1_000_000).toFixed(2)}M`;
  }

  if (volume >= 1_000) {
    return `${(volume / 1_000).toFixed(2)}K`;
  }

  return volume.toLocaleString();
}