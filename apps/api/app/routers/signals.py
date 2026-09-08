from fastapi import APIRouter, HTTPException, Query, Request

from app.container import AppContainer
from app.schemas.common import SignalStyle, SymbolId
from app.schemas.signal import SignalTicket
from app.services.instrument_catalog import UnknownInstrumentError

router = APIRouter(tags=["signals"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


def _resolve_symbol(request: Request, symbol: str) -> SymbolId:
    try:
        return _container(request).catalog.resolve(symbol)
    except UnknownInstrumentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/signals/{symbol}")
def get_signal(
    symbol: str,
    request: Request,
    style: SignalStyle = Query(default="swing"),
) -> SignalTicket:
    resolved = _resolve_symbol(request, symbol)
    ticket = _container(request).signal_store.read(resolved, style)
    if ticket is None:
        raise HTTPException(status_code=404, detail=f"No signal yet for {resolved}")
    return ticket


@router.get("/briefings/{symbol}")
def get_briefing(
    symbol: str,
    request: Request,
    style: SignalStyle = Query(default="swing"),
) -> SignalTicket:
    """Alias for clients that still call the briefing path from the original plan."""
    return get_signal(symbol, request, style)
