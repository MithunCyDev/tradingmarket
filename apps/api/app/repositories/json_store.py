import json
from pathlib import Path
from typing import Any


class JsonFileStore:
    """Atomic JSON file store keyed by an allowlisted symbol."""

    def __init__(self, directory: Path) -> None:
        self._directory = directory
        self._directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, symbol: str) -> Path:
        if "/" in symbol or "\\" in symbol or ".." in symbol:
            raise ValueError("Invalid symbol path")
        return self._directory / f"{symbol}.json"

    def read(self, symbol: str) -> dict[str, Any] | None:
        path = self.path_for(symbol)
        if not path.exists():
            return None
        return json.loads(path.read_text(encoding="utf-8"))

    def write(self, symbol: str, payload: dict[str, Any]) -> Path:
        path = self.path_for(symbol)
        temporary = path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
        return path
