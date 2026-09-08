from app.schemas.common import ApiModel, MarketKind, SymbolId


class Instrument(ApiModel):
    id: SymbolId
    label: str
    tv_symbol: str
    yahoo_symbol: str
    price_decimals: int
    market_kind: MarketKind


class InstrumentListResponse(ApiModel):
    data: list[Instrument]
