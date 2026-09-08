from typing import assert_never

from app.schemas.analysis import ConfluenceFactor, ConfluenceReport
from app.schemas.common import Action, Bias, Confidence, SignalStyle
from app.schemas.signal import SignalTicket
from app.schemas.snapshot import MarketSnapshot, TimeframeSnapshot


def build_confluence(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> ConfluenceReport:
    if ticket.action == "no_trade":
        factors = _no_trade_factors(ticket, snapshot)
        return ConfluenceReport(
            headline="Why NO TRADE",
            action=ticket.action,
            confidence=ticket.confidence,
            suggested_confidence=None,
            passed_count=sum(1 for factor in factors if factor.passed),
            factor_count=len(factors),
            summary=_no_trade_summary(factors),
            factors=factors,
        )

    factors = _trade_factors(ticket, snapshot)
    passed = sum(1 for factor in factors if factor.passed)
    suggested = _suggested_confidence(passed)
    return ConfluenceReport(
        headline=f"Why {ticket.confidence.upper()}",
        action=ticket.action,
        confidence=ticket.confidence,
        suggested_confidence=suggested,
        passed_count=passed,
        factor_count=len(factors),
        summary=_trade_summary(ticket.action, ticket.confidence, ticket.style, passed, len(factors)),
        factors=factors,
    )


def _suggested_confidence(passed: int) -> Confidence:
    if passed >= 5:
        return "high"
    if passed >= 3:
        return "medium"
    return "low"


def _signal_frame(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> TimeframeSnapshot | None:
    if snapshot is None:
        return None
    return snapshot.timeframes.get(ticket.timeframe)


def _trade_factors(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> list[ConfluenceFactor]:
    if ticket.style == "swing":
        return _swing_trade_factors(ticket, snapshot)
    if ticket.style == "scalp":
        return _scalp_trade_factors(ticket, snapshot)
    assert_never(ticket.style)


def _swing_trade_factors(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> list[ConfluenceFactor]:
    action = ticket.action
    h4 = ticket.timeframe_bias["H4"]
    d1 = ticket.timeframe_bias["D1"]
    signal_bias = ticket.timeframe_bias[ticket.timeframe]
    m15 = ticket.timeframe_bias["M15"]
    frame = _signal_frame(ticket, snapshot)
    return [
        _htf_factor(action, h4, d1, "H4", "D1"),
        _signal_tf_factor(ticket.timeframe, signal_bias, action),
        _ltf_factor("M15", m15, action),
        _stop_atr_factor(ticket, frame),
        _swing_factor(ticket, frame),
    ]


def _scalp_trade_factors(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> list[ConfluenceFactor]:
    action = ticket.action
    h1 = ticket.timeframe_bias["H1"]
    m15 = ticket.timeframe_bias["M15"]
    m5 = ticket.timeframe_bias["M5"]
    m1 = ticket.timeframe_bias["M1"]
    frame = _signal_frame(ticket, snapshot)
    return [
        _htf_factor(action, h1, m15, "H1", "M15"),
        _signal_tf_factor("M5", m5, action),
        _ltf_factor("M1", m1, action),
        _stop_atr_factor(ticket, frame),
        _swing_factor(ticket, frame),
    ]


def _no_trade_factors(ticket: SignalTicket, snapshot: MarketSnapshot | None) -> list[ConfluenceFactor]:
    if ticket.style == "swing":
        return _swing_no_trade_factors(ticket, snapshot)
    if ticket.style == "scalp":
        return _scalp_no_trade_factors(ticket, snapshot)
    assert_never(ticket.style)


def _swing_no_trade_factors(
    ticket: SignalTicket,
    snapshot: MarketSnapshot | None,
) -> list[ConfluenceFactor]:
    h4 = ticket.timeframe_bias["H4"]
    d1 = ticket.timeframe_bias["D1"]
    h1 = ticket.timeframe_bias["H1"]
    m15 = ticket.timeframe_bias["M15"]
    snapshot_failed = _snapshot_failed(snapshot)
    htf_unclear = h4 != d1 or h4 == "range" or d1 == "range"
    if h4 in {"long", "short"}:
        conflict = _is_opposite(h4, m15) or _is_opposite(h4, h1)
    else:
        conflict = h1 in {"long", "short"} and m15 in {"long", "short"} and h1 != m15
    return [
        _snapshot_failed_factor(snapshot, snapshot_failed),
        ConfluenceFactor(
            id="htf_unclear",
            passed=htf_unclear,
            title="H4 and D1 are not a clean team",
            detail=f"H4 is {h4}, D1 is {d1}.",
        ),
        ConfluenceFactor(
            id="timeframe_conflict",
            passed=bool(conflict),
            title="Lower timeframes disagree",
            detail=f"M15 {m15}, H1 {h1}, H4 {h4}.",
        ),
        _no_level_factor(ticket),
    ]


def _scalp_no_trade_factors(
    ticket: SignalTicket,
    snapshot: MarketSnapshot | None,
) -> list[ConfluenceFactor]:
    h1 = ticket.timeframe_bias["H1"]
    m15 = ticket.timeframe_bias["M15"]
    m5 = ticket.timeframe_bias["M5"]
    m1 = ticket.timeframe_bias["M1"]
    snapshot_failed = _snapshot_failed(snapshot)
    htf_unclear = h1 != m15 or h1 == "range" or m15 == "range"
    if h1 in {"long", "short"}:
        conflict = _is_opposite(h1, m1) or _is_opposite(h1, m15)
    else:
        conflict = m1 in {"long", "short"} and m5 in {"long", "short"} and m1 != m5
    return [
        _snapshot_failed_factor(snapshot, snapshot_failed),
        ConfluenceFactor(
            id="htf_unclear",
            passed=htf_unclear,
            title="H1 and M15 are not a clean team",
            detail=f"H1 is {h1}, M15 is {m15}.",
        ),
        ConfluenceFactor(
            id="timeframe_conflict",
            passed=bool(conflict),
            title="Lower timeframes disagree",
            detail=f"M1 {m1}, M5 {m5}, H1 {h1}.",
        ),
        _no_level_factor(ticket),
    ]


def _snapshot_failed(snapshot: MarketSnapshot | None) -> bool:
    return snapshot is None or snapshot.error is not None or snapshot.last_price is None


def _snapshot_failed_factor(snapshot: MarketSnapshot | None, failed: bool) -> ConfluenceFactor:
    if snapshot is not None and snapshot.error:
        detail = snapshot.error
    elif failed:
        detail = "No usable last price / OHLC snapshot."
    else:
        detail = "Snapshot printed usable levels."
    return ConfluenceFactor(
        id="snapshot_failed",
        passed=failed,
        title="Tape snapshot is not reliable",
        detail=detail,
    )


def _no_level_factor(ticket: SignalTicket) -> ConfluenceFactor:
    return ConfluenceFactor(
        id="no_level",
        passed=ticket.entry_zone is None,
        title="No mapped entry level",
        detail=(
            "No entry/stop/target to mark on the chart."
            if ticket.entry_zone is None
            else "A level exists, so a no-trade is discretionary."
        ),
    )


def _htf_factor(
    action: Action,
    higher: Bias,
    highest: Bias,
    higher_label: str,
    highest_label: str,
) -> ConfluenceFactor:
    passed = higher == action and highest == action
    return ConfluenceFactor(
        id="htf_aligned",
        passed=passed,
        title=f"{higher_label} and {highest_label} agree with the trade",
        detail=(
            f"{higher_label} is {higher}, {highest_label} is {highest}."
            if passed
            else f"{higher_label} is {higher} and {highest_label} is {highest}, not a stacked {action}."
        ),
    )


def _signal_tf_factor(timeframe: str, signal_bias: Bias, action: Action) -> ConfluenceFactor:
    passed = signal_bias == action
    return ConfluenceFactor(
        id="signal_tf_aligned",
        passed=passed,
        title=f"{timeframe} agrees with the trade",
        detail=(
            f"{timeframe} bias is {signal_bias}."
            if passed
            else f"{timeframe} is {signal_bias}, not {action}."
        ),
    )


def _ltf_factor(timeframe: str, bias: Bias, action: Action) -> ConfluenceFactor:
    fighting = _is_opposite(action, bias)
    return ConfluenceFactor(
        id="ltf_not_fighting",
        passed=not fighting,
        title=f"{timeframe} is not fighting the idea",
        detail=(
            f"{timeframe} is not countertrend."
            if not fighting
            else f"{timeframe} is {bias} against a {action}."
        ),
    )


def _is_opposite(direction: Action | Bias, bias: Bias) -> bool:
    return (direction == "long" and bias == "short") or (direction == "short" and bias == "long")


def _stop_atr_factor(ticket: SignalTicket, frame: TimeframeSnapshot | None) -> ConfluenceFactor:
    if ticket.entry_zone is None or ticket.stop is None or frame is None or frame.atr is None:
        return ConfluenceFactor(
            id="stop_vs_atr",
            passed=False,
            title="Stop has ATR breathing room",
            detail="ATR is missing, so the stop cannot be scored.",
        )
    if ticket.action == "long":
        distance = abs(ticket.entry_zone.low - ticket.stop)
    else:
        distance = abs(ticket.stop - ticket.entry_zone.high)
    passed = distance >= 0.6 * frame.atr
    return ConfluenceFactor(
        id="stop_vs_atr",
        passed=passed,
        title="Stop has ATR breathing room",
        detail=(
            f"Stop is {distance:.2f} from the zone versus ATR {frame.atr:.2f}."
            if passed
            else f"Stop is only {distance:.2f} versus ATR {frame.atr:.2f} — too tight."
        ),
    )


def _swing_factor(ticket: SignalTicket, frame: TimeframeSnapshot | None) -> ConfluenceFactor:
    if ticket.entry_zone is None or frame is None:
        return ConfluenceFactor(
            id="entry_at_swing",
            passed=False,
            title="Entry sits on a mapped swing",
            detail="No swing map for this timeframe.",
        )
    swings = [*frame.swing_highs, *frame.swing_lows]
    zone = ticket.entry_zone
    hit = any(zone.low <= swing <= zone.high for swing in swings)
    if not hit and frame.atr:
        mid = (zone.low + zone.high) / 2
        hit = any(abs(swing - mid) <= 0.35 * frame.atr for swing in swings)
    return ConfluenceFactor(
        id="entry_at_swing",
        passed=hit,
        title="Entry sits on a mapped swing",
        detail="Zone overlaps a snapshot swing." if hit else "Zone is not on a mapped swing high/low.",
    )


def _trade_summary(
    action: Action,
    confidence: Confidence,
    style: SignalStyle,
    passed: int,
    total: int,
) -> str:
    if style == "scalp":
        stack = "H1/M15 stack, M5, M1, ATR stop, swing"
    elif style == "swing":
        stack = "HTF stack, signal timeframe, M15, ATR stop, swing"
    else:
        assert_never(style)
    return (
        f"{confidence.capitalize()} {action} because {passed} of {total} chart checks line up "
        f"({stack})."
    )


def _no_trade_summary(factors: list[ConfluenceFactor]) -> str:
    reasons = [factor.title.lower() for factor in factors if factor.passed]
    if not reasons:
        return "No trade: structure is unclear and there is no clean chart trigger."
    return "No trade because " + "; ".join(reasons) + "."
