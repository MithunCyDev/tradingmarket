from collections.abc import Callable
from datetime import UTC, datetime, timedelta

from app.schemas.instrument import Instrument
from app.schemas.quote import Quote
from app.services.instrument_catalog import InstrumentCatalog
from app.services.live_quotes import HttpLiveQuotes
from app.services.market_data import MarketDataError, MarketDataPort, RawQuote
from app.services.market_hours import is_market_open, status_label


class QuoteService:
    def __init__(
        self,
        catalog: InstrumentCatalog,
        market_data: MarketDataPort,
        cache_seconds: int,
        clock: Callable[[], datetime] | None = None,
        live_quotes: HttpLiveQuotes | None = None,
    ) -> None:
        self._catalog = catalog
        self._market_data = market_data
        self._cache_seconds = cache_seconds
        self._clock = clock or (lambda: datetime.now(UTC))
        self._live_quotes = live_quotes
        self._cached: list[Quote] | None = None
        self._cached_at: datetime | None = None

    def list_quotes(self) -> list[Quote]:
        now = self._clock()
        if (
            self._cached is not None
            and self._cached_at is not None
            and now - self._cached_at < timedelta(seconds=self._cache_seconds)
        ):
            return self._cached

        quotes = [self._quote_one(instrument, now) for instrument in self._catalog.all()]
        self._cached = quotes
        self._cached_at = now
        return quotes

    def _quote_one(self, instrument: Instrument, now: datetime) -> Quote:
        raw: RawQuote | None = None
        source = "yahoo"
        if self._live_quotes is not None:
            try:
                raw, source = self._live_quotes.quote(instrument)
            except MarketDataError:
                raw = None
        if raw is None:
            try:
                raw = self._market_data.quote(instrument.yahoo_symbol)
                source = "yahoo"
            except MarketDataError:
                raw = None

        open_now = is_market_open(instrument.market_kind, now)
        label = status_label(instrument.market_kind, now, source)
        change = None if raw is None else round(raw.last - raw.previous_close, 6)
        change_percent = None
        if raw is not None and raw.previous_close != 0:
            change_percent = round((change or 0) / raw.previous_close * 100, 4)

        return Quote(
            symbol=instrument.id,
            last=None if raw is None else raw.last,
            change=change,
            change_percent=change_percent,
            as_of=now if raw is None else raw.as_of,
            delayed=label != "LIVE",
            market_state="open" if open_now else "closed",
            status_label=label,
            source=source if raw is not None else "none",
        )
