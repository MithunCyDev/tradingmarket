from datetime import UTC, datetime, timedelta

from app.services.market_data import Bar, resample_to_hours, resample_to_minutes


def test_resample_four_hourly_bars_into_one() -> None:
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = [
        Bar(start + timedelta(hours=offset), 10 + offset, 11 + offset, 9 + offset, 10.5 + offset, 100)
        for offset in range(4)
    ]

    resampled = resample_to_hours(bars, 4)

    assert len(resampled) == 1
    assert resampled[0].open == 10
    assert resampled[0].close == 13.5
    assert resampled[0].high == 14
    assert resampled[0].low == 9
    assert resampled[0].volume == 400


def test_resample_five_minute_bars_into_one() -> None:
    start = datetime(2026, 1, 1, 0, 0, tzinfo=UTC)
    bars = [
        Bar(start + timedelta(minutes=offset), 10 + offset, 11 + offset, 9 + offset, 10.5 + offset, 100)
        for offset in range(5)
    ]

    resampled = resample_to_minutes(bars, 5)

    assert len(resampled) == 1
    assert resampled[0].open == 10
    assert resampled[0].close == 14.5
    assert resampled[0].high == 15
    assert resampled[0].low == 9
    assert resampled[0].volume == 500
