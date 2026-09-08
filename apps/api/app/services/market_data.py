from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Protocol

import pandas as pd
import yfinance as yf


class MarketDataError(Exception):
    """Raised when a market data vendor cannot return usable prices."""


@dataclass(frozen=True)
class Bar:
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class RawQuote:
    last: float
    previous_close: float
    as_of: datetime


class MarketDataPort(Protocol):
    def history(self, yahoo_symbol: str, interval: str, period: str) -> list[Bar]:
        """Return OHLC bars for a Yahoo symbol."""

    def quote(self, yahoo_symbol: str) -> RawQuote:
        """Return the latest last/previous-close quote."""


def bars_from_frame(frame: pd.DataFrame) -> list[Bar]:
    if frame is None or frame.empty:
        return []

    working = frame.copy()
    if getattr(working.columns, "nlevels", 1) > 1:
        working.columns = [str(column[0]).lower() for column in working.columns]
    else:
        working.columns = [str(column).lower() for column in working.columns]

    bars: list[Bar] = []
    for index, row in working.iterrows():
        timestamp = index.to_pydatetime() if hasattr(index, "to_pydatetime") else index
        if not isinstance(timestamp, datetime):
            continue
        if timestamp.tzinfo is None:
            timestamp = timestamp.replace(tzinfo=UTC)
        bars.append(
            Bar(
                timestamp=timestamp,
                open=float(row["open"]),
                high=float(row["high"]),
                low=float(row["low"]),
                close=float(row["close"]),
                volume=float(row["volume"]) if "volume" in working.columns else 0.0,
            )
        )
    return bars


def resample_to_hours(bars: list[Bar], hours: int) -> list[Bar]:
    if hours < 1:
        raise ValueError("hours must be >= 1")
    if not bars:
        return []

    grouped: dict[datetime, list[Bar]] = {}
    for bar in bars:
        timestamp = bar.timestamp.astimezone(UTC)
        floored = timestamp.replace(minute=0, second=0, microsecond=0)
        bucket = floored.replace(hour=(floored.hour // hours) * hours)
        grouped.setdefault(bucket, []).append(bar)

    resampled: list[Bar] = []
    for bucket in sorted(grouped):
        chunk = grouped[bucket]
        resampled.append(
            Bar(
                timestamp=bucket,
                open=chunk[0].open,
                high=max(item.high for item in chunk),
                low=min(item.low for item in chunk),
                close=chunk[-1].close,
                volume=sum(item.volume for item in chunk),
            )
        )
    return resampled


def resample_to_minutes(bars: list[Bar], minutes: int) -> list[Bar]:
    if minutes < 1:
        raise ValueError("minutes must be >= 1")
    if not bars:
        return []

    grouped: dict[datetime, list[Bar]] = {}
    for bar in bars:
        timestamp = bar.timestamp.astimezone(UTC)
        total_minutes = timestamp.hour * 60 + timestamp.minute
        floored = (total_minutes // minutes) * minutes
        bucket = timestamp.replace(
            hour=floored // 60,
            minute=floored % 60,
            second=0,
            microsecond=0,
        )
        grouped.setdefault(bucket, []).append(bar)

    resampled: list[Bar] = []
    for bucket in sorted(grouped):
        chunk = grouped[bucket]
        resampled.append(
            Bar(
                timestamp=bucket,
                open=chunk[0].open,
                high=max(item.high for item in chunk),
                low=min(item.low for item in chunk),
                close=chunk[-1].close,
                volume=sum(item.volume for item in chunk),
            )
        )
    return resampled


class YahooMarketData:
    def history(self, yahoo_symbol: str, interval: str, period: str) -> list[Bar]:
        try:
            frame = yf.Ticker(yahoo_symbol).history(
                period=period,
                interval=interval,
                auto_adjust=True,
            )
        except Exception as exc:
            raise MarketDataError(f"Yahoo history failed for {yahoo_symbol}: {exc}") from exc

        bars = bars_from_frame(frame)
        if not bars:
            raise MarketDataError(f"Yahoo returned no bars for {yahoo_symbol} ({interval}/{period})")
        return bars

    def quote(self, yahoo_symbol: str) -> RawQuote:
        ticker = yf.Ticker(yahoo_symbol)
        try:
            info = ticker.fast_info
            last = float(info["last_price"])
            previous = float(info["previous_close"])
            return RawQuote(last=last, previous_close=previous, as_of=datetime.now(UTC))
        except Exception:
            daily = self.history(yahoo_symbol, interval="1d", period="5d")
            if len(daily) < 2:
                raise MarketDataError(f"Yahoo returned no quote for {yahoo_symbol}")
            last_bar = daily[-1]
            previous = daily[-2].close
            return RawQuote(last=last_bar.close, previous_close=previous, as_of=last_bar.timestamp)
