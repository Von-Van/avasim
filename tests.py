"""
Test suite for Avalore Character Simulator

Tests all core functionality including stats, skills, backgrounds,
items, XP system, and character persistence.
"""

import unittest
import json
import os
import tempfile
from avasim import (
    Character,
    Item,
    STATS,
    BACKGROUNDS,
    ITEMS,
    create_character,
    STAT_MAX,
    SKILL_MAX
)


class TestCharacterCreation(unittest.TestCase):
    """Test character creation and basic attributes."""
    
    def test_default_character(self):
        """Test creating a default character."""
        char = Character(name="Test Hero")
        
        self.assertEqual(char.name, "Test Hero")
        self.assertIsNone(char.background)
        self.assertEqual(char.total_xp, 0)
        self.assertEqual(char.spent_xp, 0)
        
        # All stats should start at 0
        for stat_name in ["Dexterity", "Intelligence", "Harmony", "Strength"]:
            self.assertEqual(char.get_stat(stat_name), 0)
        
        # All skills should start at 0
        for stat_name, skills in STATS.items():
            for skill_name in skills:
                self.assertEqual(char.get_skill(stat_name, skill_name), 0)
    
    def test_derived_stats(self):
        """Test derived stats calculation."""
        char = Character(name="Test Hero")
        
        # Default HP should be 20
        self.assertEqual(char.get_max_hp(), 20)
        self.assertEqual(char.current_hp, 20)
        
        # Default initiative is based on DEX (0)
        self.assertEqual(char.get_initiative_modifier(), 0)
        
        # Default action count
        self.assertEqual(char.action_count, 2)
    
    def test_create_character_helper(self):
        """Test the create_character helper function."""
        char = create_character("Hero", background="Soldier", starting_xp=20)
        
        self.assertEqual(char.name, "Hero")
        self.assertEqual(char.background, "Soldier")
        self.assertEqual(char.total_xp, 20)
        self.assertEqual(char.get_stat("Strength"), 1)  # Soldier gives +1 STR


class TestStatsAndSkills(unittest.TestCase):
    """Test stat and skill system."""
    
    def test_get_modifier(self):
        """Test combined stat+skill modifier."""
        char = Character()
        char.base_stats["Dexterity"] = 2
        char.base_skills["Dexterity"]["Stealth"] = 1
        
        # Modifier should be stat + skill
        self.assertEqual(char.get_modifier("Dexterity", "Stealth"), 3)
    
    def test_negative_values(self):
        """Test that negative stat/skill values work correctly."""
        char = Character()
        char.base_stats["Strength"] = -2
        char.base_skills["Strength"]["Athletics"] = 1
        
        self.assertEqual(char.get_stat("Strength"), -2)
        self.assertEqual(char.get_modifier("Strength", "Athletics"), -1)
    
    def test_invalid_stat_skill(self):
        """Test error handling for invalid stats/skills."""
        char = Character()
        
        with self.assertRaises(ValueError):
            char.get_stat("InvalidStat")
        
        with self.assertRaises(ValueError):
            char.get_skill("Dexterity", "InvalidSkill")


class TestBackgrounds(unittest.TestCase):
    """Test background system."""
    
    def test_apply_soldier_background(self):
        """Test applying Soldier background."""
        char = Character()
        char.apply_background("Soldier")
        
        self.assertEqual(char.background, "Soldier")
        self.assertEqual(char.get_stat("Strength"), 1)
    
    def test_apply_seafarer_background(self):
        """Test applying Seafarer background with skill bonus."""
        char = Character()
        char.apply_background("Seafarer")
        
        self.assertEqual(char.background, "Seafarer")
        self.assertEqual(char.get_skill("Dexterity", "Acrobatics"), 1)
    
    def test_cannot_apply_multiple_backgrounds(self):
        """Test that only one background can be applied."""
        char = Character()
        char.apply_background("Soldier")
        
        with self.assertRaises(ValueError):
            char.apply_background("Noble")
    
    def test_invalid_background(self):
        """Test error handling for invalid background."""
        char = Character()
        
        with self.assertRaises(ValueError):
            char.apply_background("InvalidBackground")
    
    def test_all_backgrounds_valid(self):
        """Test that all defined backgrounds can be applied."""
        for bg_name in BACKGROUNDS.keys():
            char = Character()
            char.apply_background(bg_name)
            self.assertEqual(char.background, bg_name)


