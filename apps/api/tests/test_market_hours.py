from datetime import datetime
from zoneinfo import ZoneInfo

from app.services.market_hours import is_market_open, status_label

NY = ZoneInfo("America/New_York")
CHI = ZoneInfo("America/Chicago")


def test_crypto_is_open_on_the_weekend() -> None:
    saturday = datetime(2026, 9, 5, 12, 0, tzinfo=NY)
    assert is_market_open("crypto", saturday) is True
    assert status_label("crypto", saturday, source="binance") == "LIVE"


def test_forex_is_closed_on_saturday() -> None:
    saturday = datetime(2026, 9, 5, 12, 0, tzinfo=NY)
    assert is_market_open("forex", saturday) is False
    assert status_label("forex", saturday, source="yahoo") == "CLOSED"


def test_forex_opens_sunday_evening_new_york() -> None:
    before = datetime(2026, 9, 6, 16, 59, tzinfo=NY)
    after = datetime(2026, 9, 6, 17, 0, tzinfo=NY)
    assert is_market_open("forex", before) is False
    assert is_market_open("forex", after) is True


def test_forex_closes_friday_evening_new_york() -> None:
    open_window = datetime(2026, 9, 4, 16, 59, tzinfo=NY)
    closed = datetime(2026, 9, 4, 17, 0, tzinfo=NY)
    assert is_market_open("forex", open_window) is True
    assert is_market_open("forex", closed) is False


def test_metals_have_weekday_maintenance_break() -> None:
    break_time = datetime(2026, 9, 9, 17, 30, tzinfo=NY)
    lunch = datetime(2026, 9, 9, 12, 0, tzinfo=NY)
    assert is_market_open("cme_metals", break_time) is False
    assert is_market_open("cme_metals", lunch) is True


def test_energy_has_weekday_maintenance_break() -> None:
    break_time = datetime(2026, 9, 9, 16, 30, tzinfo=CHI)
    lunch = datetime(2026, 9, 9, 11, 0, tzinfo=CHI)
    assert is_market_open("cme_energy", break_time) is False
    assert is_market_open("cme_energy", lunch) is True


def test_open_yahoo_quote_is_marked_delayed() -> None:
    lunch = datetime(2026, 9, 9, 12, 0, tzinfo=NY)
    assert status_label("forex", lunch, source="yahoo") == "DELAYED"
