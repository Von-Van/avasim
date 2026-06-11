#!/usr/bin/env python3
"""Scrape the authoritative Avalore grimoire and emit structured spell data.

The grimoire is split across seven live pages that block default User-Agents,
so a browser UA is required:

- https://avalore.net/grimoire/        (general + patron cantrips)
- https://avalore.net/<discipline>-spells/  for ichor, cursesmithy, ether,
  artifice, force, tellurgy (inherent cantrip, 2/4/6/10 anima tiers, capstone)

Each spell is a "cutout" card: name header, optional ``<em>`` tag line
(``Targeted`` / ``Recasts daily until cancelled``), an **Effect:** paragraph,
a **Method:** paragraph, an info table (anima cost, action count, ``/cast``
command), and a requirement footer.

Usage::

    python scripts/fetch_spells.py --emit json > tests/data/avalore_spells_source.json
    python scripts/fetch_spells.py --emit python   # prints the AVALORE_SPELLS literal
    python scripts/fetch_spells.py --cache-dir /tmp/grimoire --emit json

Pass ``--cache-dir PATH`` to reuse saved copies of the pages (useful offline /
in CI); missing pages are fetched and saved there.
"""

from __future__ import annotations

import argparse
import html
import json
import pathlib
import re
import sys
import urllib.request

BASE = "https://avalore.net"
_UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

# page slug -> discipline ("" = the shared cantrip page)
PAGES = {
    "grimoire": "",
    "ichor-spells": "Ichor",
    "cursesmithy-spells": "Cursesmithy",
    "ether-spells": "Ether",
    "artifice-spells": "Artifice",
    "force-spells": "Force",
    "tellurgy-spells": "Tellurgy",
}

STAT_ABBR = {"DEX": "Dexterity", "INT": "Intelligence", "HAR": "Harmony", "STR": "Strength"}

_CUTOUT = re.compile(
    r'<div class="cutout-header">(?P<name>.*?)</div>'
    r'(?P<body>.*?)'
    r'<div class="cutout-footer">(?P<req>.*?)</div>',
    re.S,
)
_H4 = re.compile(r'<h4[^>]*>(?P<title>.*?)</h4>', re.S)
_TAGLINE = re.compile(r'^\s*<p[^>]*>\s*<em>(?P<tags>.*?)</em>\s*</p>', re.S)
_EFFECT = re.compile(r'<strong>\s*Effect:\s*</strong>(?P<text>.*?)</p>', re.S)
_METHOD = re.compile(r'<strong>\s*Method:\s*</strong>(?P<text>.*?)</p>', re.S)
_ANIMA = re.compile(r'fa-bolt-lightning"></i>\s*(?:Cantrip \((?P<cantrip>\d+) anima\)|(?P<cost>\d+) anima)')
_ACTIONS = re.compile(r'fa-clock"></i>\s*(?P<n>\d+) actions?')
_CMD = re.compile(r'<span class="cmdspan">(?P<cmd>.*?)</span>', re.S)


def _clean(text: str) -> str:
    # Replace tags with a space so block boundaries (</p>, <br>) don't fuse
    # adjacent sentences, then collapse the resulting whitespace.
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def fetch_html(slug: str, cache_dir: str | None) -> str:
    if cache_dir:
        cached = pathlib.Path(cache_dir) / f"{slug}.html"
        if cached.exists():
            return cached.read_text(encoding="utf-8")
    url = f"{BASE}/{'grimoire' if slug == 'grimoire' else slug}/"
    req = urllib.request.Request(url, headers={"User-Agent": _UA})
    with urllib.request.urlopen(req, timeout=30) as resp:  # noqa: S310 (trusted URL)
        page = resp.read().decode("utf-8", "replace")
    if cache_dir:
        path = pathlib.Path(cache_dir)
        path.mkdir(parents=True, exist_ok=True)
        (path / f"{slug}.html").write_text(page, encoding="utf-8")
    return page


