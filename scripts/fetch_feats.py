#!/usr/bin/env python3
"""Scrape the authoritative Avalore feat list and emit structured data.

The live feats page at https://avalore.net/feats loads its content from
``/custom_pages/feats.html`` and blocks default User-Agents, so a browser UA is
required. This script parses that page into structured feat records and can emit
either the JSON parity fixture used by the test-suite or the Python ``Feat``
literal used by :mod:`combat.feats`.

Usage::

    python scripts/fetch_feats.py --emit json    > tests/fixtures/avalore_feats_source.json
    python scripts/fetch_feats.py --emit python   # prints the AVALORE_FEATS literal

Pass ``--from-file PATH`` to parse a cached copy of the include HTML instead of
fetching it (useful offline / in CI).
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.request

FEATS_URL = "https://avalore.net/custom_pages/feats.html"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

STAT_ABBR = {"DEX": "Dexterity", "INT": "Intelligence", "HAR": "Harmony", "STR": "Strength"}
# Section heading text -> (category, archetype).
SECTION_META = {
    "Combat": ("Combat", ""),
    "Lineage Weapon": ("Lineage Weapon", ""),
    "Mutation": ("Mutation", "Mutant"),
    "Vampiric": ("Vampiric", "Vampire"),
    "Utility": ("Utility", ""),
    "Backgrounds": ("Backgrounds", ""),
}

_CUTOUT = re.compile(
    r'<div class="cutout-header">(?P<name>.*?)</div>'
    r'(?P<body>.*?)'
    r'<div class="cutout-footer">(?P<req>.*?)</div>',
    re.S,
)
_H3 = re.compile(r'<h3[^>]*>(?P<title>.*?)</h3>', re.S)


def _clean(text: str) -> str:
    # Replace tags with a space so block boundaries (</p>, <br>) don't fuse
    # adjacent sentences, then collapse the resulting whitespace.
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_html() -> str:
    req = urllib.request.Request(FEATS_URL, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted URL)
        return resp.read().decode("utf-8", "replace")


def parse_requirements(raw: str):
    """Map a "Requires ..." string to (stat_requirements, archetype).

    Examples::

        "No requirement."                         -> ({}, "")
        "Requires DEX: Stealth +2"                -> ({"Dexterity:Stealth": 2}, "")
        "Requires STR +1 and Shield Bash feat"    -> ({"Strength": 1, "Shield Bash": 1}, "")
        "Requires Lineage Weapon feat and Vampire trait"
                                                  -> ({"Lineage Weapon": 1}, "Vampire")
    """
    reqs: dict = {}
    archetype = ""
    raw = raw.strip()
    raw = re.sub(r"^Requires\s+", "", raw)
    if not raw or raw.lower().startswith("no requirement"):
        return reqs, archetype
    for clause in re.split(r"\s+and\s+", raw):
        clause = clause.strip().rstrip(".")
        if not clause:
            continue
        if clause.endswith("trait"):
            archetype = clause[: -len("trait")].strip()
            continue
        if clause.endswith("feat"):
            reqs[clause[: -len("feat")].strip()] = 1
            continue
        m = re.match(r"(?P<stat>DEX|INT|HAR|STR)(?:\s*:\s*(?P<skill>[A-Za-z]+))?\s*(?P<val>[+-]?\d+)", clause)
        if not m:
            continue
        stat = STAT_ABBR[m.group("stat")]
        key = f"{stat}:{m.group('skill')}" if m.group("skill") else stat
        reqs[key] = int(m.group("val"))
    return reqs, archetype


def parse_feats(page: str):
    feats = []
    # Index of section headings so each cutout can be attributed to a section.
    headings = [(m.start(), _clean(m.group("title"))) for m in _H3.finditer(page)]

    def section_for(pos: int) -> str:
        name = ""
        for start, title in headings:
            if start <= pos:
                name = title
            else:
                break
        return name

    for m in _CUTOUT.finditer(page):
        section = section_for(m.start())
        category, archetype = SECTION_META.get(section, (section, ""))
        name = _clean(m.group("name"))
        body = m.group("body")
        limited = "<em>Limited</em>" in body or "<em> Limited" in body
        effect = _clean(body)
        effect = re.sub(r"^Limited\s*", "", effect)
        effect = re.sub(r"^\**\s*Effect:\s*", "", effect).strip()
        req_raw = _clean(m.group("req"))
        reqs, trait_arch = parse_requirements(req_raw)
        feats.append({
            "name": name,
            "section": section,
            "category": category,
            "archetype": trait_arch or archetype,
            "limited": limited,
            "requires": req_raw,
            "stat_requirements": reqs,
            "effect": effect,
        })
    return feats


def emit_python(feats) -> str:
    lines = ["AVALORE_FEATS = {"]
    for f in feats:
        parts = [
            f"name={f['name']!r}",
            f"description={f['effect']!r}",
            f"stat_requirements={f['stat_requirements']!r}",
            f"category={f['category']!r}",
        ]
        if f["archetype"]:
            parts.append(f"archetype={f['archetype']!r}")
        if f["limited"]:
            parts.append("limited=True")
        lines.append(f"    {f['name']!r}: Feat({', '.join(parts)}),")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", choices=["json", "python"], default="json")
    ap.add_argument("--from-file", help="Parse a cached copy instead of fetching.")
    args = ap.parse_args()

    page = open(args.from_file, encoding="utf-8").read() if args.from_file else fetch_html()
    feats = parse_feats(page)
    if len(feats) < 90:
        print(f"WARNING: only parsed {len(feats)} feats; page format may have changed.", file=sys.stderr)

    if args.emit == "python":
        print(emit_python(feats))
    else:
        source = [
            {"name": f["name"], "section": f["section"], "limited": f["limited"],
             "requires": f["requires"], "effect": f["effect"]}
            for f in feats
        ]
        json.dump(source, sys.stdout, indent=2, ensure_ascii=False)
        sys.stdout.write("\n")


if __name__ == "__main__":
    main()
