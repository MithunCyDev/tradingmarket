export type SymbolId = "XAUUSD" | "BTCUSD" | "XAGUSD" | "USOIL" | "EURUSD";
export type Bias = "long" | "short" | "range";
export type Action = "long" | "short" | "no_trade";
export type Confidence = "low" | "medium" | "high";
export type Timeframe = "M1" | "M5" | "M15" | "H1" | "H4" | "D1";
export type SignalStyle = "swing" | "scalp";
export type MarketKind = "crypto" | "forex" | "cme_metals" | "cme_energy";
export type MarketState = "open" | "closed";
export type StatusLabel = "LIVE" | "DELAYED" | "CLOSED";

export interface Instrument {
  id: SymbolId;
  label: string;
  tvSymbol: string;
  yahooSymbol: string;
  priceDecimals: number;
  marketKind: MarketKind;
}

export interface Quote {
  symbol: SymbolId;
  last: number | null;
  change: number | null;
  changePercent: number | null;
  asOf: string;
  delayed: boolean;
  marketState: MarketState;
  statusLabel: StatusLabel;
  source: string;
}

export interface SignalTicket {
  symbol: SymbolId;
  style?: SignalStyle;
  analyzedAt: string;
  action: Action;
  confidence: Confidence;
  timeframe: Timeframe;
  timeframeBias: Partial<Record<Timeframe, Bias>>;
  entryZone: { low: number; high: number } | null;
  stop: number | null;
  targets: { tp1: number; tp2: number } | null;
  invalidation: number | null;
  narrative: string;
  riskNotes: string;
}

export const SWING_BIAS_FRAMES: Timeframe[] = ["M15", "H1", "H4", "D1"];
export const SCALP_BIAS_FRAMES: Timeframe[] = ["M1", "M5", "M15", "H1"];

export interface ConfluenceFactor {
  id: string;
  passed: boolean;
  title: string;
  detail: string;
}

export interface ConfluenceReport {
  headline: string;
  action: Action;
  confidence: Confidence;
  suggestedConfidence: Confidence | null;
  passedCount: number;
  factorCount: number;
  summary: string;
  factors: ConfluenceFactor[];
}

export interface AnalysisLevel {
  id: string;
  label: string;
  price: number;
  kind: "entry" | "stop" | "target" | "invalidation";
}

export interface AnalysisResponse {
  symbol: SymbolId;
  analyzedAt: string;
  confluence: ConfluenceReport;
  levels: AnalysisLevel[];
}

export interface ChartBar {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface ChartResponse {
  symbol: string;
  timeframe: Timeframe;
  bars: ChartBar[];
  ema20: Array<number | null>;
  ema50: Array<number | null>;
  swingHighs: number[];
  swingLows: number[];
}

export interface InstrumentListResponse {
  data: Instrument[];
}

export interface QuoteListResponse {
  data: Quote[];
}

export const FALLBACK_INSTRUMENTS: Instrument[] = [
  {
    id: "XAUUSD",
    label: "GOLD",
    tvSymbol: "OANDA:XAUUSD",
    yahooSymbol: "GC=F",
    priceDecimals: 2,
    marketKind: "cme_metals",
  },
  {
    id: "BTCUSD",
    label: "BTC",
    tvSymbol: "BINANCE:BTCUSDT",
    yahooSymbol: "BTC-USD",
    priceDecimals: 1,
    marketKind: "crypto",
  },
  {
    id: "XAGUSD",
    label: "SILVER",
    tvSymbol: "OANDA:XAGUSD",
    yahooSymbol: "SI=F",
    priceDecimals: 3,
    marketKind: "cme_metals",
  },
  {
    id: "USOIL",
    label: "US OIL",
    tvSymbol: "TVC:USOIL",
    yahooSymbol: "CL=F",
    priceDecimals: 2,
    marketKind: "cme_energy",
  },
  {
    id: "EURUSD",
    label: "EUR/USD",
    tvSymbol: "FX:EURUSD",
    yahooSymbol: "EURUSD=X",
    priceDecimals: 5,
    marketKind: "forex",
  },
];
