#!/usr/bin/env python3
"""Export current Python rule constants into versioned JSON catalogs."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from combat.catalog import CATALOG_ROOT, CATALOG_VERSION, to_catalog_entry
from combat.feats import AVALORE_FEATS
from combat.items import AVALORE_ARMOR, AVALORE_SHIELDS, AVALORE_WEAPONS
from combat.spells import AVALORE_SPELLS


def write_catalog(name: str, entries: list[dict]) -> None:
    CATALOG_ROOT.mkdir(parents=True, exist_ok=True)
    path = CATALOG_ROOT / f"{name}.json"
    payload = {
        "version": CATALOG_VERSION,
        "kind": name,
        "entries": entries,
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> None:
    write_catalog("weapons", [to_catalog_entry(item) for item in AVALORE_WEAPONS.values()])
    write_catalog("armor", [to_catalog_entry(item) for item in AVALORE_ARMOR.values()])
    write_catalog("shields", [to_catalog_entry(item) for item in AVALORE_SHIELDS.values()])
    write_catalog("feats", [to_catalog_entry(item) for item in AVALORE_FEATS.values()])
    write_catalog("spells", [to_catalog_entry(item) for item in AVALORE_SPELLS.values()])


if __name__ == "__main__":
    main()
