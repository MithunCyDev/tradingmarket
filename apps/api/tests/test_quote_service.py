from datetime import UTC, datetime
from app.config import REPO_ROOT
from app.services.instrument_catalog import InstrumentCatalog
from app.services.market_data import MarketDataError, RawQuote
from app.services.quote_service import QuoteService


class PartialMarketData:
    def history(self, yahoo_symbol: str, interval: str, period: str):
        raise MarketDataError("unused")

    def quote(self, yahoo_symbol: str) -> RawQuote:
        if yahoo_symbol == "PAXG-USD":
            raise MarketDataError("gold down")
        return RawQuote(last=100.0, previous_close=99.0, as_of=datetime(2026, 9, 9, 12, 0, tzinfo=UTC))


def test_quotes_survive_a_single_vendor_failure() -> None:
    catalog = InstrumentCatalog(REPO_ROOT / "config" / "instruments.json")
    service = QuoteService(
        catalog,
        PartialMarketData(),
        cache_seconds=60,
        clock=lambda: datetime(2026, 9, 9, 16, 0, tzinfo=UTC),
    )

    quotes = service.list_quotes()
    by_symbol = {item.symbol: item for item in quotes}

    assert len(quotes) == 5
    assert by_symbol["XAUUSD"].last is None
    assert by_symbol["BTCUSD"].last == 100.0
    assert by_symbol["BTCUSD"].market_state in {"open", "closed"}
