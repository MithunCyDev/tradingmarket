import {
  CandlestickSeries,
  ColorType,
  LineSeries,
  LineStyle,
  createChart,
  createSeriesMarkers,
  type IChartApi,
  type ISeriesApi,
  type UTCTimestamp,
} from "lightweight-charts";
import { useEffect, useRef } from "react";

import { useChart } from "../hooks/useChart";
import { levelColor } from "../lib/levels";
import type { AnalysisLevel, SymbolId, Timeframe } from "../types";
import { ChartLegend } from "./ChartLegend";

interface AnalysisChartProps {
  symbol: SymbolId;
  timeframe: Timeframe;
  levels: AnalysisLevel[];
  decimals: number;
}

export function AnalysisChart({
  symbol,
  timeframe,
  levels,
  decimals,
}: AnalysisChartProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const { data, error, isLoading } = useChart(symbol, timeframe);

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !data || data.bars.length === 0) {
      return;
    }

    const chart: IChartApi = createChart(host, {
      autoSize: true,
      layout: {
        background: { type: ColorType.Solid, color: "#12161c" },
        textColor: "#7d8491",
        fontFamily: "IBM Plex Sans, Segoe UI, sans-serif",
      },
      grid: {
        vertLines: { color: "#1c222b" },
        horzLines: { color: "#1c222b" },
      },
      rightPriceScale: { borderColor: "#222831" },
      timeScale: { borderColor: "#222831", timeVisible: true },
      crosshair: { mode: 0 },
    });

    const candles: ISeriesApi<"Candlestick"> = chart.addSeries(
      CandlestickSeries,
      {
        upColor: "#26a69a",
        downColor: "#ef5350",
        borderVisible: false,
        wickUpColor: "#26a69a",
        wickDownColor: "#ef5350",
      },
    );
    candles.setData(
      data.bars.map((bar) => ({
        time: bar.time as UTCTimestamp,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      })),
    );

    const ema20 = chart.addSeries(LineSeries, {
      color: "#d4a017",
      lineWidth: 2,
      priceLineVisible: false,
    });
    const ema50 = chart.addSeries(LineSeries, {
      color: "#5b8def",
      lineWidth: 2,
      priceLineVisible: false,
    });
    ema20.setData(_linePoints(data.bars, data.ema20));
    ema50.setData(_linePoints(data.bars, data.ema50));

    for (const level of levels) {
      candles.createPriceLine({
        price: level.price,
        color: levelColor(level.kind),
        lineWidth: 2,
        lineStyle: level.kind === "entry" ? LineStyle.Solid : LineStyle.Dashed,
        axisLabelVisible: true,
        title: level.label,
      });
    }

    createSeriesMarkers(
      candles,
      _swingMarkers(data.bars, data.swingHighs, data.swingLows),
    );
    chart.timeScale().fitContent();

    return () => {
      chart.remove();
    };
  }, [data, levels]);

  return (
    <section className="analysis-chart" aria-label="Marked analysis chart">
      <div className="pane-header">
        <h2>Marked chart</h2>
        <span className="pane-sub">{timeframe} markup</span>
      </div>
      {error ? (
        <p className="state error">Could not load OHLC for markup.</p>
      ) : null}
      {isLoading && !data ? <p className="state">Loading structure…</p> : null}
      <div className="analysis-host" ref={hostRef} />
      <ChartLegend levels={levels} decimals={decimals} />
    </section>
  );
}

function _linePoints(
  bars: Array<{ time: number }>,
  values: Array<number | null>,
): Array<{ time: UTCTimestamp; value: number }> {
  const points: Array<{ time: UTCTimestamp; value: number }> = [];
  for (let index = 0; index < bars.length; index += 1) {
    const value = values[index];
    if (value == null) {
      continue;
    }
    points.push({ time: bars[index].time as UTCTimestamp, value });
  }
  return points;
}

function _swingMarkers(
  bars: Array<{ time: number; high: number; low: number }>,
  highs: number[],
  lows: number[],
) {
  const markers: Array<{
    time: UTCTimestamp;
    position: "aboveBar" | "belowBar";
    color: string;
    shape: "arrowDown" | "arrowUp";
    text: string;
  }> = [];
  for (const price of highs) {
    const bar = [...bars]
      .reverse()
      .find((item) => Math.abs(item.high - price) < 1e-6 * Math.max(1, price));
    if (bar) {
      markers.push({
        time: bar.time as UTCTimestamp,
        position: "aboveBar",
        color: "#ef5350",
        shape: "arrowDown",
        text: "SH",
      });
    }
  }
  for (const price of lows) {
    const bar = [...bars]
      .reverse()
      .find((item) => Math.abs(item.low - price) < 1e-6 * Math.max(1, price));
    if (bar) {
      markers.push({
        time: bar.time as UTCTimestamp,
        position: "belowBar",
        color: "#26a69a",
        shape: "arrowUp",
        text: "SL",
      });
    }
  }
  const unique = new Map<number, (typeof markers)[number]>();
  for (const marker of markers) {
    unique.set(Number(marker.time), marker);
  }
  return [...unique.values()].sort(
    (left, right) => Number(left.time) - Number(right.time),
  );
}
