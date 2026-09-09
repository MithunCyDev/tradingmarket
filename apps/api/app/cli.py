from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import Settings
from app.container import build_container
from app.schemas.common import SignalStyle
from app.schemas.signal import SignalTicket
from app.services.analysis_chart import (
    artifact_filename,
    publish_chart_artifact,
    render_analysis_chart,
)
from app.services.analysis_service import levels_from_ticket
from app.services.instrument_catalog import UnknownInstrumentError
from app.services.market_data import MarketDataError


def _container(data_dir: Path | None = None):
    settings = Settings(data_dir=data_dir) if data_dir is not None else Settings()
    return build_container(settings)


def run_snapshot(raw_symbol: str, data_dir: Path | None = None) -> int:
    container = _container(data_dir)
    try:
        symbol = container.catalog.resolve(raw_symbol)
    except UnknownInstrumentError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    snapshot = container.snapshot_service.capture(symbol)
    path = container.settings.snapshots_dir() / f"{symbol}.json"
    print(json.dumps(snapshot.model_dump(mode="json", by_alias=True), indent=2))
    print(f"Wrote {path}", file=sys.stderr)
    if snapshot.error:
        print(f"Snapshot error: {snapshot.error}", file=sys.stderr)
        return 1
    return 0


def check_signal(
    raw_symbol: str,
    data_dir: Path | None = None,
    style: SignalStyle = "swing",
) -> int:
    container = _container(data_dir)
    try:
        symbol = container.catalog.resolve(raw_symbol)
    except UnknownInstrumentError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    ticket = container.signal_store.read(symbol, style)
    if ticket is None:
        print(f"No signal file for {symbol}", file=sys.stderr)
        return 1
    SignalTicket.model_validate(ticket.model_dump())
    print(json.dumps(ticket.model_dump(mode="json", by_alias=True), indent=2))
    return 0


def run_chart(
    raw_symbol: str,
    data_dir: Path | None = None,
    style: SignalStyle = "swing",
) -> int:
    container = _container(data_dir)
    try:
        symbol = container.catalog.resolve(raw_symbol)
    except UnknownInstrumentError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    instrument = container.catalog.get(symbol)
    ticket = container.signal_store.read(symbol, style)
    if ticket is None:
        print(f"No signal file for {symbol}", file=sys.stderr)
        return 1

    try:
        chart = container.chart_service.get(symbol, ticket.timeframe)
    except MarketDataError as exc:
        print(f"Could not load OHLC for {symbol}: {exc}", file=sys.stderr)
        return 1
    if not chart.bars:
        print(f"No OHLC bars for {symbol} {ticket.timeframe}", file=sys.stderr)
        return 1

    snapshot = container.snapshot_store.read(symbol)
    last_price = snapshot.last_price if snapshot is not None else chart.bars[-1].close
    output_path = container.settings.charts_dir(style) / f"{symbol}.png"
    render_analysis_chart(
        chart,
        ticket,
        levels_from_ticket(ticket),
        last_price,
        instrument.price_decimals,
        output_path,
        instrument.yahoo_symbol,
        instrument.label,
    )
    print(f"Wrote {output_path}", file=sys.stderr)

    published = publish_chart_artifact(output_path, artifact_filename(ticket))
    if published is not None:
        print(f"ARTIFACT {published}", file=sys.stderr)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Elite Forex snapshot and signal tools")
    parser.add_argument("--data-dir", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="Fetch Yahoo OHLC and write a technical snapshot")
    snapshot.add_argument("symbol", help="GOLD, BTC, SILVER, US OIL, EUR/USD, or the desk id")

    check = sub.add_parser("check-signal", help="Validate the latest signal JSON for a symbol")
    check.add_argument("symbol")
    check.add_argument("--style", choices=("swing", "scalp"), default="swing")

    chart = sub.add_parser("chart", help="Render a marked analysis PNG from the latest ticket")
    chart.add_argument("symbol")
    chart.add_argument("--style", choices=("swing", "scalp"), default="swing")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        return run_snapshot(args.symbol, args.data_dir)
    if args.command == "check-signal":
        return check_signal(args.symbol, args.data_dir, args.style)
    if args.command == "chart":
        return run_chart(args.symbol, args.data_dir, args.style)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
