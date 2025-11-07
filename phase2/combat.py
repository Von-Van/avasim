from dataclasses import dataclass, field
from typing import Optional, Dict, List, Tuple
import random

# Simple, extendable Phase 2 combat core
# Uses a distance-based spatial model for now but includes position as (x,y)

def roll_2d10() -> Tuple[int, Tuple[int,int]]:
    a = random.randint(1,10)
    b = random.randint(1,10)
    return a + b, (a,b)


def stat_to_mod(stat: int) -> int:
    # Convert raw stat (e.g. 10) to a small modifier used by initiative/skills.
    # Cap at -3..+3 to reflect Avalore skill caps in many places.
    m = (stat - 10) // 2
    return max(-3, min(3, m))


@dataclass
class Weapon:
    name: str = "Fist"
    damage: int = 2
    accuracy: int = 0
    ap: bool = False
    actions: int = 1


@dataclass
class Armor:
    name: str = "Clothes"
    protection: int = 0  # flat damage reduction
    category: str = "none"


@dataclass
class Combatant:
    id: int
    name: str
    hp: int
    max_hp: int
    stats: Dict[str,int]
    anima: int = 0
    weapon: Weapon = field(default_factory=Weapon)
    armor: Armor = field(default_factory=Armor)
    position: Tuple[int,int] = (0,0)  # grid position groundwork
    is_npc: bool = False
    status: Dict[str, bool] = field(default_factory=dict)
    # simple flags: 'evade', 'block'

    def dex_mod(self) -> int:
        return stat_to_mod(self.stats.get("dexterity", 10))

    def take_damage(self, amount: int, ap: bool=False) -> int:
        # Returns actual damage applied
        if amount <= 0:
            return 0
        if ap:
            final = max(0, amount)
        else:
            final = max(0, amount - self.armor.protection)
        self.hp = max(0, self.hp - final)
        return final


