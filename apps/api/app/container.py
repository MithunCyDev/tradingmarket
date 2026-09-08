from dataclasses import dataclass

from app.config import Settings
from app.repositories.json_store import JsonFileStore
from app.services.instrument_catalog import InstrumentCatalog
from app.services.analysis_service import AnalysisService
from app.services.chart_service import ChartService
from app.services.live_quotes import HttpLiveQuotes
from app.services.market_data import MarketDataPort, YahooMarketData
from app.services.quote_service import QuoteService
from app.services.signal_store import SignalStore
from app.services.snapshot_service import SnapshotService
from app.services.snapshot_store import SnapshotStore


@dataclass(frozen=True)
class AppContainer:
    settings: Settings
    catalog: InstrumentCatalog
    signal_store: SignalStore
    snapshot_store: SnapshotStore
    quote_service: QuoteService
    snapshot_service: SnapshotService
    analysis_service: AnalysisService
    chart_service: ChartService


def build_container(
    settings: Settings,
    market_data: MarketDataPort | None = None,
    live_quotes: HttpLiveQuotes | None = None,
) -> AppContainer:
    vendor = market_data or YahooMarketData()
    live = live_quotes
    if market_data is None and live is None:
        live = HttpLiveQuotes()
    catalog = InstrumentCatalog(settings.resolved_catalog_path())
    signal_store = SignalStore(
        JsonFileStore(settings.signals_dir()),
        JsonFileStore(settings.scalp_signals_dir()),
    )
    snapshot_store = SnapshotStore(JsonFileStore(settings.snapshots_dir()))
    return AppContainer(
        settings=settings,
        catalog=catalog,
        signal_store=signal_store,
        snapshot_store=snapshot_store,
        quote_service=QuoteService(
            catalog,
            vendor,
            settings.quote_cache_seconds,
            live_quotes=live,
        ),
        snapshot_service=SnapshotService(catalog, vendor, snapshot_store),
        analysis_service=AnalysisService(signal_store, snapshot_store),
        chart_service=ChartService(catalog, vendor),
    )
