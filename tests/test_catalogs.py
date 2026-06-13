import json
import unittest
from pathlib import Path

from combat import AVALORE_ARMOR, AVALORE_FEATS, AVALORE_SHIELDS, AVALORE_SPELLS, AVALORE_WEAPONS

FEATS_SOURCE = Path(__file__).parent / "data" / "avalore_feats_source.json"
SPELLS_SOURCE = Path(__file__).parent / "data" / "avalore_spells_source.json"


class TestRuleCatalogs(unittest.TestCase):
    def test_representative_literal_values(self):
        self.assertEqual(AVALORE_WEAPONS["Arming Sword"].damage, 4)
        self.assertEqual(AVALORE_WEAPONS["Arming Sword"].range_category.value, "melee")
        self.assertEqual(AVALORE_ARMOR["Light Armor"].category.value, "light")
        self.assertEqual(AVALORE_SHIELDS["Small Shield"].shield_type.value, "small")
        self.assertEqual(AVALORE_FEATS["Dual Striker"].stat_requirements["Dexterity"], 1)
        self.assertEqual(AVALORE_SPELLS["Pyrebolt"].anima_cost, 6)
        self.assertEqual(AVALORE_SPELLS["Displace"].effects[0].push_blocks, 8)
        self.assertTrue(AVALORE_SPELLS["Triage"].engine_wired)
        self.assertFalse(AVALORE_SPELLS["Whisper"].engine_wired)


class TestFeatCoverage(unittest.TestCase):
    """Every feat published at https://avalore.net/feats must be cataloged."""

    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(FEATS_SOURCE.read_text(encoding="utf-8"))

    def test_all_100_site_feats_present(self):
        self.assertEqual(len(self.source), 100)
        missing = {f["name"] for f in self.source} - set(AVALORE_FEATS)
        self.assertEqual(missing, set(), f"feats missing from catalog: {sorted(missing)}")

    def test_catalog_has_no_unlisted_feats(self):
        extra = set(AVALORE_FEATS) - {f["name"] for f in self.source}
        self.assertEqual(extra, set(), f"catalog has feats not on the site: {sorted(extra)}")

    def test_retired_feats_absent(self):
        for retired in ("Armor Piercer", "Parry", "Feint"):
            self.assertNotIn(retired, AVALORE_FEATS)

    def test_limited_flags_match_source(self):
        for f in self.source:
            self.assertEqual(
                AVALORE_FEATS[f["name"]].limited, f["limited"],
                f"limited flag mismatch for {f['name']}",
            )

    def test_descriptions_match_source(self):
        for f in self.source:
            self.assertEqual(
                AVALORE_FEATS[f["name"]].description, f["effect"],
                f"description drift for {f['name']}",
            )


class TestSpellCoverage(unittest.TestCase):
    """Every spell published in the Avalore Grimoire must be cataloged."""

    @classmethod
    def setUpClass(cls):
        cls.source = json.loads(SPELLS_SOURCE.read_text(encoding="utf-8"))

    def test_all_217_site_spells_present(self):
        self.assertEqual(len(self.source), 217)
        missing = {s["name"] for s in self.source} - set(AVALORE_SPELLS)
        self.assertEqual(missing, set(), f"spells missing from catalog: {sorted(missing)}")

    def test_catalog_has_no_unlisted_spells(self):
        extra = set(AVALORE_SPELLS) - {s["name"] for s in self.source}
        self.assertEqual(extra, set(), f"catalog has spells not on the site: {sorted(extra)}")

    def test_canonical_fields_match_source(self):
        for s in self.source:
            spell = AVALORE_SPELLS[s["name"]]
            self.assertEqual(spell.discipline, s["discipline"], f"discipline drift for {s['name']}")
            self.assertEqual(spell.tier, s["tier"], f"tier drift for {s['name']}")
            self.assertEqual(spell.anima_cost, s["anima_cost"], f"anima drift for {s['name']}")
            self.assertEqual(spell.actions_required, s["actions_required"], f"actions drift for {s['name']}")
            self.assertEqual(spell.description, s["effect"], f"description drift for {s['name']}")
            self.assertEqual(spell.requires, s["requires"], f"requirement drift for {s['name']}")

    def test_discipline_counts(self):
        for discipline in ("Ichor", "Cursesmithy", "Ether", "Artifice", "Force", "Tellurgy"):
            count = sum(1 for s in AVALORE_SPELLS.values() if s.discipline == discipline)
            self.assertEqual(count, 32, f"{discipline} should have 32 spells, found {count}")

    def test_wired_spells_have_mechanics(self):
        wired = [s for s in AVALORE_SPELLS.values() if s.engine_wired]
        self.assertGreaterEqual(len(wired), 30)
        for spell in wired:
            has_mechanics = (
                spell.damage > 0 or spell.healing > 0 or spell.healing_dice_count > 0
                or spell.effects
            )
            self.assertTrue(has_mechanics, f"{spell.name} is wired but has no mechanics")


if __name__ == "__main__":
    unittest.main()
