import { useEffect, useId, useRef } from "react";

const SCRIPT_SRC = "https://s3.tradingview.com/tv.js";

function loadTradingView(): Promise<void> {
  if (window.TradingView) {
    return Promise.resolve();
  }

  const existing = document.querySelector<HTMLScriptElement>("script[data-tradingview]");
  if (existing) {
    return new Promise((resolve, reject) => {
      existing.addEventListener("load", () => resolve(), { once: true });
      existing.addEventListener("error", () => reject(new Error("TradingView script failed")), {
        once: true,
      });
    });
  }

  return new Promise((resolve, reject) => {
    const script = document.createElement("script");
    script.src = SCRIPT_SRC;
    script.async = true;
    script.dataset.tradingview = "true";
    script.addEventListener("load", () => resolve(), { once: true });
    script.addEventListener("error", () => reject(new Error("TradingView script failed")), {
      once: true,
    });
    document.body.appendChild(script);
  });
}

interface TradingViewChartProps {
  tvSymbol: string;
}

export function TradingViewChart({ tvSymbol }: TradingViewChartProps) {
  const containerId = useId().replace(/:/g, "");
  const hostRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    let widget: { remove?: () => void } | undefined;

    async function mount() {
      try {
        await loadTradingView();
      } catch {
        return;
      }
      if (cancelled || !hostRef.current || !window.TradingView) {
        return;
      }
      hostRef.current.id = containerId;
      hostRef.current.replaceChildren();
      widget = new window.TradingView.widget({
        autosize: true,
        symbol: tvSymbol,
        interval: "60",
        timezone: "Etc/UTC",
        theme: "dark",
        style: "1",
        locale: "en",
        hide_side_toolbar: false,
        allow_symbol_change: false,
        withdateranges: true,
        container_id: containerId,
      });
    }

    void mount();
    return () => {
      cancelled = true;
      widget?.remove?.();
    };
  }, [containerId, tvSymbol]);

  return (
    <section className="chart-panel" aria-label="Live chart">
      <div className="chart-host" ref={hostRef} />
    </section>
  );
}
