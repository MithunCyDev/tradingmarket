from datetime import UTC, datetime

import httpx

from app.schemas.instrument import Instrument
from app.services.market_data import MarketDataError, RawQuote

_YAHOO_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; EliteForex/1.0; +https://localhost)",
    "Accept": "application/json",
}


class HttpLiveQuotes:
    """Public Binance last for BTC; Yahoo 1-minute chart last for the rest."""

    def quote(self, instrument: Instrument) -> tuple[RawQuote, str]:
        if instrument.id == "BTCUSD":
            return self._binance_btc(), "binance"
        return self._yahoo_intraday(instrument.yahoo_symbol), "yahoo"

    def _binance_btc(self) -> RawQuote:
        try:
            response = httpx.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": "BTCUSDT"},
                timeout=5.0,
            )
            response.raise_for_status()
            payload = response.json()
            last = float(payload["lastPrice"])
            change = float(payload["priceChange"])
            return RawQuote(
                last=last,
                previous_close=last - change,
                as_of=datetime.now(UTC),
            )
        except Exception as exc:
            raise MarketDataError(f"Binance BTC quote failed: {exc}") from exc

    def _yahoo_intraday(self, yahoo_symbol: str) -> RawQuote:
        try:
            response = httpx.get(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{yahoo_symbol}",
                params={"interval": "1m", "range": "1d"},
                headers=_YAHOO_HEADERS,
                timeout=5.0,
            )
            response.raise_for_status()
            result = response.json()["chart"]["result"][0]
            meta = result["meta"]
            last = float(meta["regularMarketPrice"])
            previous = float(meta.get("chartPreviousClose") or meta.get("previousClose") or last)
            as_of = datetime.fromtimestamp(int(meta["regularMarketTime"]), tz=UTC)
            return RawQuote(last=last, previous_close=previous, as_of=as_of)
        except Exception as exc:
            raise MarketDataError(f"Yahoo live quote failed for {yahoo_symbol}: {exc}") from exc
