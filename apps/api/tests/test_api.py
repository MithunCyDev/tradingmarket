from datetime import UTC, datetime
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import REPO_ROOT, Settings
from app.container import build_container
from app.main import create_app
from app.schemas.signal import SignalTicket
from app.services.market_data import Bar, RawQuote
from tests.conftest import make_trend_bars


class FakeMarketData:
    def history(self, yahoo_symbol: str, interval: str, period: str) -> list[Bar]:
        return make_trend_bars(60, start=100.0, step=1.0)

    def quote(self, yahoo_symbol: str) -> RawQuote:
        return RawQuote(last=2651.4, previous_close=2640.0, as_of=datetime(2026, 9, 8, 18, 0, tzinfo=UTC))


def _client(tmp_path: Path) -> TestClient:
    settings = Settings(
        data_dir=tmp_path,
        catalog_path=REPO_ROOT / "config" / "instruments.json",
        quote_cache_seconds=60,
    )
    app = create_app(settings=settings, container=build_container(settings, FakeMarketData()))
    return TestClient(app)


def _ticket_payload() -> dict:
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
        "narrative": "H1 reclaimed the prior day's high.",
        "riskNotes": "Invalid if New York cash open trades through 2628.",
    }


def test_lists_the_five_desk_instruments(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/instruments")

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["data"]]
    assert ids == ["XAUUSD", "BTCUSD", "XAGUSD", "USOIL", "EURUSD"]
    assert response.json()["data"][0]["tvSymbol"] == "OANDA:XAUUSD"


def test_missing_signal_returns_structured_404(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/signals/XAUUSD")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_unknown_symbol_returns_404(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/signals/AAPL")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "NOT_FOUND"


def test_written_signal_is_returned_and_gold_alias_works(tmp_path: Path) -> None:
    client = _client(tmp_path)
    container = client.app.state.container
    container.signal_store.write(SignalTicket.model_validate(_ticket_payload()))

    by_id = client.get("/api/v1/signals/XAUUSD")
    by_alias = client.get("/api/v1/signals/GOLD")
    briefing = client.get("/api/v1/briefings/GOLD")

    assert by_id.status_code == 200
    assert by_alias.status_code == 200
    assert briefing.status_code == 200
    assert by_id.json()["action"] == "long"
    assert by_id.json()["entryZone"]["low"] == 2640.0
    assert by_alias.json()["symbol"] == "XAUUSD"


def test_quotes_use_vendor_last_and_previous_close(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/quotes")

    assert response.status_code == 200
    gold = next(item for item in response.json()["data"] if item["symbol"] == "XAUUSD")
    assert gold["last"] == 2651.4
    assert gold["change"] == 11.4


def test_analysis_explains_a_written_ticket(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.app.state.container.signal_store.write(SignalTicket.model_validate(_ticket_payload()))

    missing = client.get("/api/v1/analysis/BTCUSD")
    found = client.get("/api/v1/analysis/GOLD")

    assert missing.status_code == 404
    assert found.status_code == 200
    assert found.json()["confluence"]["headline"] == "Why MEDIUM"
    assert found.json()["levels"][0]["label"] == "ENTRY L"


def test_chart_returns_ohlc_for_an_instrument(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/charts/XAUUSD", params={"timeframe": "H1"})

    assert response.status_code == 200
    assert len(response.json()["bars"]) == 60
    assert response.json()["timeframe"] == "H1"


def test_missing_snapshot_returns_404(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/snapshots/BTCUSD")
    assert response.status_code == 404


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


def test_scalp_style_404_when_only_swing_exists(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.app.state.container.signal_store.write(SignalTicket.model_validate(_ticket_payload()))

    scalp = client.get("/api/v1/signals/XAUUSD", params={"style": "scalp"})
    swing = client.get("/api/v1/signals/XAUUSD", params={"style": "swing"})
    analysis = client.get("/api/v1/analysis/XAUUSD", params={"style": "scalp"})

    assert scalp.status_code == 404
    assert analysis.status_code == 404
    assert swing.status_code == 200
    assert swing.json()["action"] == "long"
    assert swing.json()["style"] == "swing"


def test_scalp_style_returns_scalp_ticket_without_touching_swing(tmp_path: Path) -> None:
    client = _client(tmp_path)
    store = client.app.state.container.signal_store
    store.write(SignalTicket.model_validate(_ticket_payload()))
    store.write(SignalTicket.model_validate(_scalp_payload()))

    scalp = client.get("/api/v1/signals/GOLD", params={"style": "scalp"})
    swing = client.get("/api/v1/signals/GOLD")
    analysis = client.get("/api/v1/analysis/GOLD", params={"style": "scalp"})

    assert scalp.status_code == 200
    assert scalp.json()["style"] == "scalp"
    assert scalp.json()["timeframe"] == "M5"
    assert swing.json()["style"] == "swing"
    assert swing.json()["timeframe"] == "H1"
    assert analysis.status_code == 200
    assert analysis.json()["confluence"]["headline"] == "Why MEDIUM"


def test_chart_accepts_m5(tmp_path: Path) -> None:
    response = _client(tmp_path).get("/api/v1/charts/XAUUSD", params={"timeframe": "M5"})

    assert response.status_code == 200
    assert response.json()["timeframe"] == "M5"
    assert len(response.json()["bars"]) == 60
