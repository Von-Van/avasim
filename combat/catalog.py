"""Versioned JSON catalog helpers for static Avalore rule data."""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, is_dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict


CATALOG_VERSION = "1.0.0"


def _catalog_root() -> Path:
    """Locate data/avalore/v1 both in a checkout and a frozen (PyInstaller) app."""
    if getattr(sys, "frozen", False):
        bundle_root = Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
        return bundle_root / "data" / "avalore" / "v1"
    return Path(__file__).resolve().parent.parent / "data" / "avalore" / "v1"


CATALOG_ROOT = _catalog_root()


def _json_ready(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {key: _json_ready(item) for key, item in asdict(value).items()}
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_ready(item) for item in value]
    return value


def to_catalog_entry(value: Any) -> Dict[str, Any]:
    entry = _json_ready(value)
    if not isinstance(entry, dict):
        raise TypeError(f"Catalog entries must serialize to objects, got {type(entry)!r}.")
    return entry


def load_catalog(name: str) -> Dict[str, Any]:
    path = CATALOG_ROOT / f"{name}.json"
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        data = json.load(handle)
    if data.get("version") != CATALOG_VERSION:
        raise ValueError(
            f"Unsupported {name} catalog version {data.get('version')!r}; "
            f"expected {CATALOG_VERSION!r}."
        )
    return data
