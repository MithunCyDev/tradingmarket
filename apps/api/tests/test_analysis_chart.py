from datetime import UTC, datetime
from pathlib import Path

from app.schemas.analysis import AnalysisLevel, ChartBar, ChartResponse
from app.schemas.signal import SignalTicket
from app.services.analysis_chart import artifact_filename, render_analysis_chart


def _ticket() -> SignalTicket:
    return SignalTicket.model_validate(
        {
            "symbol": "XAUUSD",
            "style": "swing",
            "analyzedAt": "2026-09-09T08:25:00Z",
            "action": "no_trade",
            "confidence": "medium",
            "timeframe": "H1",
            "timeframeBias": {
                "M15": "long",
                "H1": "range",
                "H4": "short",
                "D1": "range",
            },
            "entryZone": None,
            "stop": None,
            "targets": None,
            "invalidation": None,
            "narrative": "HTF is not stacked.",
            "riskNotes": "Stand aside.",
        }
    )


def test_render_analysis_chart_writes_png(tmp_path: Path) -> None:
    origin = datetime(2026, 9, 1, tzinfo=UTC)
    bars = [
        ChartBar(
            time=int((origin.timestamp() + index * 3600)),
            open=4400 + index,
            high=4402 + index,
            low=4398 + index,
            close=4401 + index,
        )
        for index in range(40)
    ]
    chart = ChartResponse(
        symbol="XAUUSD",
        timeframe="H1",
        bars=bars,
        ema20=[None] * 20 + [4405.0] * 20,
        ema50=[None] * 30 + [4390.0] * 10,
        swing_highs=[4440.0],
        swing_lows=[4370.0],
    )
    output = tmp_path / "gold.png"

    render_analysis_chart(
        chart,
        _ticket(),
        [AnalysisLevel(id="stop", label="STOP", price=4380.0, kind="stop")],
        4402.99,
        2,
        output,
        "PAXG-USD",
        "GOLD",
    )

    assert output.exists()
    assert output.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"
    assert output.stat().st_size > 8_000


def test_artifact_filename_is_stable_and_unique() -> None:
    name = artifact_filename(_ticket())
    assert name == "xauusd_swing_h1_no_trade_20260909T0825.png"
