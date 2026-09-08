from typing import assert_never

from app.repositories.json_store import JsonFileStore
from app.schemas.common import SignalStyle, SymbolId
from app.schemas.signal import SignalTicket


class SignalStore:
    def __init__(self, swing_repository: JsonFileStore, scalp_repository: JsonFileStore) -> None:
        self._swing_repository = swing_repository
        self._scalp_repository = scalp_repository

    def read(self, symbol: SymbolId, style: SignalStyle = "swing") -> SignalTicket | None:
        payload = self._repository(style).read(symbol)
        if payload is None:
            return None
        return SignalTicket.model_validate(payload)

    def write(self, ticket: SignalTicket) -> None:
        self._repository(ticket.style).write(
            ticket.symbol,
            ticket.model_dump(mode="json", by_alias=True),
        )

    def _repository(self, style: SignalStyle) -> JsonFileStore:
        if style == "swing":
            return self._swing_repository
        if style == "scalp":
            return self._scalp_repository
        assert_never(style)
