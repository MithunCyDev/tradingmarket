from datetime import UTC, datetime

from app.schemas.signal import SignalTicket
from app.schemas.snapshot import MarketSnapshot, TimeframeSnapshot
from app.services.confluence import build_confluence


def _ticket(**overrides: object) -> SignalTicket:
    payload = {
        "symbol": "XAUUSD",
        "analyzedAt": "2026-09-08T18:00:00Z",
        "action": "long",
        "confidence": "medium",
        "timeframe": "H1",
        "timeframeBias": {
            "M15": "long",
            "H1": "long",
            "H4": "long",
            "D1": "long",
        },
        "entryZone": {"low": 2640.0, "high": 2648.0},
        "stop": 2632.0,
        "targets": {"tp1": 2660.0, "tp2": 2675.0},
        "invalidation": 2628.0,
        "narrative": "Stacked EMAs and a held swing.",
        "riskNotes": "Invalid under 2628.",
    }
    payload.update(overrides)
    return SignalTicket.model_validate(payload)


def _snapshot(atr: float = 8.0, swings: list[float] | None = None) -> MarketSnapshot:
    frame = TimeframeSnapshot(
        timeframe="H1",
        last_close=2644.0,
        atr=atr,
        ema20=2640.0,
        ema50=2630.0,
        bias="long",
        swing_highs=[2660.0],
        swing_lows=swings or [2642.0],
        bar_count=60,
    )
    return MarketSnapshot(
        symbol="XAUUSD",
        yahoo_symbol="GC=F",
        captured_at=datetime(2026, 9, 8, 18, 0, tzinfo=UTC),
        last_price=2644.0,
        timeframes={"H1": frame, "M15": frame, "H4": frame, "D1": frame},
    )


def test_aligned_long_with_swing_and_atr_is_high() -> None:
    report = build_confluence(_ticket(confidence="high"), _snapshot())

    assert report.headline == "Why HIGH"
    assert report.action == "long"
    assert report.passed_count == 5
    assert report.suggested_confidence == "high"
    assert all(factor.passed for factor in report.factors)


def test_mixed_timeframes_drop_confluence_to_medium() -> None:
    ticket = _ticket(
        confidence="medium",
        timeframeBias={"M15": "short", "H1": "range", "H4": "long", "D1": "long"},
    )
    report = build_confluence(ticket, _snapshot())

    assert report.headline == "Why MEDIUM"
    assert report.suggested_confidence == "medium"
    titles = {factor.id: factor.passed for factor in report.factors}
    assert titles["htf_aligned"] is True
    assert titles["signal_tf_aligned"] is False
    assert titles["ltf_not_fighting"] is False


def test_no_trade_explains_conflict_and_missing_level() -> None:
    ticket = _ticket(
        action="no_trade",
        confidence="low",
        entryZone=None,
        stop=None,
        targets=None,
        invalidation=None,
        timeframeBias={"M15": "short", "H1": "range", "H4": "long", "D1": "short"},
    )
    report = build_confluence(ticket, _snapshot())

    assert report.headline == "Why NO TRADE"
    assert report.suggested_confidence is None
    assert any(factor.id == "htf_unclear" and factor.passed for factor in report.factors)
    assert any(factor.id == "no_level" and factor.passed for factor in report.factors)


def test_snapshot_error_supports_no_trade() -> None:
    ticket = _ticket(
        action="no_trade",
        confidence="low",
        entryZone=None,
        stop=None,
        targets=None,
        invalidation=None,
    )
    snapshot = _snapshot()
    snapshot = snapshot.model_copy(update={"error": "Yahoo returned no bars", "last_price": None})
    report = build_confluence(ticket, snapshot)

    assert any(factor.id == "snapshot_failed" and factor.passed for factor in report.factors)


def _scalp_ticket(**overrides: object) -> SignalTicket:
    payload = {
        "symbol": "XAUUSD",
        "style": "scalp",
        "analyzedAt": "2026-09-08T18:00:00Z",
        "action": "long",
        "confidence": "high",
        "timeframe": "M5",
        "timeframeBias": {
            "M1": "long",
            "M5": "long",
            "M15": "long",
            "H1": "long",
        },
        "entryZone": {"low": 2640.0, "high": 2648.0},
        "stop": 2632.0,
        "targets": {"tp1": 2660.0, "tp2": 2675.0},
        "invalidation": 2628.0,
        "narrative": "M5 held the London sweep low.",
        "riskNotes": "Yahoo M5 can lag the OANDA tape.",
    }
    payload.update(overrides)
    return SignalTicket.model_validate(payload)


def _scalp_snapshot(atr: float = 8.0, swings: list[float] | None = None) -> MarketSnapshot:
    frame = TimeframeSnapshot(
        timeframe="M5",
        last_close=2644.0,
        atr=atr,
        ema20=2640.0,
        ema50=2630.0,
        bias="long",
        swing_highs=[2660.0],
        swing_lows=swings or [2642.0],
        bar_count=60,
    )
    return MarketSnapshot(
        symbol="XAUUSD",
        yahoo_symbol="GC=F",
        captured_at=datetime(2026, 9, 8, 18, 0, tzinfo=UTC),
        last_price=2644.0,
        timeframes={"M1": frame, "M5": frame, "M15": frame, "H1": frame},
    )


def test_aligned_scalp_long_is_high() -> None:
    report = build_confluence(_scalp_ticket(), _scalp_snapshot())

    assert report.headline == "Why HIGH"
    assert report.passed_count == 5
    assert report.suggested_confidence == "high"
    assert all(factor.passed for factor in report.factors)
    assert "H1/M15 stack" in report.summary


def test_scalp_m1_fighting_fails_ltf_guard() -> None:
    ticket = _scalp_ticket(
        confidence="medium",
        timeframeBias={"M1": "short", "M5": "long", "M15": "long", "H1": "long"},
    )
    report = build_confluence(ticket, _scalp_snapshot())

    titles = {factor.id: factor.passed for factor in report.factors}
    assert titles["htf_aligned"] is True
    assert titles["signal_tf_aligned"] is True
    assert titles["ltf_not_fighting"] is False
