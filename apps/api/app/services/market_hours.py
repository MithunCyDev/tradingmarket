from datetime import datetime
from typing import Literal
from zoneinfo import ZoneInfo

from app.schemas.common import MarketKind

NEW_YORK = ZoneInfo("America/New_York")
CHICAGO = ZoneInfo("America/Chicago")

StatusLabel = Literal["LIVE", "DELAYED", "CLOSED"]


def _minutes(moment: datetime) -> int:
    return moment.hour * 60 + moment.minute


def is_market_open(kind: MarketKind, now: datetime) -> bool:
    if kind == "crypto":
        return True
    if kind == "forex":
        return _forex_open(now.astimezone(NEW_YORK))
    if kind == "cme_metals":
        return _cme_session_open(
            now.astimezone(NEW_YORK),
            sunday_open=18 * 60,
            friday_close=17 * 60,
            break_start=17 * 60,
            break_end=18 * 60,
        )
    if kind == "cme_energy":
        return _cme_session_open(
            now.astimezone(CHICAGO),
            sunday_open=17 * 60,
            friday_close=16 * 60,
            break_start=16 * 60,
            break_end=17 * 60,
        )
    raise AssertionError(f"Unhandled market kind: {kind}")


def status_label(kind: MarketKind, now: datetime, source: str) -> StatusLabel:
    if not is_market_open(kind, now):
        return "CLOSED"
    if source == "binance":
        return "LIVE"
    return "DELAYED"


def _forex_open(local: datetime) -> bool:
    weekday = local.weekday()
    if weekday == 5:
        return False
    if weekday == 6:
        return _minutes(local) >= 17 * 60
    if weekday == 4:
        return _minutes(local) < 17 * 60
    return True


def _cme_session_open(
    local: datetime,
    sunday_open: int,
    friday_close: int,
    break_start: int,
    break_end: int,
) -> bool:
    weekday = local.weekday()
    clock = _minutes(local)
    if weekday == 5:
        return False
    if weekday == 6:
        return clock >= sunday_open
    if weekday == 4:
        return clock < friday_close
    return clock < break_start or clock >= break_end
