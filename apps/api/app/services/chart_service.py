from datetime import UTC, datetime, timedelta

from app.schemas.analysis import ChartBar, ChartResponse
from app.schemas.common import TIMEFRAMES, SymbolId, Timeframe
from app.services.indicators import ema_series, swing_points
from app.services.instrument_catalog import InstrumentCatalog
from app.services.market_data import (
    Bar,
    MarketDataError,
    MarketDataPort,
    resample_to_hours,
    resample_to_minutes,
)

_HISTORY: dict[Timeframe, tuple[str, str]] = {
    "M1": ("1m", "7d"),
    "M5": ("5m", "60d"),
    "M15": ("15m", "60d"),
    "H1": ("1h", "60d"),
    "D1": ("1d", "2y"),
}


class ChartService:
    def __init__(self, catalog: InstrumentCatalog, market_data: MarketDataPort) -> None:
        self._catalog = catalog
        self._market_data = market_data
        self._cached: dict[tuple[SymbolId, Timeframe], tuple[datetime, ChartResponse]] = {}

    def get(self, symbol: SymbolId, timeframe: Timeframe) -> ChartResponse:
        now = datetime.now(UTC)
        cached = self._cached.get((symbol, timeframe))
        if cached is not None and now - cached[0] < timedelta(seconds=90):
            return cached[1]

        instrument = self._catalog.get(symbol)
        bars = self._load_bars(instrument.yahoo_symbol, timeframe)
        closes = [bar.close for bar in bars]
        highs = [bar.high for bar in bars]
        lows = [bar.low for bar in bars]
        swing_highs, swing_lows = swing_points(highs, lows, lookback=5) if bars else ([], [])
        chart = ChartResponse(
            symbol=symbol,
            timeframe=timeframe,
            bars=[
                ChartBar(
                    time=int(bar.timestamp.timestamp()),
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                )
                for bar in bars[-180:]
            ],
            ema20=ema_series(closes, 20)[-180:],
            ema50=ema_series(closes, 50)[-180:],
            swing_highs=swing_highs[-4:],
            swing_lows=swing_lows[-4:],
        )
        self._cached[(symbol, timeframe)] = (now, chart)
        return chart

    def _load_bars(self, yahoo_symbol: str, timeframe: Timeframe) -> list[Bar]:
        if timeframe not in TIMEFRAMES:
            raise MarketDataError(f"Unsupported timeframe {timeframe}")
        if timeframe == "H4":
            hourly = self._market_data.history(yahoo_symbol, *_HISTORY["H1"])
            return resample_to_hours(hourly, 4)
        if timeframe == "M5":
            return self._load_m5(yahoo_symbol)
        interval, period = _HISTORY[timeframe]
        return self._market_data.history(yahoo_symbol, interval, period)

    def _load_m5(self, yahoo_symbol: str) -> list[Bar]:
        try:
            return self._market_data.history(yahoo_symbol, *_HISTORY["M5"])
        except MarketDataError:
            m1 = self._market_data.history(yahoo_symbol, *_HISTORY["M1"])
            resampled = resample_to_minutes(m1, 5)
            if not resampled:
                raise MarketDataError(f"Yahoo returned no M5 bars for {yahoo_symbol}")
            return resampled
