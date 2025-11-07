#!/usr/bin/env python3
"""
Example usage of the Avalore Character Simulator

This script demonstrates the core features of the character simulator,
including character creation, backgrounds, equipment, XP spending, and persistence.
"""

from avasim import Character, ITEMS, BACKGROUNDS, create_character


def example_1_basic_character():
    """Example 1: Create a basic character with no customization."""
    print("=" * 70)
    print("EXAMPLE 1: Basic Character Creation")
    print("=" * 70)
    
    char = Character(name="Basic Hero")
    print(char.get_character_sheet())
    print()


def example_2_character_with_background():
    """Example 2: Create a character with a background."""
    print("=" * 70)
    print("EXAMPLE 2: Character with Background")
    print("=" * 70)
    
    char = create_character("Aria Swiftblade", background="Rogue", starting_xp=0)
    print(char.get_character_sheet())
    print()


def example_3_spending_xp():
    """Example 3: Create a character and spend XP to improve stats/skills."""
    print("=" * 70)
    print("EXAMPLE 3: Character Advancement with XP")
    print("=" * 70)
    
    char = create_character("Grom Ironheart", background="Warrior", starting_xp=50)
    
    print("Initial character:")
    print(char.get_character_sheet())
    print()
    
    # Spend XP to improve Strength and Athletics
    print("Spending XP to improve Strength to +2 (costs 9 XP)...")
    char.spend_xp_on_stat("Strength", 2)
    
    print("Spending XP to improve Fortitude to +2 (costs 4 XP)...")
    char.spend_xp_on_skill("Strength", "Fortitude", 2)
    
    print("\nCharacter after advancement:")
    print(char.get_character_sheet())
    print()


def example_4_equipment():
    """Example 4: Equip items with stat modifiers."""
    print("=" * 70)
    print("EXAMPLE 4: Equipping Items")
    print("=" * 70)
    
    char = create_character("Lyra Shadowstep", background="Rogue", starting_xp=20)
    
    # Improve stats to meet requirements
    char.spend_xp_on_stat("Dexterity", 2)
    char.spend_xp_on_skill("Dexterity", "Stealth", 1)
    
    print("Character before equipment:")
    print(char.get_character_sheet())
    print()
    
    # Equip items
    cloak = ITEMS["Cloak of Stealth"]
    tools = ITEMS["Thief's Tools"]
    
    print(f"Equipping {cloak.name}...")
    char.equip_item(cloak)
    
    print(f"Equipping {tools.name}...")
    char.equip_item(tools)
    
    print("\nCharacter with equipment:")
    print(char.get_character_sheet())
    print()


def example_5_weapon_requirements():
    """Example 5: Demonstrate weapon requirements."""
    print("=" * 70)
    print("EXAMPLE 5: Weapon Requirements")
    print("=" * 70)
    
    char = create_character("Ranger Vale", background="Ranger", starting_xp=30)
    
    longbow = ITEMS["Longbow"]
    
    print("Character attempting to equip Longbow:")
    print(f"  Requirements: DEX:Acrobatics >= 1, STR:Athletics >= 1")
    print(f"  Current DEX:Acrobatics = {char.get_modifier('Dexterity', 'Acrobatics')}")
    print(f"  Current STR:Athletics = {char.get_modifier('Strength', 'Athletics')}")
    
    result = char.equip_item(longbow)
    print(f"  Can equip? {result}")
    print()
    
    # Improve stats to meet requirements
    print("Improving Dexterity to +1 and Athletics to +1...")
    char.spend_xp_on_stat("Dexterity", 1)
    char.spend_xp_on_skill("Strength", "Athletics", 1)
    
    print(f"  New DEX:Acrobatics = {char.get_modifier('Dexterity', 'Acrobatics')}")
    print(f"  New STR:Athletics = {char.get_modifier('Strength', 'Athletics')}")
    
    result = char.equip_item(longbow)
    print(f"  Can equip? {result}")
    print()
    
    if result:
        print("Character with Longbow equipped:")
        print(char.get_character_sheet())
    print()


