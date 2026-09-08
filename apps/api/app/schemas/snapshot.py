from datetime import datetime

from app.schemas.common import ApiModel, Bias, SymbolId, Timeframe


class TimeframeSnapshot(ApiModel):
    timeframe: Timeframe
    last_close: float
    atr: float | None
    ema20: float | None
    ema50: float | None
    bias: Bias
    swing_highs: list[float]
    swing_lows: list[float]
    bar_count: int


class MarketSnapshot(ApiModel):
    symbol: SymbolId
    yahoo_symbol: str
    captured_at: datetime
    last_price: float | None
    timeframes: dict[Timeframe, TimeframeSnapshot]
    source: str = "yahoo"
    delayed: bool = True
    error: str | None = None
