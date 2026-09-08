from app.schemas.common import SymbolId, Timeframe
from app.schemas.snapshot import MarketSnapshot
from app.services.instrument_catalog import InstrumentCatalog
from app.services.market_data import (
    Bar,
    MarketDataError,
    MarketDataPort,
    resample_to_hours,
    resample_to_minutes,
)
from app.services.snapshot import build_market_snapshot
from app.services.snapshot_store import SnapshotStore

_SWING_HISTORY: dict[Timeframe, tuple[str, str]] = {
    "M15": ("15m", "60d"),
    "H1": ("1h", "60d"),
    "D1": ("1d", "2y"),
}
_SCALP_HISTORY: dict[Timeframe, tuple[str, str]] = {
    "M1": ("1m", "7d"),
    "M5": ("5m", "60d"),
}


class SnapshotService:
    def __init__(
        self,
        catalog: InstrumentCatalog,
        market_data: MarketDataPort,
        store: SnapshotStore,
    ) -> None:
        self._catalog = catalog
        self._market_data = market_data
        self._store = store

    def get(self, symbol: SymbolId) -> MarketSnapshot | None:
        return self._store.read(symbol)

    def capture(self, symbol: SymbolId) -> MarketSnapshot:
        instrument = self._catalog.get(symbol)
        bars_by_timeframe: dict[Timeframe, list[Bar]] = {}
        last_price: float | None = None
        error: str | None = None

        try:
            last_price = self._market_data.quote(instrument.yahoo_symbol).last
            m15 = self._market_data.history(instrument.yahoo_symbol, *_SWING_HISTORY["M15"])
            h1 = self._market_data.history(instrument.yahoo_symbol, *_SWING_HISTORY["H1"])
            d1 = self._market_data.history(instrument.yahoo_symbol, *_SWING_HISTORY["D1"])
            bars_by_timeframe["M15"] = m15
            bars_by_timeframe["H1"] = h1
            bars_by_timeframe["H4"] = resample_to_hours(h1, 4)
            bars_by_timeframe["D1"] = d1
        except MarketDataError as exc:
            error = str(exc)

        self._attach_scalp_bars(instrument.yahoo_symbol, bars_by_timeframe)

        snapshot = build_market_snapshot(
            symbol=symbol,
            yahoo_symbol=instrument.yahoo_symbol,
            last_price=last_price,
            bars_by_timeframe=bars_by_timeframe,
            error=error,
        )
        self._store.write(snapshot)
        return snapshot

    def _attach_scalp_bars(
        self,
        yahoo_symbol: str,
        bars_by_timeframe: dict[Timeframe, list[Bar]],
    ) -> None:
        m1 = self._optional_history(yahoo_symbol, *_SCALP_HISTORY["M1"])
        if m1:
            bars_by_timeframe["M1"] = m1

        m5 = self._optional_history(yahoo_symbol, *_SCALP_HISTORY["M5"])
        if not m5 and m1:
            m5 = resample_to_minutes(m1, 5)
        if m5:
            bars_by_timeframe["M5"] = m5

    def _optional_history(self, yahoo_symbol: str, interval: str, period: str) -> list[Bar]:
        try:
            return self._market_data.history(yahoo_symbol, interval, period)
        except MarketDataError:
            return []