class TestXPSystem(unittest.TestCase):
    """Test XP tracking and spending."""
    
    def test_add_xp(self):
        """Test adding XP to character."""
        char = Character()
        char.add_xp(100)
        
        self.assertEqual(char.total_xp, 100)
        self.assertEqual(char.spent_xp, 0)
    
    def test_spend_xp_on_stat(self):
        """Test spending XP to raise stats."""
        char = Character()
        char.add_xp(20)
        
        # Cost to go from 0 to 1 is 4
        result = char.spend_xp_on_stat("Strength", 1)
        self.assertTrue(result)
        self.assertEqual(char.get_stat("Strength"), 1)
        self.assertEqual(char.spent_xp, 4)
    
    def test_spend_xp_on_skill(self):
        """Test spending XP to raise skills."""
        char = Character()
        char.add_xp(10)
        
        # Cost to go from 0 to 1 is 2
        result = char.spend_xp_on_skill("Dexterity", "Stealth", 1)
        self.assertTrue(result)
        self.assertEqual(char.get_skill("Dexterity", "Stealth"), 1)
        self.assertEqual(char.spent_xp, 2)
    
    def test_insufficient_xp(self):
        """Test that spending fails with insufficient XP."""
        char = Character()
        char.add_xp(2)  # Not enough for stat increase
        
        result = char.spend_xp_on_stat("Strength", 1)
        self.assertFalse(result)
        self.assertEqual(char.get_stat("Strength"), 0)
        self.assertEqual(char.spent_xp, 0)
    
    def test_cannot_exceed_max(self):
        """Test that stats/skills cannot exceed maximum."""
        char = Character()
        char.add_xp(1000)
        
        # Raise to max
        char.spend_xp_on_stat("Strength", STAT_MAX)
        self.assertEqual(char.get_stat("Strength"), STAT_MAX)
        
        # Try to exceed max
        result = char.spend_xp_on_stat("Strength", STAT_MAX + 1)
        self.assertFalse(result)
        self.assertEqual(char.get_stat("Strength"), STAT_MAX)
    
    def test_multi_level_increase(self):
        """Test raising stat multiple levels at once."""
        char = Character()
        char.add_xp(100)
        
        # Cost from 0->1->2 is 4+5=9
        result = char.spend_xp_on_stat("Dexterity", 2)
        self.assertTrue(result)
        self.assertEqual(char.get_stat("Dexterity"), 2)
        self.assertEqual(char.spent_xp, 9)


