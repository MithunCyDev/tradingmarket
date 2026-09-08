interface TradingViewWidgetOptions {
  autosize: boolean;
  symbol: string;
  interval: string;
  timezone: string;
  theme: "dark" | "light";
  style: string;
  locale: string;
  hide_side_toolbar?: boolean;
  allow_symbol_change?: boolean;
  withdateranges?: boolean;
  container_id: string;
}

interface TradingViewWidget {
  remove?: () => void;
}

interface TradingViewNamespace {
  widget: new (options: TradingViewWidgetOptions) => TradingViewWidget;
}

interface Window {
  TradingView?: TradingViewNamespace;
}
