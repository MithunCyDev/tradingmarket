from fastapi import APIRouter, Request

from app.container import AppContainer
from app.schemas.instrument import InstrumentListResponse

router = APIRouter(tags=["instruments"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


@router.get("/instruments")
def list_instruments(request: Request) -> InstrumentListResponse:
    return InstrumentListResponse(data=_container(request).catalog.all())
