from fastapi import APIRouter, HTTPException, Query, Request

from app.container import AppContainer
from app.schemas.analysis import AnalysisResponse
from app.schemas.common import SignalStyle, SymbolId
from app.services.analysis_service import AnalysisNotFoundError
from app.services.instrument_catalog import UnknownInstrumentError

router = APIRouter(tags=["analysis"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


def _resolve_symbol(request: Request, symbol: str) -> SymbolId:
    try:
        return _container(request).catalog.resolve(symbol)
    except UnknownInstrumentError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/analysis/{symbol}")
def get_analysis(
    symbol: str,
    request: Request,
    style: SignalStyle = Query(default="swing"),
) -> AnalysisResponse:
    resolved = _resolve_symbol(request, symbol)
    try:
        return _container(request).analysis_service.get(resolved, style)
    except AnalysisNotFoundError as exc:
        raise HTTPException(status_code=404, detail=f"No signal yet for {resolved}") from exc
