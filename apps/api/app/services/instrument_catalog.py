import json
from pathlib import Path

from app.schemas.common import SYMBOL_ALIASES, SymbolId
from app.schemas.instrument import Instrument


class UnknownInstrumentError(Exception):
    """Raised when a symbol or alias is not on the desk."""


class InstrumentCatalog:
    def __init__(self, catalog_path: Path) -> None:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
        instruments = [Instrument.model_validate(item) for item in raw["instruments"]]
        self._by_id: dict[SymbolId, Instrument] = {item.id: item for item in instruments}

    def all(self) -> list[Instrument]:
        return list(self._by_id.values())

    def get(self, symbol: SymbolId) -> Instrument:
        return self._by_id[symbol]

    def resolve(self, raw: str) -> SymbolId:
        key = " ".join(raw.strip().upper().replace("-", "/").split())
        symbol = SYMBOL_ALIASES.get(key)
        if symbol is None or symbol not in self._by_id:
            raise UnknownInstrumentError(f"Unknown instrument: {raw}")
        return symbol