class CombatEngine:
    def __init__(self, combatants: List[Combatant]):
        self.combatants = combatants
        self.round = 0
        self.initiative_order: List[int] = []  # indices into combatants
        self.current_index = 0
        self.log: List[str] = []

    def logf(self, msg: str):
        self.log.append(msg)

    def roll_initiative(self):
        entries = []
        # roll 2d10 + DEX mod
        for i, c in enumerate(self.combatants):
            total, dice = roll_2d10()
            score = total + c.dex_mod()
            entries.append((score, c.stats.get("dexterity", 10), total, i, dice))
            self.logf(f"{c.name} rolls initiative {total} + DEXmod({c.dex_mod()}) = {score}")

        # sort by score desc, break ties by raw DEX desc, then reroll among exact ties
        entries.sort(key=lambda e: (e[0], e[1]), reverse=True)

        # detect exact ties on both score and dex stat, and reroll those groups
        ordered = []
        i = 0
        while i < len(entries):
            # find group with same score and same raw dex
            j = i + 1
            group = [entries[i]]
            while j < len(entries) and entries[j][0] == entries[i][0] and entries[j][1] == entries[i][1]:
                group.append(entries[j])
                j += 1
            if len(group) == 1:
                ordered.append(group[0])
            else:
                # reroll order among these tied combatants
                self.logf(f"Tie detected among {[self.combatants[g[3]].name for g in group]}; rerolling tie-breakers")
                rerolled = []
                for (_, _, _, idx, _) in group:
                    tot, dice = roll_2d10()
                    rerolled.append((tot, idx, dice))
                    self.logf(f"Reroll for {self.combatants[idx].name}: {tot} ({dice})")
                rerolled.sort(key=lambda x: x[0], reverse=True)
                for r in rerolled:
                    # append with original score/dex placeholders so ordering remains deterministic post-reroll
                    ordered.append((999, self.combatants[r[1]].stats.get("dexterity", 10), r[0], r[1], r[2]))
            i = j

        # flatten to initiative order of indices
        self.initiative_order = [e[3] for e in ordered]
        self.current_index = 0
        self.round = 1
        self.logf(f"Initiative order: {', '.join(self.combatants[i].name for i in self.initiative_order)}")

    def get_current_combatant(self) -> Optional[Combatant]:
        if not self.initiative_order:
            return None
        idx = self.initiative_order[self.current_index]
        return self.combatants[idx]

    def advance_turn(self):
        self.current_index += 1
        if self.current_index >= len(self.initiative_order):
            self.current_index = 0
            self.round += 1
            self.logf(f"--- Starting round {self.round} ---")

    def perform_attack(self, attacker: Combatant, defender: Combatant):
        # resolve attack: roll 2d10 + accuracy
        atk_roll, dice = roll_2d10()
        total = atk_roll + attacker.weapon.accuracy
        is_crit = (dice == (10,10))
        self.logf(f"{attacker.name} attacks {defender.name}: roll {atk_roll} {dice} + accuracy({attacker.weapon.accuracy}) = {total}{' (CRIT)' if is_crit else ''}")

        # check defensive states
        if is_crit:
            # crit auto hits, AP, extra damage if weapon AP
            base_damage = attacker.weapon.damage
            added = 2 if attacker.weapon.ap else 0
            dmg = base_damage + added
            applied = defender.take_damage(dmg, ap=True)
            self.logf(f"CRITICAL! {attacker.name} deals {dmg} AP damage to {defender.name} (applied {applied})")
            return

        # if defender evaded
        if defender.status.get("evade"):
            # defender rolls DEX:Acrobatics capped at +3
            evas_roll, edice = roll_2d10()
            evas_mod = min(3, stat_to_mod(defender.stats.get("dexterity",10)))
            evas_total = evas_roll + evas_mod
            self.logf(f"{defender.name} has Evade: rolls {evas_roll}{edice} + acrobatics({evas_mod}) = {evas_total}")
            if evas_total >= total:
                self.logf(f"{defender.name} evades the attack from {attacker.name}!")
                return
            elif evas_total >= 12:
                # grazing hit
                dmg = max(0, attacker.weapon.damage // 2 + (1 if attacker.weapon.damage %2 else 0))
                applied = defender.take_damage(dmg, ap=attacker.weapon.ap)
                self.logf(f"Grazing hit: {attacker.name} deals {dmg} (after graze) to {defender.name} (applied {applied})")
                return
            else:
                self.logf(f"Evade failed to avoid the attack")

        # if defender blocked
        if defender.status.get("block"):
            block_roll, bdice = roll_2d10()
            # shield block is simplified: 2d10 + small bonus (we'll use dex mod as placeholder)
            block_total = block_roll + stat_to_mod(defender.stats.get("dexterity",10))
            self.logf(f"{defender.name} has Block: rolls {block_roll}{bdice} + blockmod({stat_to_mod(defender.stats.get('dexterity',10))}) = {block_total}")
            # success if >= attacker roll total (simplified)
            if block_total >= total:
                self.logf(f"{defender.name} successfully blocks the attack with their shield!")
                return
            else:
                self.logf(f"Block failed")

        # standard hit check: require >=12 to hit
        if total < 12:
            self.logf(f"{attacker.name} misses {defender.name} (total {total} < 12)")
            return

        # hit: apply damage
        dmg = attacker.weapon.damage
        applied = defender.take_damage(dmg, ap=attacker.weapon.ap)
        self.logf(f"{attacker.name} hits {defender.name} for {dmg} damage (ap={attacker.weapon.ap}), applied {applied}")

    def is_finished(self) -> bool:
        # simple end: one side all at 0 HP. Let's treat combatants with is_npc True as enemies for demo
        allies = [c for c in self.combatants if not c.is_npc and c.hp>0]
        enemies = [c for c in self.combatants if c.is_npc and c.hp>0]
        return len(allies) == 0 or len(enemies) == 0

    def step(self):
        # run one combatant's turn using a very simple AI for NPCs and expecting player choice for non-NPCs
        current = self.get_current_combatant()
        if not current or current.hp <= 0:
            self.advance_turn()
            return
        self.logf(f"Turn: {current.name} (HP {current.hp}/{current.max_hp})")

        # simple action resolution: each combatant gets up to 2 actions
        actions = 2
        while actions > 0 and current.hp > 0:
            # choose target
            if current.is_npc:
                # simple AI: attack nearest enemy
                targets = [c for c in self.combatants if c.is_npc != current.is_npc and c.hp>0]
                if not targets:
                    break
                # pick target by proximity (manhattan)
                targets.sort(key=lambda t: abs(t.position[0]-current.position[0]) + abs(t.position[1]-current.position[1]))
                target = targets[0]
                self.perform_attack(current, target)
            else:
                # for player-controlled, just attack the first enemy available in this MVP
                targets = [c for c in self.combatants if c.is_npc and c.hp>0]
                if not targets:
                    break
                target = targets[0]
                self.perform_attack(current, target)
            actions -= 1
            # reset temporary statuses like evade/block after being used this round
        # clear defensive statuses at end of turn
        current.status["evade"] = False
        current.status["block"] = False

        self.advance_turn()


# Small helper to create a Combatant from the existing Character model (lightweight mapping)

def combatant_from_character(cid: int, char_obj, is_npc: bool=False, position=(0,0)) -> Combatant:
    # char_obj is expected to be an instance with .name, .level, .stats, .equipment etc.
    name = getattr(char_obj, "name", "PC")
    stats = getattr(char_obj, "stats", {"strength":10, "dexterity":10, "intelligence":10, "vitality":10})
    max_hp = 20 + (stats.get("vitality",10) - 10)  # small HP scaling heuristic
    # try to map weapon name to simple Weapon values
    weapon_item = (getattr(char_obj, "equipment", {}) or {}).get("weapon")
    if weapon_item and getattr(weapon_item, 'name', None):
        wname = weapon_item.name
        if "Sword" in wname:
            weapon = Weapon(name=wname, damage=3, accuracy=0, ap=False)
        elif "Wand" in wname:
            weapon = Weapon(name=wname, damage=2, accuracy=2, ap=True)
        else:
            weapon = Weapon(name=wname, damage=2, accuracy=0, ap=False)
    else:
        weapon = Weapon()

    # simple armor inference
    chest = (getattr(char_obj, "equipment", {}) or {}).get("chest")
    if chest and getattr(chest, 'name','').lower().find("chainmail") >= 0:
        armor = Armor(name=chest.name, protection=2, category="medium")
    elif chest:
        armor = Armor(name=chest.name, protection=1, category="light")
    else:
        armor = Armor()

    anima = getattr(char_obj, "anima", 0)
    return Combatant(id=cid, name=name, hp=max_hp, max_hp=max_hp, stats=stats.copy(), anima=anima, weapon=weapon, armor=armor, position=position, is_npc=is_npc)