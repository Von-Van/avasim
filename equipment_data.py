from character import Item

# A small set of sample equipment to choose from in the Streamlit app.
sample_equipment = {
    "Iron Sword": Item(name="Iron Sword", slot="weapon", bonuses={"strength": 3}, description="A sturdy iron blade."),
    "Wooden Shield": Item(name="Wooden Shield", slot="offhand", bonuses={"vitality": 2}, description="Basic wooden shield."),
    "Leather Cap": Item(name="Leather Cap", slot="head", bonuses={"dexterity": 1}, description="Simple leather headgear."),
    "Chainmail": Item(name="Chainmail", slot="chest", bonuses={"vitality": 4, "strength": 1}, description="Protective chain armor."),
    "Cloth Boots": Item(name="Cloth Boots", slot="boots", bonuses={"dexterity": 1}, description="Light boots for mobility."),
    "Ring of Learning": Item(name="Ring of Learning", slot="ring", bonuses={"intelligence": 2}, description="Improves magical aptitude."),
    "Amulet of Vigor": Item(name="Amulet of Vigor", slot="amulet", bonuses={"vitality": 3}, description="Increases health and resilience."),
}