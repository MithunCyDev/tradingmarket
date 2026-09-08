from pathlib import Path

import pytest
from pydantic import ValidationError

from app.repositories.json_store import JsonFileStore
from app.schemas.signal import SignalTicket
from app.services.signal_store import SignalStore


def _store(tmp_path: Path) -> SignalStore:
    return SignalStore(JsonFileStore(tmp_path), JsonFileStore(tmp_path / "scalp"))


def _valid_ticket() -> dict:
    return {
        "symbol": "XAUUSD",
        "analyzedAt": "2026-09-08T18:00:00Z",
        "action": "long",
        "confidence": "medium",
        "timeframe": "H1",
        "timeframeBias": {
            "M15": "long",
            "H1": "long",
            "H4": "range",
            "D1": "long",
        },
        "entryZone": {"low": 2640.0, "high": 2648.0},
        "stop": 2632.0,
        "targets": {"tp1": 2660.0, "tp2": 2675.0},
        "invalidation": 2628.0,
        "narrative": "H1 reclaimed VWAP after a London sweep.",
        "riskNotes": "Skip if New York opens through the stop.",
    }


def test_signal_store_round_trips_a_ticket(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ticket = SignalTicket.model_validate(_valid_ticket())

    store.write(ticket)
    loaded = store.read("XAUUSD")

    assert loaded is not None
    assert loaded.action == "long"
    assert loaded.entry_zone is not None
    assert loaded.entry_zone.low == 2640.0
    assert loaded.targets is not None
    assert loaded.targets.tp2 == 2675.0


def test_signal_store_returns_none_when_missing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    assert store.read("BTCUSD") is None


def test_missing_style_defaults_to_swing() -> None:
    ticket = SignalTicket.model_validate(_valid_ticket())
    assert ticket.style == "swing"


def test_scalp_ticket_requires_m5_and_scalp_bias() -> None:
    payload = _valid_ticket()
    payload["style"] = "scalp"
    payload["timeframe"] = "M5"
    payload["timeframeBias"] = {
        "M1": "long",
        "M5": "long",
        "M15": "long",
        "H1": "long",
    }

    ticket = SignalTicket.model_validate(payload)

    assert ticket.style == "scalp"
    assert ticket.timeframe == "M5"


def test_scalp_ticket_rejects_swing_bias_keys() -> None:
    payload = _valid_ticket()
    payload["style"] = "scalp"
    payload["timeframe"] = "M5"

    with pytest.raises(ValidationError):
        SignalTicket.model_validate(payload)


def test_scalp_ticket_rejects_non_m5_timeframe() -> None:
    payload = _valid_ticket()
    payload["style"] = "scalp"
    payload["timeframe"] = "H1"
    payload["timeframeBias"] = {
        "M1": "long",
        "M5": "long",
        "M15": "long",
        "H1": "long",
    }

    with pytest.raises(ValidationError):
        SignalTicket.model_validate(payload)


def test_swing_ticket_still_rejects_missing_htf_bias() -> None:
    payload = _valid_ticket()
    payload["timeframeBias"] = {"M15": "long", "H1": "long"}

    with pytest.raises(ValidationError):
        SignalTicket.model_validate(payload)


def test_no_trade_ticket_allows_null_levels() -> None:
    payload = _valid_ticket()
    payload["action"] = "no_trade"
    payload["entryZone"] = None
    payload["stop"] = None
    payload["targets"] = None
    payload["invalidation"] = None

    ticket = SignalTicket.model_validate(payload)

    assert ticket.action == "no_trade"
    assert ticket.entry_zone is None


def test_long_signal_requires_levels() -> None:
    payload = _valid_ticket()
    payload["stop"] = None

    with pytest.raises(ValidationError):
        SignalTicket.model_validate(payload)


def test_rejects_unknown_symbol() -> None:
    payload = _valid_ticket()
    payload["symbol"] = "AAPL"

    with pytest.raises(ValidationError):
        SignalTicket.model_validate(payload)


def _scalp_payload() -> dict:
    return {
        "symbol": "XAUUSD",
        "style": "scalp",
        "analyzedAt": "2026-09-08T18:05:00Z",
        "action": "short",
        "confidence": "medium",
        "timeframe": "M5",
        "timeframeBias": {
            "M1": "short",
            "M5": "short",
            "M15": "short",
            "H1": "range",
        },
        "entryZone": {"low": 2648.0, "high": 2652.0},
        "stop": 2658.0,
        "targets": {"tp1": 2640.0, "tp2": 2632.0},
        "invalidation": 2662.0,
        "narrative": "M5 rejected the London high.",
        "riskNotes": "Stand aside if Yahoo lags the live tape.",
    }


def test_writing_scalp_does_not_replace_swing(tmp_path: Path) -> None:
    store = _store(tmp_path)
    swing = SignalTicket.model_validate(_valid_ticket())
    scalp = SignalTicket.model_validate(_scalp_payload())

    store.write(swing)
    store.write(scalp)

    loaded_swing = store.read("XAUUSD", "swing")
    loaded_scalp = store.read("XAUUSD", "scalp")

    assert loaded_swing is not None
    assert loaded_swing.action == "long"
    assert loaded_swing.timeframe == "H1"
    assert loaded_scalp is not None
    assert loaded_scalp.action == "short"
    assert loaded_scalp.timeframe == "M5"
    assert (tmp_path / "XAUUSD.json").exists()
    assert (tmp_path / "scalp" / "XAUUSD.json").exists()


def test_check_signal_cli_reads_style(tmp_path: Path) -> None:
    from app.cli import check_signal
    from app.config import Settings
    from app.container import build_container

    container = build_container(Settings(data_dir=tmp_path))
    container.signal_store.write(SignalTicket.model_validate(_scalp_payload()))

    assert check_signal("GOLD", tmp_path, "scalp") == 0
    assert check_signal("GOLD", tmp_path, "swing") == 1
