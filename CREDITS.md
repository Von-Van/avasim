# Credits & Attribution

AvaSim is an **unofficial, fan-made combat simulator** for the
[Avalore](https://avalore.net) tabletop RPG. All game rules, mechanics,
items, feats, spells, lore, place names, and setting material belong to the
**Avalore team and community**. AvaSim models those rules for combat
analysis and build experimentation; it is not affiliated with or endorsed by
the Avalore staff. If you enjoy this simulator, go play on the real thing.

## Rules & Mechanics

The combat engine and its data catalogs are built directly from the rules
published on avalore.net. Effect text in the catalogs is reproduced verbatim
from these pages so the simulator stays faithful to canon:

| Page | URL | Used for |
|------|-----|----------|
| Core Mechanics | <https://avalore.net/mechanics> | Action economy, tests (2d10/DC 12), attacks, evasion, blocking, criticals, grazes, health/death/bleedout, improvised equipment, non-proficiency |
| Extended Mechanics | <https://avalore.net/extended-mechanics> | Maneuvers (Grapple, Disarm, Struggle, Shove, Topple, Pull), Prone/Grappled conditions, stealth, light & darkness, environmental rules |
| Weapons | <https://avalore.net/weapons> | The full weapon roster: damage, aim, actions, range bands, traits |
| Armour | <https://avalore.net/armour> | Armor classes, soak, penalties, shields |
| Feats | <https://avalore.net/feats> | All 100 feats (see [docs/feats_catalog.md](docs/feats_catalog.md)) |
| Fabled Feats | <https://avalore.net/fabled-feats> | Fable feat system (cataloged context) |
| Arcane | <https://avalore.net/arcane> | Spellcasting & anima, casting/miscasting, overcasting, patrons & mage progression, the magic wheel |
| The Grimoire | <https://avalore.net/grimoire> | All cantrips; index of the six disciplines (see [docs/spells_catalog.md](docs/spells_catalog.md)) |
| — Ichor Spells | <https://avalore.net/ichor-spells> | All 32 Ichor spells |
| — Cursesmithy Spells | <https://avalore.net/cursesmithy-spells> | All 32 Cursesmithy spells |
| — Ether Spells | <https://avalore.net/ether-spells> | All 32 Ether spells |
| — Artifice Spells | <https://avalore.net/artifice-spells> | All 32 Artifice spells |
| — Force Spells | <https://avalore.net/force-spells> | All 32 Force spells |
| — Tellurgy Spells | <https://avalore.net/tellurgy-spells> | All 32 Tellurgy spells |
| Vampirism | <https://avalore.net/vampirism> | Vampire trait context for the Vampiric feat category |
| Crafting | <https://avalore.net/crafting> | Crafting system (not yet modelled) |

## World Compendium

The [Avalore Compendium](https://avalore.net/compendium/) provides the world
that gives these rules meaning — the races and traits behind archetypes, the
creatures behind creature types, and the lore behind the items and feats.
Its sections and entries:

**Races of the World** — Human, Arsa Sidhe, Greatling, Fey-Touched,
Void-Touched, Half-Races

**Factions of the World** — Valkian Realm, Fallstone, Duchy of Rulan,
Great Clans of Ko'ram, Serene Monarchy

**Cultures of the World** — Valks, Walljacks, Falstoner, Aedall, Korami,
Mistan, Stonerunner, Fireborne, The Pearl Coast

**Notable Places** — Southern Reach, The Spire, Midlands, Faded Steppe,
The Wall, Ashlands, The North, Mist Isles, Albern Crossing, Ko'ram,
Ynsyoedd Eryri, The Pearl Coast, Sanguifleur, Sudvalkia, The Amafells

**Fables** — Overview, Lady Luck, Spirit of the Fire Dragon, Lady of the
Lake, The Portents, Shrinekeepers, Siren Serene, Equinox & Phoenix,
Divine Gardeners

**Bestiary** — Overview, Guide to the Fey, Common Types of Fey, Beasts of
the Realm, Necrophages, Beast DM'ing Guide, Apparitions

**History** — The Collapse, The Great Disappearance, Sanguifleur,
The Long Winter

**Miscellaneous** — Standard Calendar, Currency, Constellations & The
Zodiac, The Sun & Moons, The Storyteller & Revival, Divining Cards,
Flora & Fauna Beyond the Reach, Illness & Diseases

## Tooling

- [Python](https://www.python.org/) — engine, analysis core, and tests
- [PySide6 / Qt](https://www.qt.io/qt-for-python) — desktop UI
- [PyInstaller](https://pyinstaller.org/) — desktop packaging
- Optional UI fonts: [Cinzel](https://fonts.google.com/specimen/Cinzel),
  [Crimson Text](https://fonts.google.com/specimen/Crimson+Text),
  [Spectral](https://fonts.google.com/specimen/Spectral), and
  [Marcellus](https://fonts.google.com/specimen/Marcellus)
  (SIL Open Font License, via Google Fonts)

## Thanks

To the Avalore staff, lore team, and community for building and maintaining
a freely readable, carefully written ruleset — and for keeping the
mechanics precise enough that a simulator like this is possible.
