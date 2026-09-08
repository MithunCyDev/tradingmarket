from fastapi import APIRouter, Request

from app.container import AppContainer
from app.schemas.quote import QuoteListResponse

router = APIRouter(tags=["quotes"])


def _container(request: Request) -> AppContainer:
    return request.app.state.container


@router.get("/quotes")
def list_quotes(request: Request) -> QuoteListResponse:
    return QuoteListResponse(data=_container(request).quote_service.list_quotes())
