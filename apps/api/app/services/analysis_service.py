from app.schemas.analysis import AnalysisLevel, AnalysisResponse
from app.schemas.common import SignalStyle, SymbolId
from app.schemas.signal import SignalTicket
from app.services.confluence import build_confluence
from app.services.signal_store import SignalStore
from app.services.snapshot_store import SnapshotStore


class AnalysisNotFoundError(Exception):
    """Raised when there is no ticket to explain."""


class AnalysisService:
    def __init__(self, signals: SignalStore, snapshots: SnapshotStore) -> None:
        self._signals = signals
        self._snapshots = snapshots

    def get(self, symbol: SymbolId, style: SignalStyle = "swing") -> AnalysisResponse:
        ticket = self._signals.read(symbol, style)
        if ticket is None:
            raise AnalysisNotFoundError(symbol)
        snapshot = self._snapshots.read(symbol)
        return AnalysisResponse(
            symbol=symbol,
            analyzed_at=ticket.analyzed_at,
            confluence=build_confluence(ticket, snapshot),
            levels=_levels_from_ticket(ticket),
        )


def _levels_from_ticket(ticket: SignalTicket) -> list[AnalysisLevel]:
    levels: list[AnalysisLevel] = []
    if ticket.entry_zone is not None:
        levels.append(
            AnalysisLevel(id="entry_low", label="ENTRY L", price=ticket.entry_zone.low, kind="entry")
        )
        levels.append(
            AnalysisLevel(id="entry_high", label="ENTRY H", price=ticket.entry_zone.high, kind="entry")
        )
    if ticket.stop is not None:
        levels.append(AnalysisLevel(id="stop", label="STOP", price=ticket.stop, kind="stop"))
    if ticket.targets is not None:
        levels.append(AnalysisLevel(id="tp1", label="TP1", price=ticket.targets.tp1, kind="target"))
        levels.append(AnalysisLevel(id="tp2", label="TP2", price=ticket.targets.tp2, kind="target"))
    if ticket.invalidation is not None:
        levels.append(
            AnalysisLevel(id="invalidation", label="INVALID", price=ticket.invalidation, kind="invalidation")
        )
    return levels
