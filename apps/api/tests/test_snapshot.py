from datetime import UTC, datetime

from app.config import REPO_ROOT, Settings
from app.container import build_container
from app.services.market_data import Bar, MarketDataError, RawQuote
from app.services.snapshot import build_market_snapshot, build_timeframe_snapshot
from tests.conftest import make_trend_bars


def test_uptrend_bars_classify_as_long() -> None:
    bars = make_trend_bars(60, start=100.0, step=1.0)

    frame = build_timeframe_snapshot(bars, "H1")

    assert frame.bias == "long"
    assert frame.last_close == 160.0
    assert frame.ema20 is not None
    assert frame.ema50 is not None
    assert frame.atr is not None
    assert frame.bar_count == 60


def test_downtrend_bars_classify_as_short() -> None:
    bars = make_trend_bars(60, start=200.0, step=-1.0)

    frame = build_timeframe_snapshot(bars, "H1")

    assert frame.bias == "short"
    assert frame.last_close == 140.0


def test_flat_bars_classify_as_range() -> None:
    bars = make_trend_bars(60, start=100.0, step=0.0)

    frame = build_timeframe_snapshot(bars, "H1")

    assert frame.bias == "range"


def test_market_snapshot_includes_all_timeframes() -> None:
    bars = {
        "M15": make_trend_bars(60, start=100.0, step=0.2),
        "H1": make_trend_bars(60, start=100.0, step=0.5),
        "H4": make_trend_bars(60, start=100.0, step=1.0),
        "D1": make_trend_bars(60, start=100.0, step=2.0),
    }

    snapshot = build_market_snapshot(
        symbol="XAUUSD",
        yahoo_symbol="GC=F",
        last_price=160.0,
        bars_by_timeframe=bars,
    )

    assert snapshot.symbol == "XAUUSD"
    assert set(snapshot.timeframes.keys()) == {"M15", "H1", "H4", "D1"}
    assert snapshot.delayed is True
    assert snapshot.error is None


def test_market_snapshot_includes_scalp_timeframes_when_present() -> None:
    bars = {
        "M1": make_trend_bars(60, start=100.0, step=0.1),
        "M5": make_trend_bars(60, start=100.0, step=0.15),
        "M15": make_trend_bars(60, start=100.0, step=0.2),
        "H1": make_trend_bars(60, start=100.0, step=0.5),
        "H4": make_trend_bars(60, start=100.0, step=1.0),
        "D1": make_trend_bars(60, start=100.0, step=2.0),
    }

    snapshot = build_market_snapshot(
        symbol="XAUUSD",
        yahoo_symbol="GC=F",
        last_price=160.0,
        bars_by_timeframe=bars,
    )

    assert set(snapshot.timeframes.keys()) == {"M1", "M5", "M15", "H1", "H4", "D1"}


class _IntervalMarketData:
    def __init__(self, fail_intervals: set[str] | None = None) -> None:
        self._fail_intervals = fail_intervals or set()

    def history(self, yahoo_symbol: str, interval: str, period: str) -> list[Bar]:
        if interval in self._fail_intervals:
            raise MarketDataError(f"no bars for {interval}")
        return make_trend_bars(60, start=100.0, step=1.0)

    def quote(self, yahoo_symbol: str) -> RawQuote:
        return RawQuote(last=2651.4, previous_close=2640.0, as_of=datetime(2026, 9, 8, 18, 0, tzinfo=UTC))


def _snapshot_service(tmp_path, fail_intervals: set[str] | None = None):
    settings = Settings(data_dir=tmp_path, catalog_path=REPO_ROOT / "config" / "instruments.json")
    container = build_container(settings, _IntervalMarketData(fail_intervals))
    return container.snapshot_service


def test_capture_includes_m1_and_m5_when_vendor_has_bars(tmp_path) -> None:
    snapshot = _snapshot_service(tmp_path).capture("XAUUSD")

    assert snapshot.error is None
    assert "M1" in snapshot.timeframes
    assert "M5" in snapshot.timeframes
    assert "H1" in snapshot.timeframes


def test_m1_failure_does_not_fail_the_snapshot(tmp_path) -> None:
    snapshot = _snapshot_service(tmp_path, {"1m"}).capture("XAUUSD")

    assert snapshot.error is None
    assert "M1" not in snapshot.timeframes
    assert "M15" in snapshot.timeframes
    assert "H1" in snapshot.timeframes


def test_htf_failure_still_sets_snapshot_error(tmp_path) -> None:
    snapshot = _snapshot_service(tmp_path, {"1h"}).capture("XAUUSD")

    assert snapshot.error is not None
    assert "H1" not in snapshot.timeframes
