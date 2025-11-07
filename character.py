from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from copy import deepcopy
import json

default_slots = ["weapon", "offhand", "head", "chest", "legs", "boots", "ring", "amulet"]

dataclass
class Item:
    name: str
    slot: str
    bonuses: Dict[str, int] = field(default_factory=dict)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "slot": self.slot, "bonuses": self.bonuses, "description": self.description}

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Item":
        if not d:
            return None
        return Item(name=d.get("name", "item"), slot=d.get("slot", ""), bonuses=d.get("bonuses", {}), description=d.get("description", ""))


dataclass
class Character:
    name: str = ""
    level: int = 1
    char_class: str = ""
    race: str = ""
    notes: str = ""
    stats: Dict[str, int] = field(default_factory=lambda: {"strength": 10, "dexterity": 10, "intelligence": 10, "vitality": 10})
    equipment: Dict[str, Optional[Item]] = field(default_factory=lambda: {s: None for s in default_slots})

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["equipment"] = {slot: (item.to_dict() if item else None) for slot, item in self.equipment.items()}
        return d

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "Character":
        c = Character()
        c.name = d.get("name", "")
        c.level = d.get("level", 1)
        c.char_class = d.get("char_class", "") or d.get("class", "")
        c.race = d.get("race", "")
        c.notes = d.get("notes", "")
        c.stats = d.get("stats", c.stats)
        eq = {}
        for slot in default_slots:
            item_d = (d.get("equipment") or {}).get(slot)
            eq[slot] = Item.from_dict(item_d) if item_d else None
        c.equipment = eq
        return c

    @staticmethod
    def default() -> "Character":
        # A richer default character to start with
        base = Character(
            name="AvaSim Default",
            level=5,
            char_class="Warrior",
            race="Human",
            notes="A sample starting character.",
            stats={"strength": 14, "dexterity": 11, "intelligence": 9, "vitality": 13},
        )
        # lightweight sample equipment to equip by default
        base.equipment["weapon"] = Item(name="Iron Sword", slot="weapon", bonuses={"strength": 3}, description="A sturdy iron blade.")
        base.equipment["offhand"] = Item(name="Wooden Shield", slot="offhand", bonuses={"vitality": 2}, description="Basic wooden shield.")
        base.equipment["head"] = Item(name="Leather Cap", slot="head", bonuses={"dexterity": 1}, description="Simple leather headgear.")
        base.equipment["chest"] = Item(name="Chainmail", slot="chest", bonuses={"vitality": 4, "strength": 1}, description="Protective chain armor.")
        base.equipment["boots"] = Item(name="Cloth Boots", slot="boots", bonuses={"dexterity": 1}, description="Light boots for mobility.")
        base.equipment["ring"] = Item(name="Ring of Learning", slot="ring", bonuses={"intelligence": 2}, description="Improves magical aptitude.")
        base.equipment["amulet"] = Item(name="Amulet of Vigor", slot="amulet", bonuses={"vitality": 3}, description="Increases health and resilience.")
        return base

    def equip(self, slot: str, item: Item):
        if slot not in self.equipment:
            raise KeyError(f"Unknown slot: {slot}")
        self.equipment[slot] = deepcopy(item)

    def unequip(self, slot: str):
        if slot in self.equipment:
            self.equipment[slot] = None

    def equipment_table(self) -> List[Dict[str, Any]]:
        rows = []
        for slot, item in self.equipment.items():
            if item:
                rows.append({"slot": slot, "name": item.name, "bonuses": item.bonuses, "description": item.description})
            else:
                rows.append({"slot": slot, "name": "", "bonuses": {}, "description": ""})
        return rows

    def aggregated_equipment_bonuses(self) -> Dict[str, int]:
        agg = {}
        for item in self.equipment.values():
            if not item:
                continue
            for k, v in item.bonuses.items():
                agg[k] = agg.get(k, 0) + v
        return agg

    def effective_stats(self) -> Dict[str, int]:
        agg = self.aggregated_equipment_bonuses()
        eff = {k: self.stats.get(k, 0) + agg.get(k, 0) for k in self.stats.keys()}
        for k, v in agg.items():
            if k not in eff:
                eff[k] = v
        return eff

    def to_summary(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "level": self.level,
            "class": self.char_class,
            "race": self.race,
            "base_stats": self.stats,
            "equipment_bonuses": self.aggregated_equipment_bonuses(),
            "effective_stats": self.effective_stats(),
        }