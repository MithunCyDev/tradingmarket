from app.schemas.common import Bias


def true_ranges(highs: list[float], lows: list[float], closes: list[float]) -> list[float]:
    if not (len(highs) == len(lows) == len(closes)):
        raise ValueError("highs, lows, and closes must be the same length")

    ranges: list[float] = []
    for index, (high, low, close) in enumerate(zip(highs, lows, closes, strict=True)):
        high_low = high - low
        if index == 0:
            ranges.append(high_low)
            continue
        prior_close = closes[index - 1]
        ranges.append(max(high_low, abs(high - prior_close), abs(low - prior_close)))
    return ranges


def atr(
    highs: list[float],
    lows: list[float],
    closes: list[float],
    period: int = 14,
) -> float | None:
    if period < 1:
        raise ValueError("period must be >= 1")
    ranges = true_ranges(highs, lows, closes)
    if len(ranges) < period:
        return None
    window = ranges[-period:]
    return sum(window) / period


def ema_series(values: list[float], period: int) -> list[float | None]:
    if period < 1:
        raise ValueError("period must be >= 1")
    series: list[float | None] = [None] * len(values)
    if len(values) < period:
        return series
    current = sum(values[:period]) / period
    series[period - 1] = current
    multiplier = 2 / (period + 1)
    for index in range(period, len(values)):
        current = current + multiplier * (values[index] - current)
        series[index] = current
    return series


def ema(values: list[float], period: int) -> float | None:
    if period < 1:
        raise ValueError("period must be >= 1")
    if len(values) < period:
        return None

    seed = sum(values[:period]) / period
    multiplier = 2 / (period + 1)
    current = seed
    for value in values[period:]:
        current = current + multiplier * (value - current)
    return current


def classify_trend(close: float, ema_fast: float, ema_slow: float) -> Bias:
    if close > ema_fast > ema_slow:
        return "long"
    if close < ema_fast < ema_slow:
        return "short"
    return "range"


def swing_points(
    highs: list[float],
    lows: list[float],
    lookback: int = 5,
) -> tuple[list[float], list[float]]:
    if lookback < 1:
        raise ValueError("lookback must be >= 1")
    if len(highs) != len(lows):
        raise ValueError("highs and lows must be the same length")

    swing_highs: list[float] = []
    swing_lows: list[float] = []
    last_index = len(highs) - 1

    for index in range(lookback, last_index - lookback + 1):
        high_window = highs[index - lookback : index + lookback + 1]
        low_window = lows[index - lookback : index + lookback + 1]
        if highs[index] == max(high_window):
            swing_highs.append(highs[index])
        if lows[index] == min(low_window):
            swing_lows.append(lows[index])

    return swing_highs, swing_lows
