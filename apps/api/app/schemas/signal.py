from datetime import datetime
from typing import assert_never

from pydantic import Field, model_validator

from app.schemas.common import (
    SCALP_BIAS_FRAMES,
    SCALP_SIGNAL_FRAMES,
    SWING_BIAS_FRAMES,
    SWING_SIGNAL_FRAMES,
    Action,
    ApiModel,
    Bias,
    Confidence,
    SignalStyle,
    SymbolId,
    Timeframe,
)


class EntryZone(ApiModel):
    low: float
    high: float

    @model_validator(mode="after")
    def low_must_be_lte_high(self) -> "EntryZone":
        if self.low > self.high:
            raise ValueError("entryZone.low must be less than or equal to entryZone.high")
        return self


class Targets(ApiModel):
    tp1: float
    tp2: float


class SignalTicket(ApiModel):
    symbol: SymbolId
    style: SignalStyle = "swing"
    analyzed_at: datetime
    action: Action
    confidence: Confidence
    timeframe: Timeframe
    timeframe_bias: dict[Timeframe, Bias]
    entry_zone: EntryZone | None = None
    stop: float | None = None
    targets: Targets | None = None
    invalidation: float | None = None
    narrative: str = Field(..., min_length=1, max_length=2000)
    risk_notes: str = Field(..., min_length=1, max_length=2000)

    @model_validator(mode="after")
    def trade_signals_need_levels(self) -> "SignalTicket":
        if self.action == "no_trade":
            return self
        missing = [
            name
            for name, value in (
                ("entryZone", self.entry_zone),
                ("stop", self.stop),
                ("targets", self.targets),
                ("invalidation", self.invalidation),
            )
            if value is None
        ]
        if missing:
            raise ValueError(f"Trade signals require {', '.join(missing)}")
        return self

    @model_validator(mode="after")
    def timeframe_matches_style(self) -> "SignalTicket":
        if self.style == "swing":
            allowed = SWING_SIGNAL_FRAMES
            if self.timeframe not in allowed:
                raise ValueError("swing tickets must use M15, H1, H4, or D1")
            return self
        if self.style == "scalp":
            if self.timeframe not in SCALP_SIGNAL_FRAMES:
                raise ValueError("scalp tickets must use M5")
            return self
        assert_never(self.style)

    @model_validator(mode="after")
    def timeframe_bias_is_complete(self) -> "SignalTicket":
        if self.style == "swing":
            required = set(SWING_BIAS_FRAMES)
            message = "timeframeBias must include M15, H1, H4, and D1"
        elif self.style == "scalp":
            required = set(SCALP_BIAS_FRAMES)
            message = "timeframeBias must include M1, M5, M15, and H1"
        else:
            assert_never(self.style)
        if set(self.timeframe_bias) != required:
            raise ValueError(message)
        return self