class TestItems(unittest.TestCase):
    """Test item system."""
    
    def test_create_item(self):
        """Test creating an item."""
        item = Item(
            name="Test Sword",
            item_type="weapon",
            stat_modifiers={"Strength": 1}
        )
        
        self.assertEqual(item.name, "Test Sword")
        self.assertEqual(item.item_type, "weapon")
        self.assertEqual(item.stat_modifiers["Strength"], 1)
    
    def test_equip_item_with_requirements(self):
        """Test equipping item with stat requirements."""
        char = Character()
        longbow = ITEMS["Longbow"]
        
        # Should fail - character doesn't meet requirements
        result = char.equip_item(longbow)
        self.assertFalse(result)
        
        # Raise stats to meet requirements
        char.base_stats["Dexterity"] = 1
        char.base_skills["Dexterity"]["Acrobatics"] = 0
        char.base_stats["Strength"] = 1
        char.base_skills["Strength"]["Athletics"] = 0
        
        # Should succeed now
        result = char.equip_item(longbow)
        self.assertTrue(result)
        self.assertIn(longbow, char.equipped_items)
    
    def test_item_stat_modifier(self):
        """Test that equipped items modify stats."""
        char = Character()
        belt = ITEMS["Belt of Giant Strength"]
        
        # Equip the belt (no requirements)
        char.equip_item(belt)
        
        # Strength should be increased
        self.assertEqual(char.base_stats["Strength"], 0)
        self.assertEqual(char.get_stat("Strength"), 1)
    
    def test_item_skill_modifier(self):
        """Test that equipped items modify skills."""
        char = Character()
        tools = ITEMS["Thief's Tools"]
        
        char.equip_item(tools)
        
        # Finesse should be increased
        self.assertEqual(char.base_skills["Dexterity"]["Finesse"], 0)
        self.assertEqual(char.get_skill("Dexterity", "Finesse"), 1)
    
    def test_item_hp_modifier(self):
        """Test that equipped items modify HP."""
        char = Character()
        self.assertEqual(char.get_max_hp(), 20)
        
        armor = ITEMS["Heavy Armor"]
        
        # Need to meet requirements first
        char.base_stats["Strength"] = 1
        char.base_skills["Strength"]["Fortitude"] = 1
        
        char.equip_item(armor)
        self.assertEqual(char.get_max_hp(), 25)
        self.assertEqual(char.current_hp, 25)
    
    def test_unequip_item(self):
        """Test unequipping items."""
        char = Character()
        belt = ITEMS["Belt of Giant Strength"]
        
        char.equip_item(belt)
        self.assertEqual(char.get_stat("Strength"), 1)
        
        result = char.unequip_item(belt)
        self.assertTrue(result)
        self.assertEqual(char.get_stat("Strength"), 0)
        self.assertNotIn(belt, char.equipped_items)
    
    def test_unequip_hp_modifier(self):
        """Test that unequipping items with HP modifiers adjusts current HP."""
        char = Character()
        amulet = ITEMS["Amulet of Health"]
        
        char.equip_item(amulet)
        self.assertEqual(char.get_max_hp(), 25)
        self.assertEqual(char.current_hp, 25)
        
        # Take some damage
        char.current_hp = 22
        
        # Unequip should reduce max HP and cap current HP
        char.unequip_item(amulet)
        self.assertEqual(char.get_max_hp(), 20)
        self.assertEqual(char.current_hp, 20)


class TestPersistence(unittest.TestCase):
    """Test character save/load functionality."""
    
    def setUp(self):
        """Create a temporary directory for test files."""
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir)
    
    def test_save_and_load_basic(self):
        """Test saving and loading a basic character."""
        char = Character(name="Test Character")
        char.base_stats["Strength"] = 2
        char.base_skills["Strength"]["Athletics"] = 1
        char.add_xp(50)
        
        filepath = os.path.join(self.temp_dir, "test_char.json")
        char.save_to_file(filepath)
        
        loaded = Character.load_from_file(filepath)
        
        self.assertEqual(loaded.name, "Test Character")
        self.assertEqual(loaded.get_stat("Strength"), 2)
        self.assertEqual(loaded.get_skill("Strength", "Athletics"), 1)
        self.assertEqual(loaded.total_xp, 50)
    
    def test_save_and_load_with_background(self):
        """Test saving and loading character with background."""
        char = Character(name="Hero")
        char.apply_background("Soldier")
        
        filepath = os.path.join(self.temp_dir, "test_hero.json")
        char.save_to_file(filepath)
        
        loaded = Character.load_from_file(filepath)
        
        self.assertEqual(loaded.background, "Soldier")
        self.assertEqual(loaded.get_stat("Strength"), 1)
    
    def test_save_and_load_with_items(self):
        """Test saving and loading character with equipped items."""
        char = Character(name="Warrior")
        belt = ITEMS["Belt of Giant Strength"]
        char.equip_item(belt)
        
        filepath = os.path.join(self.temp_dir, "test_warrior.json")
        char.save_to_file(filepath)
        
        loaded = Character.load_from_file(filepath)
        
        self.assertEqual(len(loaded.equipped_items), 1)
        self.assertEqual(loaded.equipped_items[0].name, "Belt of Giant Strength")
        self.assertEqual(loaded.get_stat("Strength"), 1)
    
    def test_save_format_is_json(self):
        """Test that save file is valid JSON."""
        char = Character(name="Test")
        
        filepath = os.path.join(self.temp_dir, "test.json")
        char.save_to_file(filepath)
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        self.assertIsInstance(data, dict)
        self.assertEqual(data["name"], "Test")
        self.assertIn("base_stats", data)
        self.assertIn("base_skills", data)


