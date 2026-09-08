from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.config import Settings
from app.container import build_container
from app.schemas.common import SignalStyle
from app.schemas.signal import SignalTicket
from app.services.instrument_catalog import UnknownInstrumentError


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


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Elite Forex snapshot and signal tools")
    parser.add_argument("--data-dir", type=Path, default=None)
    sub = parser.add_subparsers(dest="command", required=True)

    snapshot = sub.add_parser("snapshot", help="Fetch Yahoo OHLC and write a technical snapshot")
    snapshot.add_argument("symbol", help="GOLD, BTC, SILVER, US OIL, EUR/USD, or the desk id")

    check = sub.add_parser("check-signal", help="Validate the latest signal JSON for a symbol")
    check.add_argument("symbol")
    check.add_argument("--style", choices=("swing", "scalp"), default="swing")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "snapshot":
        return run_snapshot(args.symbol, args.data_dir)
    if args.command == "check-signal":
        return check_signal(args.symbol, args.data_dir, args.style)
    raise AssertionError(f"Unhandled command: {args.command}")


if __name__ == "__main__":
    raise SystemExit(main())
