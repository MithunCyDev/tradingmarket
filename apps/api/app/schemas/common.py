from typing import Literal

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

SymbolId = Literal["XAUUSD", "BTCUSD", "XAGUSD", "USOIL", "EURUSD"]
Bias = Literal["long", "short", "range"]
Action = Literal["long", "short", "no_trade"]
Confidence = Literal["low", "medium", "high"]
Timeframe = Literal["M1", "M5", "M15", "H1", "H4", "D1"]
SignalStyle = Literal["swing", "scalp"]
MarketKind = Literal["crypto", "forex", "cme_metals", "cme_energy"]
MarketState = Literal["open", "closed"]
StatusLabel = Literal["LIVE", "DELAYED", "CLOSED"]

SYMBOL_IDS: tuple[SymbolId, ...] = ("XAUUSD", "BTCUSD", "XAGUSD", "USOIL", "EURUSD")
TIMEFRAMES: tuple[Timeframe, ...] = ("M1", "M5", "M15", "H1", "H4", "D1")
SWING_BIAS_FRAMES: tuple[Timeframe, ...] = ("M15", "H1", "H4", "D1")
SCALP_BIAS_FRAMES: tuple[Timeframe, ...] = ("M1", "M5", "M15", "H1")
SWING_SIGNAL_FRAMES: tuple[Timeframe, ...] = ("M15", "H1", "H4", "D1")
SCALP_SIGNAL_FRAMES: tuple[Timeframe, ...] = ("M5",)

SYMBOL_ALIASES: dict[str, SymbolId] = {
    "XAUUSD": "XAUUSD",
    "GOLD": "XAUUSD",
    "XAU": "XAUUSD",
    "BTCUSD": "BTCUSD",
    "BTC": "BTCUSD",
    "BITCOIN": "BTCUSD",
    "XAGUSD": "XAGUSD",
    "SILVER": "XAGUSD",
    "XAG": "XAGUSD",
    "USOIL": "USOIL",
    "OIL": "USOIL",
    "US OIL": "USOIL",
    "CRUDE": "USOIL",
    "EURUSD": "EURUSD",
    "EUR/USD": "EURUSD",
    "EUR": "EURUSD",
}


class ApiModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        extra="forbid",
    )


class ErrorDetail(ApiModel):
    field: str | None = None
    message: str


class ErrorBody(ApiModel):
    code: str
    message: str
    details: list[ErrorDetail] = []


class ErrorResponse(ApiModel):
    error: ErrorBody
