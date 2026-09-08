from datetime import UTC, datetime

from app.schemas.common import TIMEFRAMES, SymbolId, Timeframe
from app.schemas.snapshot import MarketSnapshot, TimeframeSnapshot
from app.services.indicators import atr, classify_trend, ema, swing_points
from app.services.market_data import Bar


def _recent_swings(values: list[float], limit: int = 4) -> list[float]:
    unique: list[float] = []
    for value in reversed(values):
        if value in unique:
            continue
        unique.append(value)
        if len(unique) >= limit:
            break
    unique.reverse()
    return unique


def build_timeframe_snapshot(bars: list[Bar], timeframe: Timeframe) -> TimeframeSnapshot:
    if not bars:
        raise ValueError(f"No bars available for {timeframe}")

    highs = [bar.high for bar in bars]
    lows = [bar.low for bar in bars]
    closes = [bar.close for bar in bars]
    last_close = closes[-1]
    ema20 = ema(closes, 20)
    ema50 = ema(closes, 50)
    if ema20 is None or ema50 is None:
        bias = "range"
    else:
        bias = classify_trend(last_close, ema20, ema50)

    swing_highs, swing_lows = swing_points(highs, lows, lookback=5)

    return TimeframeSnapshot(
        timeframe=timeframe,
        last_close=last_close,
        atr=atr(highs, lows, closes, period=14),
        ema20=ema20,
        ema50=ema50,
        bias=bias,
        swing_highs=_recent_swings(swing_highs),
        swing_lows=_recent_swings(swing_lows),
        bar_count=len(bars),
    )


def build_market_snapshot(
    symbol: SymbolId,
    yahoo_symbol: str,
    last_price: float | None,
    bars_by_timeframe: dict[Timeframe, list[Bar]],
    error: str | None = None,
    captured_at: datetime | None = None,
) -> MarketSnapshot:
    timeframes: dict[Timeframe, TimeframeSnapshot] = {}
    for timeframe in TIMEFRAMES:
        bars = bars_by_timeframe.get(timeframe, [])
        if not bars:
            continue
        timeframes[timeframe] = build_timeframe_snapshot(bars, timeframe)

    return MarketSnapshot(
        symbol=symbol,
        yahoo_symbol=yahoo_symbol,
        captured_at=captured_at or datetime.now(UTC),
        last_price=last_price,
        timeframes=timeframes,
        source="yahoo",
        delayed=True,
        error=error,
    )
