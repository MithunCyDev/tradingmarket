from datetime import UTC, datetime, timedelta

from app.services.market_data import Bar


def make_trend_bars(
    count: int,
    start: float,
    step: float,
    start_at: datetime | None = None,
) -> list[Bar]:
    origin = start_at or datetime(2026, 1, 1, tzinfo=UTC)
    bars: list[Bar] = []
    price = start
    for index in range(count):
        close = price + step
        high = max(price, close) + 0.2
        low = min(price, close) - 0.2
        bars.append(
            Bar(
                timestamp=origin + timedelta(hours=index),
                open=price,
                high=high,
                low=low,
                close=close,
                volume=1000.0,
            )
        )
        price = close
    return bars
