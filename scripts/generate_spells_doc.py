#!/usr/bin/env python3
"""Render docs/spells_catalog.md from the runtime spell catalog.

The catalog itself (combat/spells.py) is the source of truth; this script just
formats it for human reading, mirroring docs/feats_catalog.md.

Usage::

    python scripts/generate_spells_doc.py > docs/spells_catalog.md
"""

from __future__ import annotations

import sys
from collections import OrderedDict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from combat.spells import AVALORE_SPELLS, OPPOSED_DISCIPLINES

TIER_ORDER = {"cantrip": 0, "2": 1, "4": 2, "6": 3, "10": 4, "capstone": 5}
GROUPS = ["Cantrips", "Ichor", "Cursesmithy", "Ether", "Artifice", "Force", "Tellurgy"]


def main() -> None:
    grouped: "OrderedDict[str, list]" = OrderedDict((g, []) for g in GROUPS)
    for spell in AVALORE_SPELLS.values():
        group = spell.discipline or "Cantrips"
        grouped[group].append(spell)
    for group in grouped:
        grouped[group].sort(key=lambda s: (TIER_ORDER.get(s.tier, 9), s.section, s.name))

    total = len(AVALORE_SPELLS)
    wired = sum(1 for s in AVALORE_SPELLS.values() if s.engine_wired)

    print("# Avalore Spell Catalog")
    print()
    print(f"Every spell published in the Avalore Grimoire ({total} total:")
    print("<https://avalore.net/grimoire/> plus the six per-discipline pages).")
    print("This document is generated from the runtime catalog in")
    print("[`combat/spells.py`](../combat/spells.py); the scraped source of truth")
    print("lives in `tests/data/avalore_spells_source.json`.")
    print()
    print("Regenerate the source with `python scripts/fetch_spells.py --emit json`,")
    print("the Python catalog with `python scripts/fetch_spells.py --emit python`,")
    print("and this document with `python scripts/generate_spells_doc.py`.")
    print()
    print("**Status legend**")
    print()
    print("- ⚙ **Engine-wired** — the spell has simulated combat mechanics")
    print("  (hand-authored in `SPELL_MECHANICS`); simplifications are noted there")
    print("  and in [mechanics_reference.md](mechanics_reference.md).")
    print("- 📋 **Cataloged** — faithful text and costs, but the effect is")
    print("  out-of-combat, narrative, or scene-control magic the simulator does")
    print("  not model.")
    print()
    print("Casting rules (DC 10, anima, miscasts, overcasting, the magic wheel)")
    print("are implemented in `engine.perform_cast_spell`; see the Spellcasting")
    print("section of [mechanics_reference.md](mechanics_reference.md).")
    print()
    print("| Group | Spells | Engine-wired |")
    print("|-------|-------:|-------------:|")
    for group, spells in grouped.items():
        wired_count = sum(1 for s in spells if s.engine_wired)
        print(f"| {group} | {len(spells)} | {wired_count} |")
    print(f"| **Total** | **{total}** | **{wired}** |")
    print()

    for group, spells in grouped.items():
        print()
        print(f"## {group}")
        if group in OPPOSED_DISCIPLINES:
            print()
            print(f"_Magic-wheel opposite: **{OPPOSED_DISCIPLINES[group]}**_")
        current_section = None
        for spell in spells:
            if spell.section != current_section:
                current_section = spell.section
                print()
                print(f"### {current_section}")
            print()
            badge = "⚙" if spell.engine_wired else "📋"
            tags = []
            if spell.targeted:
                tags.append("Targeted")
            if spell.recast_daily:
                tags.append("Recasts daily")
            tag_str = f" _({', '.join(tags)})_" if tags else ""
            req = "" if spell.requires.lower().startswith("no requirement") else f" — _{spell.requires}_"
            print(f"#### {badge} {spell.name}{tag_str}{req}")
            print()
            print(f"`{spell.anima_cost} anima · {spell.actions_required} action(s) · {spell.cast_command}`")
            print()
            print(spell.description)
            if spell.method:
                print()
                print(f"**Method:** {spell.method}")


if __name__ == "__main__":
    main()
