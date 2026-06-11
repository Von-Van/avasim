import json
import unittest
from pathlib import Path

from combat import AVALORE_ARMOR, AVALORE_FEATS, AVALORE_SHIELDS, AVALORE_SPELLS, AVALORE_WEAPONS
from combat.catalog import CATALOG_VERSION, load_catalog

FEATS_SOURCE = Path(__file__).parent / "tests" / "data" / "avalore_feats_source.json"


class TestRuleCatalogs(unittest.TestCase):
    def test_catalog_names_match_exported_constants(self):
        self.assertEqual(
            {entry["name"] for entry in load_catalog("weapons")["entries"]},
            set(AVALORE_WEAPONS),
        )
        self.assertEqual(
            {entry["name"] for entry in load_catalog("armor")["entries"]},
            set(AVALORE_ARMOR),
        )
        self.assertEqual(
            {entry["name"] for entry in load_catalog("shields")["entries"]},
            set(AVALORE_SHIELDS),
        )
        self.assertEqual(
            {entry["name"] for entry in load_catalog("feats")["entries"]},
            set(AVALORE_FEATS),
        )
        self.assertEqual(
            {entry["name"] for entry in load_catalog("spells")["entries"]},
            set(AVALORE_SPELLS),
        )

    def test_catalog_version(self):
        for name in ("weapons", "armor", "shields", "feats", "spells"):
            self.assertEqual(load_catalog(name)["version"], CATALOG_VERSION)

    def test_representative_loaded_values(self):
        self.assertEqual(AVALORE_WEAPONS["Arming Sword"].damage, 4)
        self.assertEqual(AVALORE_WEAPONS["Arming Sword"].range_category.value, "melee")
        self.assertEqual(AVALORE_ARMOR["Light Armor"].category.value, "light")
        self.assertEqual(AVALORE_SHIELDS["Small Shield"].shield_type.value, "small")
        self.assertEqual(AVALORE_FEATS["Dual Striker"].stat_requirements["Dexterity"], 1)
        self.assertEqual(AVALORE_SPELLS["Force Bolt"].effects[0].push_blocks, 2)


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


if __name__ == "__main__":
    unittest.main()
