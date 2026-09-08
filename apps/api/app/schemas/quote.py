from datetime import datetime

from app.schemas.common import ApiModel, MarketState, StatusLabel, SymbolId


class Quote(ApiModel):
    symbol: SymbolId
    last: float | None
    change: float | None
    change_percent: float | None
    as_of: datetime
    delayed: bool = True
    market_state: MarketState
    status_label: StatusLabel
    source: str


class QuoteListResponse(ApiModel):
    data: list[Quote]