class TestCharacterSheet(unittest.TestCase):
    """Test character sheet generation."""
    
    def test_character_sheet_output(self):
        """Test that character sheet generates readable output."""
        char = create_character("Test Hero", background="Soldier", starting_xp=10)
        char.spend_xp_on_skill("Strength", "Athletics", 1)
        
        sheet = char.get_character_sheet()
        
        self.assertIn("Test Hero", sheet)
        self.assertIn("Soldier", sheet)
        self.assertIn("Strength", sheet)
        self.assertIn("Athletics", sheet)


class TestIntegration(unittest.TestCase):
    """Integration tests for complex scenarios."""
    
    def test_complete_character_workflow(self):
        """Test a complete character creation and customization workflow."""
        # Create character with background
        char = create_character("Elara", background="Ranger", starting_xp=50)
        
        # Verify background applied
        self.assertEqual(char.get_skill("Harmony", "Nature"), 1)
        
        # Spend XP on stats and skills
        char.spend_xp_on_stat("Dexterity", 2)
        char.spend_xp_on_skill("Dexterity", "Stealth", 2)
        
        # Equip items
        cloak = ITEMS["Cloak of Stealth"]
        char.equip_item(cloak)
        
        # Verify final stats
        self.assertEqual(char.get_stat("Dexterity"), 2)
        self.assertEqual(char.get_skill("Dexterity", "Stealth"), 3)  # 2 base + 1 from cloak
        
        # Save and load
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            filepath = f.name
        
        try:
            char.save_to_file(filepath)
            loaded = Character.load_from_file(filepath)
            
            self.assertEqual(loaded.name, "Elara")
            self.assertEqual(loaded.get_stat("Dexterity"), 2)
            self.assertEqual(loaded.get_skill("Dexterity", "Stealth"), 3)
        finally:
            os.unlink(filepath)
    
    def test_warrior_with_equipment(self):
        """Test a warrior character with weapon requirements."""
        char = create_character("Grom", background="Warrior", starting_xp=20)
        
        # Warrior gets +1 Athletics
        self.assertEqual(char.get_skill("Strength", "Athletics"), 1)
        
        # Try to equip Spellblade (requires STR:Athletics 0, STR:Fortitude 1)
        spellblade = ITEMS["Spellblade"]
        result = char.equip_item(spellblade)
        self.assertFalse(result)  # Doesn't meet Fortitude requirement
        
        # Raise Fortitude
        char.spend_xp_on_skill("Strength", "Fortitude", 1)
        
        # Should work now
        result = char.equip_item(spellblade)
        self.assertTrue(result)
    
    def test_mage_character(self):
        """Test a mage-type character."""
        char = create_character("Zara", background="Mage", starting_xp=30)
        
        # Mage gets +1 Arcana
        self.assertEqual(char.get_skill("Harmony", "Arcana"), 1)
        
        # Raise Intelligence for better spell research
        char.spend_xp_on_stat("Intelligence", 2)
        char.spend_xp_on_skill("Intelligence", "Research", 1)
        
        # Equip Ring of Intelligence
        ring = ITEMS["Ring of Intelligence"]
        char.equip_item(ring)
        
        self.assertEqual(char.get_stat("Intelligence"), 3)  # 2 base + 1 from ring


if __name__ == '__main__':
    unittest.main()