def example_6_save_and_load():
    """Example 6: Save and load a character."""
    print("=" * 70)
    print("EXAMPLE 6: Character Persistence")
    print("=" * 70)
    
    # Create and customize a character
    char = create_character("Zara Stormcaller", background="Mage", starting_xp=40)
    char.spend_xp_on_stat("Harmony", 2)
    char.spend_xp_on_stat("Intelligence", 1)
    char.spend_xp_on_skill("Harmony", "Arcana", 2)
    
    ring = ITEMS["Ring of Intelligence"]
    char.equip_item(ring)
    
    print("Original character:")
    print(char.get_character_sheet())
    print()
    
    # Save to file
    filename = "/tmp/zara_stormcaller.json"
    print(f"Saving character to {filename}...")
    char.save_to_file(filename)
    print("Character saved successfully!")
    print()
    
    # Load from file
    print(f"Loading character from {filename}...")
    loaded_char = Character.load_from_file(filename)
    print("Character loaded successfully!")
    print()
    
    print("Loaded character:")
    print(loaded_char.get_character_sheet())
    print()
    
    # Verify they match
    print("Verification:")
    print(f"  Names match: {char.name == loaded_char.name}")
    print(f"  Stats match: {char.base_stats == loaded_char.base_stats}")
    print(f"  Skills match: {char.base_skills == loaded_char.base_skills}")
    print(f"  Equipped items match: {len(char.equipped_items) == len(loaded_char.equipped_items)}")
    print()


def example_7_all_backgrounds():
    """Example 7: Show all available backgrounds."""
    print("=" * 70)
    print("EXAMPLE 7: Available Backgrounds")
    print("=" * 70)
    
    for bg_name, bg_data in BACKGROUNDS.items():
        print(f"\n{bg_name}: {bg_data['description']}")
        
        if bg_data.get('stat_bonuses'):
            print(f"  Stat bonuses: {bg_data['stat_bonuses']}")
        
        if bg_data.get('skill_bonuses'):
            print(f"  Skill bonuses: {bg_data['skill_bonuses']}")
    
    print()


def example_8_complete_build():
    """Example 8: Complete character build demonstration."""
    print("=" * 70)
    print("EXAMPLE 8: Complete Character Build - Elara Moonwhisper")
    print("=" * 70)
    
    # Create a stealth-focused character
    char = create_character("Elara Moonwhisper", background="Scout", starting_xp=60)
    
    print("Starting character with Scout background (+1 Perception):")
    print(f"  XP Available: {char.total_xp - char.spent_xp}")
    print()
    
    # Build for stealth and perception
    print("Building for stealth and awareness...")
    char.spend_xp_on_stat("Dexterity", 2)  # Cost: 9 XP
    char.spend_xp_on_stat("Intelligence", 1)  # Cost: 4 XP
    char.spend_xp_on_skill("Dexterity", "Stealth", 2)  # Cost: 4 XP
    char.spend_xp_on_skill("Dexterity", "Acrobatics", 1)  # Cost: 2 XP
    
    print(f"  XP Remaining: {char.total_xp - char.spent_xp}")
    print()
    
    # Equip stealth gear
    print("Equipping stealth gear...")
    char.equip_item(ITEMS["Cloak of Stealth"])
    char.equip_item(ITEMS["Thief's Tools"])
    print()
    
    print("Final character build:")
    print(char.get_character_sheet())
    print()
    
    print("Key capabilities:")
    print(f"  Stealth check: 2d10 + {char.get_modifier('Dexterity', 'Stealth')}")
    print(f"  Perception check: 2d10 + {char.get_modifier('Intelligence', 'Perception')}")
    print(f"  Acrobatics check: 2d10 + {char.get_modifier('Dexterity', 'Acrobatics')}")
    print(f"  Finesse check: 2d10 + {char.get_modifier('Dexterity', 'Finesse')}")
    print(f"  Initiative: +{char.get_initiative_modifier()}")
    print()


def main():
    """Run all examples."""
    examples = [
        example_1_basic_character,
        example_2_character_with_background,
        example_3_spending_xp,
        example_4_equipment,
        example_5_weapon_requirements,
        example_6_save_and_load,
        example_7_all_backgrounds,
        example_8_complete_build
    ]
    
    for example in examples:
        example()
        input("Press Enter to continue to next example...")
        print("\n\n")


if __name__ == "__main__":
    main()
