from app.repositories.json_store import JsonFileStore
from app.schemas.common import SymbolId
from app.schemas.snapshot import MarketSnapshot


class SnapshotStore:
    def __init__(self, repository: JsonFileStore) -> None:
        self._repository = repository

    def read(self, symbol: SymbolId) -> MarketSnapshot | None:
        payload = self._repository.read(symbol)
        if payload is None:
            return None
        return MarketSnapshot.model_validate(payload)

    def write(self, snapshot: MarketSnapshot) -> None:
        self._repository.write(
            snapshot.symbol,
            snapshot.model_dump(mode="json", by_alias=True),
        )