def parse_requirements(raw: str):
    """Map a "Requires ..." string to stat requirements (same as fetch_feats)."""
    reqs: dict = {}
    raw = raw.strip()
    raw = re.sub(r"^Requires\s+", "", raw)
    if not raw or raw.lower().startswith("no requirement"):
        return reqs
    for clause in re.split(r"\s+and\s+", raw):
        clause = clause.strip().rstrip(".")
        if not clause:
            continue
        m = re.match(r"(?P<stat>DEX|INT|HAR|STR)(?:\s*:\s*(?P<skill>[A-Za-z]+))?\s*(?P<val>[+-]?\d+)", clause)
        if not m:
            continue
        stat = STAT_ABBR[m.group("stat")]
        key = f"{stat}:{m.group('skill')}" if m.group("skill") else stat
        reqs[key] = int(m.group("val"))
    return reqs


def _tier_for(section: str) -> str:
    s = section.lower()
    if "cantrip" in s:
        return "cantrip"
    if "capstone" in s:
        return "capstone"
    m = re.match(r"(\d+) anima", s)
    return m.group(1) if m else s


def parse_spells(page: str, discipline: str):
    spells = []
    headings = [(m.start(), _clean(m.group("title"))) for m in _H4.finditer(page)]

    def section_for(pos: int) -> str:
        name = ""
        for start, title in headings:
            if start <= pos:
                name = title
            else:
                break
        # strip the "(N spells)" suffix
        return re.sub(r"\s*\(\d+ spells?\)\s*$", "", name)

    for m in _CUTOUT.finditer(page):
        section = section_for(m.start())
        body = m.group("body")

        tags = ""
        tag_m = _TAGLINE.match(body)
        if tag_m:
            tags = _clean(tag_m.group("tags"))
        effect_m = _EFFECT.search(body)
        method_m = _METHOD.search(body)
        anima_m = _ANIMA.search(body)
        actions_m = _ACTIONS.search(body)
        cmd_m = _CMD.search(body)
        name = _clean(m.group("name"))
        if not (effect_m and anima_m and actions_m):
            print(f"WARNING: skipped malformed cutout {name!r}", file=sys.stderr)
            continue

        req_raw = _clean(m.group("req"))
        spells.append({
            "name": name,
            "discipline": discipline,
            "section": section,
            "tier": _tier_for(section),
            "anima_cost": int(anima_m.group("cantrip") or anima_m.group("cost")),
            "actions_required": int(actions_m.group("n")),
            "cast_command": _clean(cmd_m.group("cmd")) if cmd_m else "",
            "targeted": "Targeted" in tags,
            "recast_daily": "Recasts daily" in tags,
            "effect": _clean(effect_m.group("text")),
            "method": _clean(method_m.group("text")) if method_m else "",
            "requires": req_raw,
            "stat_requirements": parse_requirements(req_raw),
        })
    return spells


def emit_python(spells) -> str:
    lines = ["AVALORE_SPELLS: Dict[str, Spell] = {"]
    for s in spells:
        parts = [
            f"name={s['name']!r}",
            f"discipline={s['discipline']!r}",
            f"tier={s['tier']!r}",
            f"section={s['section']!r}",
            f"anima_cost={s['anima_cost']!r}",
            f"actions_required={s['actions_required']!r}",
            f"cast_command={s['cast_command']!r}",
        ]
        if s["targeted"]:
            parts.append("targeted=True")
        if s["recast_daily"]:
            parts.append("recast_daily=True")
        parts.append(f"description={s['effect']!r}")
        parts.append(f"method={s['method']!r}")
        parts.append(f"requires={s['requires']!r}")
        if s["stat_requirements"]:
            parts.append(f"stat_requirements={s['stat_requirements']!r}")
        lines.append(f"    {s['name']!r}: Spell({', '.join(parts)}),")
    lines.append("}")
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--emit", choices=["json", "python"], default="json")
    ap.add_argument("--cache-dir", help="Reuse/saved page copies instead of always fetching.")
    args = ap.parse_args()

    spells = []
    for slug, discipline in PAGES.items():
        spells.extend(parse_spells(fetch_html(slug, args.cache_dir), discipline))

    if len(spells) < 200:
        print(f"WARNING: only parsed {len(spells)} spells; page format may have changed.", file=sys.stderr)

    if args.emit == "python":
        print(emit_python(spells))
        return
    json.dump(spells, sys.stdout, indent=2, ensure_ascii=False)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
