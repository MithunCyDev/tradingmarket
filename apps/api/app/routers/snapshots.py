from fastapi import APIRouter, HTTPException, Request

from app.container import AppContainer
from app.schemas.common import SymbolId
from app.schemas.snapshot import MarketSnapshot
from app.services.instrument_catalog import UnknownInstrumentError

router = APIRouter(tags=["snapshots"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


def _resolve_symbol(request: Request, symbol: str) -> SymbolId:
    try:
        return _container(request).catalog.resolve(symbol)
    except UnknownInstrumentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/snapshots/{symbol}")
def get_snapshot(symbol: str, request: Request) -> MarketSnapshot:
    resolved = _resolve_symbol(request, symbol)
    snapshot = _container(request).snapshot_service.get(resolved)
    if snapshot is None:
        raise HTTPException(status_code=404, detail=f"No snapshot yet for {resolved}")
    return snapshot
