from fastapi import APIRouter, HTTPException, Query, Request

from app.container import AppContainer
from app.schemas.analysis import ChartResponse
from app.schemas.common import TIMEFRAMES, SymbolId, Timeframe
from app.services.instrument_catalog import UnknownInstrumentError
from app.services.market_data import MarketDataError

router = APIRouter(tags=["charts"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


def _resolve_symbol(request: Request, symbol: str) -> SymbolId:
    try:
        return _container(request).catalog.resolve(symbol)
    except UnknownInstrumentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/charts/{symbol}")
def get_chart(
    symbol: str,
    request: Request,
    timeframe: Timeframe = Query(default="H1"),
) -> ChartResponse:
    resolved = _resolve_symbol(request, symbol)
    if timeframe not in TIMEFRAMES:
        raise HTTPException(status_code=422, detail="Unsupported timeframe")
    typed: Timeframe = timeframe
    try:
        return _container(request).chart_service.get(resolved, typed)
    except MarketDataError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
