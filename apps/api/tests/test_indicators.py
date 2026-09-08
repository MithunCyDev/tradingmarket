from app.services.indicators import atr, classify_trend, ema, swing_points, true_ranges


def test_true_ranges_use_prior_close_gap() -> None:
    highs = [10.0, 12.0, 11.0]
    lows = [8.0, 9.0, 9.5]
    closes = [9.0, 10.0, 10.5]

    ranges = true_ranges(highs, lows, closes)

    assert ranges == [2.0, 3.0, 1.5]


def test_atr_is_mean_of_last_period_true_ranges() -> None:
    highs = [10.0, 11.0, 12.0, 13.0]
    lows = [9.0, 10.0, 11.0, 12.0]
    closes = [9.5, 10.5, 11.5, 12.5]

    value = atr(highs, lows, closes, period=3)

    assert value == 1.5


def test_atr_returns_none_until_enough_bars() -> None:
    assert atr([10.0, 11.0], [9.0, 10.0], [9.5, 10.5], period=3) is None


def test_ema_weights_recent_closes() -> None:
    values = [1.0, 2.0, 3.0, 4.0, 5.0]

    value = ema(values, period=3)

    assert value is not None
    assert round(value, 4) == 4.0


def test_ema_returns_none_until_enough_values() -> None:
    assert ema([1.0, 2.0], period=3) is None


def test_classify_trend_long_when_price_above_stacked_emas() -> None:
    assert classify_trend(close=110.0, ema_fast=105.0, ema_slow=100.0) == "long"


def test_classify_trend_short_when_price_below_stacked_emas() -> None:
    assert classify_trend(close=90.0, ema_fast=95.0, ema_slow=100.0) == "short"


def test_classify_trend_range_when_emas_are_mixed() -> None:
    assert classify_trend(close=102.0, ema_fast=100.0, ema_slow=101.0) == "range"


def test_swing_points_find_local_highs_and_lows() -> None:
    highs = [1.0, 2.0, 5.0, 2.0, 1.0, 3.0, 2.0]
    lows = [0.5, 1.0, 2.0, 1.0, 0.4, 1.5, 1.0]

    swing_highs, swing_lows = swing_points(highs, lows, lookback=2)

    assert 5.0 in swing_highs
    assert 0.4 in swing_lows
