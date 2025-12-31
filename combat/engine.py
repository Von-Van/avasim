from typing import List, Optional, Tuple, Any, Set, Dict
from .participant import CombatParticipant
from .map import TacticalMap
from .items import Weapon, Armor, Shield, AVALORE_WEAPONS
from .feats import Feat
from .spells import Spell
from .enums import RangeCategory, ShieldType, ArmorCategory, StatusEffect, TerrainType
from .dice import roll_2d10, roll_1d2, roll_1d3, roll_1d6

class AvaCombatEngine:
    def __init__(self, participants: List[CombatParticipant], tactical_map: Optional[TacticalMap] = None):
        self.participants = participants
        self.round = 0
        self.turn_order: List[CombatParticipant] = []
        self.current_turn_index = 0
        self.combat_log: List[str] = []
        self.map_log: List[str] = []
        self.map_snapshots: List[Dict[str, Any]] = []
        self.party_initiated: bool = False
        self.party_surprised: bool = False
        self.environment_underwater: bool = False
        self.environment_darkness: bool = False
        self.time_of_day: str = "day"
        self.tactical_map = tactical_map
        if self.tactical_map:
            for p in participants:
                x, y = p.position
                self.tactical_map.set_occupant(x, y, p)
        for p in participants:
            setattr(p, 'engine', self)

    def set_time_of_day(self, time: str) -> str:
        val = time.strip().lower()
        if val not in {"day", "night"}:
            val = "day"
        self.time_of_day = val
        self.environment_darkness = (val == "night")
        self.log(f"Environment set to {self.time_of_day}.")
        return self.time_of_day
    def set_day(self) -> None:
        self.set_time_of_day("day")
    def set_night(self) -> None:
        self.set_time_of_day("night")
    def toggle_day_night(self) -> str:
        new_val = "night" if self.time_of_day == "day" else "day"
        return self.set_time_of_day(new_val)

    def log(self, message: str):
        self.combat_log.append(message)
        print(message)

    def _capture_snapshot(self, label: str, actor: Optional[CombatParticipant] = None, target: Optional[CombatParticipant] = None) -> None:
        if not self.tactical_map:
            return
        grid_cells: List[Dict[str, Any]] = []
        for y in range(self.tactical_map.height):
            for x in range(self.tactical_map.width):
                tile = self.tactical_map.get_tile(x, y)
                occupant = tile.occupant if tile else None
                grid_cells.append({
                    "x": x,
                    "y": y,
                    "terrain": (tile.terrain_type.name.lower() if tile else "wall"),
                    "occupant": getattr(occupant.character, "name", None) if occupant else None,
                })
        snap = {
            "label": label,
            "round": self.round,
            "turn_index": self.current_turn_index,
            "width": self.tactical_map.width,
            "height": self.tactical_map.height,
            "cells": grid_cells,
            "actor": {
                "name": getattr(actor.character, "name", None) if actor else None,
                "position": getattr(actor, "position", None) if actor else None,
            },
            "target": {
                "name": getattr(target.character, "name", None) if target else None,
                "position": getattr(target, "position", None) if target else None,
            },
        }
        self.map_snapshots.append(snap)

    def _log_map_state(self, label: str = "Map state") -> None:
        if not self.tactical_map:
            return
        rows: list[str] = []
        for y in range(self.tactical_map.height):
            line_chars: list[str] = []
            for x in range(self.tactical_map.width):
                tile = self.tactical_map.get_tile(x, y)
                if tile and tile.occupant and isinstance(tile.occupant, CombatParticipant):
                    name = getattr(tile.occupant.character, "name", "?") or "?"
                    line_chars.append(name[0].upper())
                else:
                    terrain = tile.terrain_type if tile else TerrainType.WALL
                    if terrain == TerrainType.WALL:
                        line_chars.append("#")
                    elif terrain == TerrainType.FOREST:
                        line_chars.append("f")
                    elif terrain == TerrainType.WATER:
                        line_chars.append("~")
                    elif terrain == TerrainType.MOUNTAIN:
                        line_chars.append("^")
                    elif terrain == TerrainType.ROAD:
                        line_chars.append("=")
                    else:
                        line_chars.append(".")
            rows.append(" ".join(line_chars))
        legend_parts = []
        for p in self.participants:
            if not hasattr(p, "position"):
                continue
            legend_parts.append(f"{p.character.name} @ {p.position[0]},{p.position[1]}")
        self.map_log.append(f"{label} (Round {self.round}, Turn {self.current_turn_index + 1})")
        self.map_log.extend(rows)
        if legend_parts:
            self.map_log.append("Legend: " + "; ".join(legend_parts))
        actor = self.get_current_participant()
        target = None
        if actor:
            opponents = [p for p in self.participants if p is not actor and p.current_hp > 0]
            target = opponents[0] if opponents else None
        self._capture_snapshot(label, actor, target)

    def get_distance(self, p1: CombatParticipant, p2: CombatParticipant) -> int:
        if not self.tactical_map:
            return 1
        return self.tactical_map.manhattan_distance(p1.position[0], p1.position[1], p2.position[0], p2.position[1])

    def is_in_range(self, attacker: CombatParticipant, target: CombatParticipant, weapon) -> bool:
        if not self.tactical_map:
            return True
        distance = self.get_distance(attacker, target)
        if weapon.range_category == RangeCategory.MELEE:
            return distance <= 1
        elif weapon.range_category == RangeCategory.SKIRMISHING:
            return 2 <= distance <= 8
        elif weapon.range_category == RangeCategory.RANGED:
            return 6 <= distance <= 30
        return False

    def roll_initiative(self):
        self.log("=== Rolling Initiative ===")
        initiative_rolls = []
        for participant in self.participants:
            roll = participant.get_initiative_roll()
            if self.party_surprised and not participant.has_feat("Always Ready"):
                roll = max(0, roll - 5)
            initiative_rolls.append((roll, participant))
            self.log(f"{participant.character.name}: Initiative {roll}")
        initiative_rolls.sort(key=lambda x: x[0], reverse=True)
        self.turn_order = [p for _, p in initiative_rolls]
        self.log(f"\nTurn order: {', '.join(p.character.name for p in self.turn_order)}")
        self.round = 1
        if self.turn_order:
            self.turn_order[0].start_turn()
            if self.party_surprised:
                for p in self.participants:
                    if not p.has_feat("Always Ready"):
                        p.actions_remaining = max(0, p.actions_remaining - 1)
            self._log_map_state("Start of combat")

    def get_current_participant(self) -> Optional[CombatParticipant]:
        if not self.turn_order:
            return None
        return self.turn_order[self.current_turn_index]

    def advance_turn(self):
        self.current_turn_index += 1
        if self.current_turn_index >= len(self.turn_order):
            self.current_turn_index = 0
            self.round += 1
            self.log(f"\n=== Round {self.round} ===")
        nxt = self.get_current_participant()
        if nxt:
            nxt.start_turn()
            self._log_map_state(f"Start turn: {nxt.character.name}")

    def _ensure_weapon_ready(self, attacker: CombatParticipant, weapon: Weapon) -> bool:
        if weapon.draw_time > 0 and attacker.drawn_weapon != weapon.name:
            if not attacker.spend_actions(weapon.draw_time):
                self.log(f"{attacker.character.name} needs {weapon.draw_time} actions to draw {weapon.name}.")
                return False
            attacker.drawn_weapon = weapon.name
            self.log(f"{attacker.character.name} draws {weapon.name} (consumed {weapon.draw_time} action(s)).")
        if weapon.load_time > 0 and attacker.loaded_weapon != weapon.name:
            if not attacker.spend_actions(weapon.load_time):
                self.log(f"{attacker.character.name} needs {weapon.load_time} actions to load {weapon.name}.")
                return False
            attacker.loaded_weapon = weapon.name
            self.log(f"{attacker.character.name} loads {weapon.name} (consumed {weapon.load_time} action(s)).")
        return True

    def perform_attack(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Optional[Weapon] = None, accuracy_modifier: int = 0, is_dual_strike: bool = False, consume_actions: bool = True, ignore_quickfooted: bool = False, bypass_graze: bool = False, force_non_ap: bool = False, ignore_shieldmaster: bool = False, half_damage: bool = False, suppress_reactions: bool = False, allow_death_save_override: Optional[bool] = None) -> Dict[str, Any]:
        if weapon is None:
            weapon = attacker.weapon_main or AVALORE_WEAPONS["Unarmed"]
        allow_death_save = True if allow_death_save_override is None else allow_death_save_override
        if not self._ensure_can_act(attacker):
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
        if getattr(attacker, "sentinel_needs_lift", False) and weapon.name in {"Spear", "Polearm", "Javelin"}:
            if attacker.actions_remaining < 1:
                self.log(f"{attacker.character.name} needs 1 action to ready {weapon.name} after Sentinel and lacks the actions.")
                return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
            attacker.actions_remaining -= 1
            attacker.sentinel_needs_lift = False
            self.log(f"{attacker.character.name} spends 1 action to re-lift {weapon.name} after Sentinel.")
        attacker.last_hit_success = False
        if not self._ensure_weapon_ready(attacker, weapon):
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
        if getattr(self, "environment_underwater", False) and not weapon.usable_underwater:
            self.log(f"{weapon.name} cannot be used underwater.")
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
        if self.tactical_map and not self.is_in_range(attacker, defender, weapon):
            distance = self.get_distance(attacker, defender)
            self.log(f"{attacker.character.name} cannot attack - target is {distance} blocks away, weapon {weapon.name} requires {weapon.range_category.name} range!")
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
        cover = "none"
        if self.tactical_map:
            attacker_pos = attacker.position
            defender_pos = defender.position
            if not self.tactical_map.has_line_of_sight(attacker_pos, defender_pos):
                self.log(f"{attacker.character.name} has no line of sight to {defender.character.name}.")
                return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
            cover = self.tactical_map.cover_between(attacker_pos, defender_pos)
        dueling_bonus = 0
        if attacker.has_feat("Dueling Stance"):
            if weapon and not weapon.is_two_handed and attacker.weapon_offhand is None and attacker.shield is None:
                dueling_bonus = 1
        lineage_aim_bonus = 0
        attack_element: Optional[str] = None
        if attacker.has_feat("Lineage Weapon") and (attacker.lineage_weapon or attacker.lineage_weapon_alt):
            if weapon and (weapon.name == attacker.lineage_weapon or weapon.name == attacker.lineage_weapon_alt):
                lineage_aim_bonus = 1
                if attacker.has_feat("LW: Questing Bane") and defender and hasattr(defender, "creature_type"):
                    if defender.creature_type in attacker.slain_species:
                        lineage_aim_bonus = 2
                if attacker.active_lineage_element:
                    attack_element = attacker.active_lineage_element
        if consume_actions and not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions to attack with {weapon.name}.")
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
        self.log(f"\n{attacker.character.name} attacks {defender.character.name} with {weapon.name}")
        rakish_aim_bonus = 0
        if weapon.name == "Unarmed" and attacker.next_unarmed_bonus == "aim":
            rakish_aim_bonus = 1
        attack_roll, dice = roll_2d10()
        is_crit = (dice[0] == 10 and dice[1] == 10)
        total_attack = attack_roll + weapon.accuracy_bonus + accuracy_modifier + dueling_bonus + rakish_aim_bonus + lineage_aim_bonus
        total_attack += getattr(attacker, "temp_attack_bonus", 0)
        total_attack -= getattr(attacker, "mockery_penalty_total", 0)
        if defender.has_status(StatusEffect.HIDDEN) and not attacker.has_feat("Precise Senses"):
            total_attack -= 3
        if getattr(self, "environment_darkness", False) and not attacker.has_feat("Precise Senses"):
            total_attack -= 2
        weapon_ap = weapon.is_piercing()
        if force_non_ap:
            weapon_ap = False
        if weapon.load_time > 0:
            attacker.loaded_weapon = None
        if weapon.draw_time > 0:
            attacker.drawn_weapon = None
        if defender.has_feat("Parry") and defender.can_use_limited("Parry"):
            total_attack -= 2
            self.log(f"{defender.character.name} parries, reducing attack by 2 (now {total_attack}).")
        if cover != "none":
            cover_penalty = defender.cover_bonus(cover)
            total_attack -= cover_penalty
            self.log(f"Cover ({cover}) imposes -{cover_penalty} to attack. Adjusted total: {total_attack}")
        self.log(f"Attack roll: {dice} = {attack_roll} + {weapon.accuracy_bonus} (weapon) + {accuracy_modifier + dueling_bonus + lineage_aim_bonus + rakish_aim_bonus} (modifier) = {total_attack}")
        if is_crit:
            self.log("CRITICAL HIT!")
            damage = weapon.damage + (2 if weapon_ap else 0)
            actual_damage = defender.take_damage(damage, armor_piercing=True, allow_death_save=allow_death_save)
            self.log(f"Critical deals {damage} AP damage! Defender takes {actual_damage} damage.")
            attacker.last_hit_success = True
            if attacker.has_feat("LW: Questing Bane") and defender.is_dead and hasattr(defender, "creature_type"):
                attacker.slain_species.add(defender.creature_type)
            self._capture_snapshot(f"Crit: {attacker.character.name}", attacker, defender)
            return {"hit": True, "damage": actual_damage, "is_crit": True, "is_graze": False, "blocked": False, "element": attack_element}
        if defender.is_evading:
            evasion_roll, evasion_dice = roll_2d10()
            qf_bonus = 0 if ignore_quickfooted else defender.get_quickfooted_bonus(weapon, defender.shield)
            evasion_mod = defender.get_evasion_modifier() + qf_bonus
            total_evasion = evasion_roll + evasion_mod
            self.log(f"{defender.character.name} evades: {evasion_dice} = {evasion_roll} + {evasion_mod} (evasion mod) = {total_evasion}")
            if total_evasion >= total_attack:
                self.log(f"{defender.character.name} fully evades the attack!")
                d_wep = defender.weapon_main or defender.weapon_offhand
                if d_wep and defender.has_feat("Galestorm Stance") and d_wep.name in {"Greatsword", "Polearm", "Staff"}:
                    defender.evades_since_last_turn = getattr(defender, "evades_since_last_turn", 0) + 1
                if defender.has_feat("Quickfooted"):
                    self.apply_knockback(defender, 2, source_pos=attacker.position, source_name=defender.character.name)
                if defender.has_feat("Reactive Stance"):
                    self._reactive_maneuver(defender, attacker)
                if defender.flowing_stance and weapon.range_category in {RangeCategory.MELEE, RangeCategory.SKIRMISHING}:
                    alt_targets = [p for p in self.participants if p is not defender and p is not attacker and p.current_hp > 0]
                    if self.tactical_map:
                        alt_targets = [p for p in alt_targets if self.tactical_map.manhattan_distance(defender.position[0], defender.position[1], p.position[0], p.position[1]) <= 1]
                    if alt_targets:
                        alt = alt_targets[0]
                        redirect_weapon = defender.weapon_main or AVALORE_WEAPONS["Unarmed"]
                        redirect = self.perform_attack(defender, alt, weapon=redirect_weapon, accuracy_modifier=-2, consume_actions=False)
                        if redirect.get("hit"):
                            self.log(f"Patient Flow redirects the incoming strike to {alt.character.name}!")
                            self.perform_attack(attacker, alt, weapon=weapon, consume_actions=False, suppress_reactions=True)
                            self._capture_snapshot(f"Redirected: {attacker.character.name}", attacker, defender)
                            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False, "element": attack_element}
                if not suppress_reactions and not getattr(defender, "reactive_maneuver_used", False):
                    self.maybe_riposte(defender, attacker)
                self._capture_snapshot(f"Evaded: {attacker.character.name}", attacker, defender)
                return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False, "element": attack_element}
            elif total_evasion >= 12:
                self.log(f"Grazing hit! Attack partially connects.")
                can_parry = False
                parry_weapon = defender.weapon_main
                if defender.has_feat("Dueling Stance") and parry_weapon and not parry_weapon.is_two_handed and defender.weapon_offhand is None and defender.shield is None:
                    if parry_weapon.name in {"Dagger", "Rapier", "Arming Sword"}:
                        in_range = True
                        if self.tactical_map:
                            dist = self.tactical_map.manhattan_distance(defender.position[0], defender.position[1], attacker.position[0], attacker.position[1])
                            in_range = dist <= 1
                        can_parry = in_range
                if can_parry:
                    parry_roll, pr_dice = roll_2d10()
                    is_parry_crit = (pr_dice[0] == 10 and pr_dice[1] == 10)
                    parry_total = parry_roll + parry_weapon.accuracy_bonus - 1
                    self.log(f"{defender.character.name} attempts a Parry! Roll {pr_dice} -> {parry_total}")
                    if parry_total >= 12 or is_parry_crit:
                        defender.parry_bonus_next_turn = True
                        self.log(f"Parry successful! Grazing hit deflected. {defender.character.name} gains +1 damage on next turn while single-wielding.")
                        self._capture_snapshot(f"Parry: {attacker.character.name}", attacker, defender)
                        return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False}
                if defender.has_feat("Evasive Tactics") and defender.is_critical and not defender.graze_buffer_used:
                    defender.suppress_death_save_once = True
                    defender.graze_buffer_used = True
                if bypass_graze or ("grazing" in weapon.traits):
                    damage = weapon.damage
                    self.log(f"Weapon trait overrides graze reduction. Full damage applies.")
                elif defender.armor and defender.armor.category in [ArmorCategory.MEDIUM, ArmorCategory.HEAVY]:
                    damage = weapon.damage
                    self.log(f"Heavy armor prevents damage reduction. Full damage applies.")
                else:
                    damage = (weapon.damage + 1) // 2
                    self.log(f"Light armor allows partial dodge. Damage halved to {damage}.")
                actual_damage = defender.take_damage(damage, armor_piercing=weapon_ap, allow_death_save=allow_death_save)
                self.log(f"Defender takes {actual_damage} damage after armor.")
                attacker.last_hit_success = True
                if attacker.has_feat("LW: Questing Bane") and defender.is_dead and hasattr(defender, "creature_type"):
                    attacker.slain_species.add(defender.creature_type)
                if weapon.name == "Unarmed" and attacker.has_feat("Rakish Combination"):
                    str_ath = attacker.character.get_modifier("Strength", "Athletics")
                    base_unarmed = 2 + (3 if str_ath >= 5 else 2 if str_ath >= 3 else 1 if str_ath >= 1 else 0)
                    attacker.next_unarmed_bonus = "aim" if base_unarmed >= 4 else "damage"
                self._capture_snapshot(f"Graze: {attacker.character.name}", attacker, defender)
                return {"hit": True, "damage": actual_damage, "is_crit": False, "is_graze": True, "blocked": False, "element": attack_element}
            else:
                self.log(f"Evasion failed (below 12). Attack proceeds normally.")
        if defender.is_blocking and defender.shield:
            is_ranged = weapon.range_category == RangeCategory.RANGED
            extra_block_bonus = 0
            if defender.has_feat("Shieldmaster") and not ignore_shieldmaster:
                melee_bonus_weapons = {
                    "Unarmed", "Arming Sword", "Dagger", "Rapier", "Mace", "Spear", "Polearm",
                    "Whip", "Meteor Hammer", "Throwing Knife", "Staff", "Recurve Bow"
                }
                if weapon.name in melee_bonus_weapons:
                    extra_block_bonus += 3
                if is_ranged:
                    extra_block_bonus += 1
            if is_ranged and self._has_shield_wall(defender):
                extra_block_bonus += 1
            block_roll, block_success = defender.shield.roll_block(is_ranged_attack=is_ranged, extra_bonus=extra_block_bonus - getattr(defender, "mockery_penalty_total", 0))
            self.log(f"{defender.character.name} attempts block: {block_roll} vs DC 12")
            if block_success:
                self.log(f"{defender.character.name} blocks the attack with their shield!")
                if not suppress_reactions:
                    self.maybe_shield_bash(defender, attacker)
                self._capture_snapshot(f"Blocked: {attacker.character.name}", attacker, defender)
                return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": True, "element": attack_element}
            else:
                self.log(f"Block failed. Attack proceeds.")
        if total_attack < 12:
            self.log(f"Attack misses (total {total_attack} < 12)")
            if attacker.has_feat("Backline Flanker") and attacker.has_status(StatusEffect.HIDDEN):
                attacker.ignore_next_conceal_penalty = True
                self.log(f"Backline Flanker: next Conceal ignores -3 penalty.")
            if attacker.parry_damage_bonus_active:
                attacker.parry_damage_bonus_active = False
            self._capture_snapshot(f"Miss: {attacker.character.name}", attacker, defender)
            return {"hit": False, "damage": 0, "is_crit": False, "is_graze": False, "blocked": False, "element": attack_element}
        self.log(f"Attack hits!")
        if defender.has_status(StatusEffect.VULNERABLE) and weapon.range_category == RangeCategory.MELEE:
            self.log(f"Target is vulnerable to melee: +1 aim applied.")
        effective_ap = weapon_ap
        if defender.shield and defender.shield.grants_ap_immunity and defender.is_blocking:
            if effective_ap:
                self.log(f"Large shield negates armor piercing!")
                effective_ap = False
        base_damage = weapon.damage + dueling_bonus
        parry_bonus_consumed = False
        if attacker.parry_damage_bonus_active and weapon and not weapon.is_two_handed and attacker.weapon_offhand is None and attacker.shield is None and weapon.name in {"Dagger", "Rapier", "Arming Sword"}:
            base_damage += 1
            parry_bonus_consumed = True
        if half_damage:
            base_damage = (base_damage + 1) // 2
        if attacker.has_feat("Aberration Slayer") and defender and hasattr(defender, "creature_type"):
            chosen = getattr(attacker, "aberration_slayer_type", None)
            if chosen and defender.creature_type == chosen:
                base_damage += 1
        if weapon.name == "Unarmed":
            str_athletics = attacker.character.get_modifier("Strength", "Athletics")
            if str_athletics >= 5:
                base_damage += 3
            elif str_athletics >= 3:
                base_damage += 2
            elif str_athletics >= 1:
                base_damage += 1
        if "vs_unarmored_bonus" in weapon.traits:
            if not defender.armor or defender.armor.category == ArmorCategory.NONE:
                base_damage += 1
                self.log(f"+1 damage vs unarmored target.")
        if "vs_medium_heavy_bonus" in weapon.traits:
            if defender.armor and defender.armor.category in [ArmorCategory.MEDIUM, ArmorCategory.HEAVY]:
                base_damage += 2
                self.log(f"+2 damage vs medium/heavy armor.")
        if "no_heavy_armor_damage" in weapon.traits:
            if defender.armor and defender.armor.category == ArmorCategory.HEAVY:
                base_damage = 0
                self.log(f"Whip cannot penetrate heavy armor - no damage!")
        if attacker.has_feat("Control") and id(defender) in getattr(attacker, "control_wall_bonus_targets", set()):
            base_damage += 1
            self.log("Control: wall pressure grants +1 damage.")
        if weapon.name == "Unarmed" and attacker.next_unarmed_bonus == "damage":
            base_damage = 4
        actual_damage = defender.take_damage(base_damage, armor_piercing=effective_ap, allow_death_save=allow_death_save)
        self.log(f"Weapon deals {base_damage} damage. Defender takes {actual_damage} after armor.")
        if parry_bonus_consumed:
            attacker.parry_damage_bonus_active = False
        if weapon.name == "Unarmed" and attacker.next_unarmed_bonus:
            attacker.next_unarmed_bonus = None
        if weapon.name == "Unarmed" and attacker.has_feat("Rakish Combination") and actual_damage > 0:
            str_ath = attacker.character.get_modifier("Strength", "Athletics")
            base_unarmed = 2 + (3 if str_ath >= 5 else 2 if str_ath >= 3 else 1 if str_ath >= 1 else 0)
            attacker.next_unarmed_bonus = "aim" if base_unarmed >= 4 else "damage"
        if self.tactical_map and attacker.has_feat("Strategic Archer") and weapon.range_category == RangeCategory.RANGED:
            ax, ay = attacker.position
            dx, dy = defender.position
            atile = self.tactical_map.get_tile(ax, ay)
            dtile = self.tactical_map.get_tile(dx, dy)
            if atile and dtile and (atile.height - dtile.height) >= 3:
                bonus = defender.take_damage(1, armor_piercing=effective_ap, allow_death_save=allow_death_save)
                actual_damage += bonus
                self.log(f"Strategic Archer: high ground bonus +1 damage applied.")
        if attacker.has_feat("Control"):
            control_weapons = {"Spear", "Polearm", "Greatsword", "Large Shield"}
            if weapon.name in control_weapons:
                wall_blocked = self._apply_control_push(attacker, defender, 4)
                if wall_blocked:
                    attacker.control_wall_bonus_targets.add(id(defender))
                    self.log("Control: target is pinned against a wall; +1 damage on subsequent attacks this turn.")
        if attacker.has_feat("Backline Flanker") and attacker.has_status(StatusEffect.HIDDEN) and self.tactical_map:
            dx, dy = defender.position
            ally_adjacent = False
            for nx, ny in self.tactical_map.get_neighbors(dx, dy):
                tile = self.tactical_map.get_tile(nx, ny)
                if tile and isinstance(tile.occupant, CombatParticipant):
                    other = tile.occupant
                    if other is not attacker and other is not defender:
                        ally_adjacent = True
                        break
            if ally_adjacent:
                bonus = defender.take_damage(1, armor_piercing=effective_ap, allow_death_save=allow_death_save)
                actual_damage += bonus
                self.log(f"Backline Flanker: +1 damage applied for flanking from hidden.")
        if attacker.has_feat("Mighty Strike"):
            mighty_weapons = {
                "Greatsword", "Greataxe", "Sling", "Staff", "Crossbow", "Mace", "Large Shield", "Unarmed"
            }
            if weapon.name in mighty_weapons:
                self.apply_knockback(defender, 3, source_pos=attacker.position, source_name=attacker.character.name)
        if attacker.has_feat("Forward Charge") and weapon.name in {"Greatsword", "Polearm", "Staff"}:
            attacker.forward_charge_ready = True
            self.log(f"Forward Charge primed: next Topple/Shove cannot be evaded or blocked.")
        attacker.last_hit_success = True
        if attacker.has_feat("LW: Questing Bane") and defender.is_dead and hasattr(defender, "creature_type"):
            attacker.slain_species.add(defender.creature_type)
        self._capture_snapshot(f"Hit: {attacker.character.name}", attacker, defender)
        return {"hit": True, "damage": actual_damage, "is_crit": False, "is_graze": False, "blocked": False, "element": attack_element}

    def maybe_riposte(self, defender: CombatParticipant, attacker: CombatParticipant):
        if not defender.has_feat("Riposte"):
            return
        if defender.is_dead or defender.current_hp <= 0:
            return
        weapon = defender.weapon_main or AVALORE_WEAPONS["Unarmed"]
        allowed = {"Dagger", "Arming Sword", "Rapier", "Unarmed"}
        if weapon.name not in allowed:
            return
        attack_roll, dice = roll_2d10()
        is_crit = (dice[0] == 10 and dice[1] == 10)
        total_attack = attack_roll + weapon.accuracy_bonus - 1
        self.log(f"{defender.character.name} attempts a Riposte! Roll {dice} -> {total_attack}")
        if total_attack < 12 and not is_crit:
            self.log("Riposte misses.")
            return
        damage = weapon.damage
        allow_ds = not (defender.has_feat("Evasive Tactics") and attacker.is_critical)
        actual = attacker.take_damage(damage, armor_piercing=weapon.is_piercing(), allow_death_save=allow_ds)
        self.log(f"Riposte hits for {actual} damage (cannot be evaded or blocked).")

    def maybe_shield_bash(self, defender: CombatParticipant, attacker: CombatParticipant):
        if not defender.has_feat("Shield Bash"):
            return
        if defender.is_dead or defender.current_hp <= 0:
            return
        if not defender.shield:
            return
        if defender.shield.shield_type == ShieldType.SMALL:
            shield_weapon = AVALORE_WEAPONS.get("Small Shield")
        else:
            shield_weapon = AVALORE_WEAPONS.get("Large Shield")
        if not shield_weapon:
            return
        if defender.has_feat("Sentinel") and defender.weapon_main and defender.weapon_main.name in {"Spear", "Polearm", "Javelin"}:
            if not defender.sentinel_retaliation_used_round:
                defender.sentinel_retaliation_used_round = True
                defender.sentinel_needs_lift = True
                attack_weapon = defender.weapon_main
                wall_bonus = 1 if self._has_shield_wall(defender) else 0
                self.log(f"{defender.character.name} uses Sentinel to retaliate with {attack_weapon.name}!")
                result = self.perform_attack(defender, attacker, weapon=attack_weapon, accuracy_modifier=wall_bonus, consume_actions=False, suppress_reactions=True)
                return
        attack_weapon = shield_weapon
        if self._has_shield_wall(defender):
            bash_wall_bonus = 1
        else:
            bash_wall_bonus = 0
        bash_bonus = 0
        if defender.has_feat("Bastion Stance") and hasattr(defender, 'bastion_active') and defender.bastion_active:
            bash_bonus = 1
        if defender.has_feat("Forward Charge") and self.tactical_map:
            self._move_toward(defender, attacker.position, 3)
        attack_roll, dice = roll_2d10()
        is_crit = (dice[0] == 10 and dice[1] == 10)
        total_attack = attack_roll + attack_weapon.accuracy_bonus + bash_bonus + bash_wall_bonus
        self.log(f"{defender.character.name} attempts Shield Bash! Roll {dice} -> {total_attack}")
        if total_attack < 12 and not is_crit:
            self.log("Shield Bash misses.")
            return
        damage = attack_weapon.damage
        allow_ds = not (defender.has_feat("Evasive Tactics") and attacker.is_critical)
        actual = attacker.take_damage(damage, armor_piercing=attack_weapon.is_piercing(), allow_death_save=allow_ds)
        self.log(f"Shield Bash hits for {actual} damage (cannot be evaded or blocked).")
        if defender.has_feat("Bastion Stance") and hasattr(defender, 'bastion_active') and defender.bastion_active:
            attacker.apply_status(StatusEffect.PRONE)
            attacker.status_durations[StatusEffect.PRONE] = 1
            self.log(f"Bastion Stance: {attacker.character.name} is knocked prone.")
            self.log(f"Bastion Stance: {attacker.character.name} is knocked prone!")

    def _has_shield_wall(self, actor: CombatParticipant) -> bool:
        if not self.tactical_map or not actor.shield or actor.shield.shield_type != ShieldType.LARGE:
            return False
        if not actor.has_feat("Shield Wall"):
            return False
        ax, ay = actor.position
        for nx, ny in self.tactical_map.get_neighbors(ax, ay):
            tile = self.tactical_map.get_tile(nx, ny)
            if not tile or not isinstance(tile.occupant, CombatParticipant):
                continue
            ally = tile.occupant
            if ally is actor:
                continue
            if ally.shield and ally.shield.shield_type == ShieldType.LARGE and ally.has_feat("Shield Wall"):
                return True
        return False

    def _move_toward(self, actor: CombatParticipant, target_pos: Tuple[int, int], blocks: int) -> None:
        if not self.tactical_map:
            return
        ax, ay = actor.position
        tx, ty = target_pos
        dx = 1 if tx > ax else (-1 if tx < ax else 0)
        dy = 1 if ty > ay else (-1 if ty < ay else 0)
        final_x, final_y = ax, ay
        for i in range(1, blocks + 1):
            nx = ax + dx * i
            ny = ay + dy * i
            if not self.tactical_map.is_passable(nx, ny, actor):
                break
            final_x, final_y = nx, ny
        if (final_x, final_y) != (ax, ay):
            self.tactical_map.clear_occupant(ax, ay)
            actor.position = (final_x, final_y)
            self.tactical_map.set_occupant(final_x, final_y, actor)
            self.log(f"{actor.character.name} advances {abs(final_x-ax)+abs(final_y-ay)} blocks toward target.")

    def perform_cast_spell(self, caster: CombatParticipant, spell: Spell, target: Optional[CombatParticipant] = None) -> Dict[str, Any]:
        self.log(f"\n{caster.character.name} casts {spell.name}")
        can_cast_normally = spell.can_cast(caster)
        is_overcast = False
        if not can_cast_normally:
            if caster.has_overcast_today:
                self.log(f"Cannot overcast - already overcast today!")
                return {"success": False, "miscast": False, "overcast": False}
            if caster.max_anima < spell.anima_cost:
                self.log(f"Cannot overcast - spell cost exceeds max Anima!")
                return {"success": False, "miscast": False, "overcast": False}
            self.log(f"OVERCASTING! (Anima: {caster.anima}/{caster.max_anima})")
            is_overcast = True
            caster.has_overcast_today = True
        cast_roll, dice = roll_2d10()
        arcana_mod = caster.character.get_modifier("Harmony", "Arcana")
        total = cast_roll + arcana_mod
        penalty = getattr(caster, "mockery_penalty_total", 0) + getattr(caster, "spell_penalty_total", 0)
        if getattr(self, "environment_darkness", False) and not caster.has_feat("Precise Senses"):
            penalty += 2
        if target and target.has_status(StatusEffect.HIDDEN) and not caster.has_feat("Precise Senses"):
            penalty += 3
        total -= penalty
        self.log(f"Casting roll: {dice} = {cast_roll} + {arcana_mod} (HAR:Arcana) - {penalty} (penalties) = {total} vs DC {spell.casting_dc}")
        if total < spell.casting_dc:
            self.log(f"MISCAST! Spell fails.")
            if is_overcast:
                self.log(f"Overcast miscast! {caster.character.name} is knocked unconscious!")
                caster.current_hp = 0
                caster.is_critical = True
                caster.anima = 0
            else:
                lost_anima = spell.anima_cost // 2
                caster.anima = max(0, caster.anima - lost_anima)
                self.log(f"Lost {lost_anima} Anima (half cost).")
            return {"success": False, "miscast": True, "overcast": is_overcast, "damage": 0, "healing": 0}
        self.log(f"Spell succeeds!")
        if not is_overcast:
            caster.anima -= spell.anima_cost
            self.log(f"Anima: {caster.anima}/{caster.max_anima}")
        else:
            consequence_roll = roll_1d6()
            self.log(f"Overcast consequence roll: {consequence_roll}")
            if consequence_roll <= 2:
                self.log(f"Severe consequence! {caster.character.name} suffers permanent scarring or is knocked down.")
            elif consequence_roll <= 4:
                self.log(f"Moderate consequence! Fatigue or temporary debuff.")
            else:
                self.log(f"Mild consequence! Ringing ears or numb hands.")
        result = {"success": True, "miscast": False, "overcast": is_overcast, "damage": 0, "healing": 0}
        if spell.damage > 0 and target:
            if spell.requires_attack_roll:
                attack_result = self.perform_attack(caster, target, weapon=None)
                if attack_result["hit"]:
                    actual_damage = target.take_damage(spell.damage, armor_piercing=True)
                    self.log(f"{spell.name} deals {spell.damage} damage to {target.character.name}!")
                    result["damage"] = actual_damage
            else:
                actual_damage = target.take_damage(spell.damage, armor_piercing=True)
                self.log(f"{spell.name} deals {spell.damage} damage to {target.character.name}!")
                result["damage"] = actual_damage
        if spell.healing > 0 and target:
            target.heal(spell.healing)
            self.log(f"{spell.name} heals {spell.healing} HP to {target.character.name}! (HP: {target.current_hp}/{target.max_hp})")
            result["healing"] = spell.healing
        return result

    def _ensure_can_act(self, actor: CombatParticipant) -> bool:
        if actor.current_hp > 0 or not actor.is_critical:
            return True
        if actor.has_feat("Death's Dance") and not actor.free_action_while_critical_used:
            actor.free_action_while_critical_used = True
            return True
        actor.resolve_death_save()
        if actor.is_dead:
            self.log(f"{actor.character.name} succumbs while attempting to act.")
            return False
        return True

    def _threatens(self, reactor: CombatParticipant, target_pos: Tuple[int, int]) -> bool:
        if reactor.is_dead or reactor.current_hp <= 0:
            return False
        weapon = reactor.weapon_main or reactor.weapon_offhand
        if weapon is None:
            return False
        if not self.tactical_map:
            return False
        dist = self.tactical_map.manhattan_distance(reactor.position[0], reactor.position[1], target_pos[0], target_pos[1])
        reach = getattr(weapon, "reach", 1)
        if "reach" in weapon.traits:
            reach = max(reach, 2)
        if reactor.has_feat("Steadfast Defender"):
            reach = max(reach, 2)
        return dist <= reach

    def _maybe_opportunity_attacks(self, mover: CombatParticipant, dest: Tuple[int, int]):
        if not self.tactical_map:
            return
        start = mover.position
        for other in self.participants:
            if other is mover:
                continue
            if not self._threatens(other, start):
                continue
            if self._threatens(other, dest):
                continue
            acc_mod = 0
            if other.has_feat("Steadfast Defender"):
                if self._has_shield_wall(other):
                    acc_mod = 1
            self.log(f"{other.character.name} makes an opportunity attack on {mover.character.name}!")
            self.perform_attack(other, mover, weapon=other.weapon_main, consume_actions=False, accuracy_modifier=acc_mod)

    def action_evade(self, actor: CombatParticipant) -> bool:
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} has no actions left to Evade.")
            return False
        actor.is_evading = True
        self.log(f"{actor.character.name} prepares to Evade incoming attacks.")
        return True

    def action_move(self, actor: CombatParticipant, dest_x: int, dest_y: int) -> bool:
        if not self._ensure_can_act(actor):
            return False
        if actor.free_move_used:
            self.log(f"{actor.character.name} has already used free movement this turn.")
            return False
        if not self.tactical_map:
            self.log("No tactical map available for movement.")
            return False
        base_movement = 5
        movement_penalty = 0
        if actor.armor:
            movement_penalty = actor.armor.movement_penalty_for(actor.character)
        if actor.has_status(StatusEffect.SLOWED):
            movement_penalty -= 2
        movement_allowance = max(0, base_movement + movement_penalty)
        start_x, start_y = actor.position
        path = self.tactical_map.find_path(start_x, start_y, dest_x, dest_y, actor)
        if not path:
            self.log(f"{actor.character.name} cannot find path to ({dest_x}, {dest_y}).")
            return False
        total_cost = 0
        for i in range(1, len(path)):
            x, y = path[i]
            tile = self.tactical_map.get_tile(x, y)
            if tile:
                total_cost += tile.move_cost
        if total_cost > movement_allowance:
            self.log(f"{actor.character.name} cannot reach ({dest_x}, {dest_y}) - needs {total_cost} movement, has {movement_allowance}.")
            return False
        if actor.whirling_devil_active:
            cx, cy = start_x, start_y
            self.tactical_map.clear_occupant(cx, cy)
            for i in range(1, len(path)):
                nx, ny = path[i]
                self._maybe_opportunity_attacks(actor, (nx, ny))
                actor.position = (nx, ny)
                self.tactical_map.set_occupant(nx, ny, actor)
                self._trigger_whirling_strikes(actor)
                if i < len(path) - 1:
                    self.tactical_map.clear_occupant(nx, ny)
            self.tactical_map.set_occupant(dest_x, dest_y, actor)
        else:
            self._maybe_opportunity_attacks(actor, (dest_x, dest_y))
            self.tactical_map.clear_occupant(start_x, start_y)
            actor.position = (dest_x, dest_y)
            self.tactical_map.set_occupant(dest_x, dest_y, actor)
        actor.free_move_used = True
        self.log(f"{actor.character.name} uses free movement from ({start_x}, {start_y}) to ({dest_x}, {dest_y}) (cost: {total_cost}).")
        self._capture_snapshot(f"Move: {actor.character.name}", actor, None)
        return True

    def action_dash(self, actor: CombatParticipant, dest_x: int, dest_y: int) -> bool:
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} needs 1 action to Dash.")
            return False
        if not self.tactical_map:
            self.log("No tactical map available for movement.")
            return False
        base_movement = 5
        movement_penalty = 0
        if actor.armor:
            movement_penalty = actor.armor.movement_penalty_for(actor.character)
        if actor.has_status(StatusEffect.SLOWED):
            movement_penalty -= 2
        base_allowance = max(0, base_movement + movement_penalty)
        dash_bonus = 4
        movement_allowance = dash_bonus if actor.free_move_used else base_allowance + dash_bonus
        start_x, start_y = actor.position
        path = self.tactical_map.find_path(start_x, start_y, dest_x, dest_y, actor)
        if not path:
            self.log(f"{actor.character.name} cannot find path to ({dest_x}, {dest_y}).")
            return False
        total_cost = 0
        for i in range(1, len(path)):
            x, y = path[i]
            tile = self.tactical_map.get_tile(x, y)
            if tile:
                total_cost += tile.move_cost
        if total_cost > movement_allowance:
            self.log(f"{actor.character.name} cannot reach ({dest_x}, {dest_y}) - needs {total_cost} movement, has {movement_allowance}.")
            return False
        if actor.whirling_devil_active:
            cx, cy = start_x, start_y
            self.tactical_map.clear_occupant(cx, cy)
            for i in range(1, len(path)):
                nx, ny = path[i]
                self._maybe_opportunity_attacks(actor, (nx, ny))
                actor.position = (nx, ny)
                self.tactical_map.set_occupant(nx, ny, actor)
                self._trigger_whirling_strikes(actor)
                if i < len(path) - 1:
                    self.tactical_map.clear_occupant(nx, ny)
            self.tactical_map.set_occupant(dest_x, dest_y, actor)
        else:
            self._maybe_opportunity_attacks(actor, (dest_x, dest_y))
            self.tactical_map.clear_occupant(start_x, start_y)
            actor.position = (dest_x, dest_y)
            self.tactical_map.set_occupant(dest_x, dest_y, actor)
        actor.dashed_this_turn = True
        actor.free_move_used = True
        self.log(f"{actor.character.name} dashes from ({start_x}, {start_y}) to ({dest_x}, {dest_y}) (cost: {total_cost}).")
        self._capture_snapshot(f"Dash: {actor.character.name}", actor, None)
        return True

    def action_whirling_devil(self, actor: CombatParticipant) -> bool:
        if not actor.has_feat("Whirling Devil"):
            return False
        if not actor.take_limited_action():
            return False
        if not self._ensure_can_act(actor):
            return False
        actor.whirling_devil_active = True
        self.log(f"{actor.character.name} activates Whirling Devil: striking adjacent foes while moving.")
        return True

    def _trigger_whirling_strikes(self, actor: CombatParticipant) -> None:
        if not self.tactical_map:
            return
        weapon = actor.weapon_main or actor.weapon_offhand or AVALORE_WEAPONS["Unarmed"]
        ax, ay = actor.position
        seen: Set[CombatParticipant] = getattr(self, "_whirling_hit_set", set())
        for nx, ny in self.tactical_map.get_neighbors(ax, ay):
            tile = self.tactical_map.get_tile(nx, ny)
            if not tile or not isinstance(tile.occupant, CombatParticipant):
                continue
            target = tile.occupant
            if target is actor:
                continue
            if target in seen:
                continue
            res = self.perform_attack(actor, target, weapon=weapon, accuracy_modifier=-1, consume_actions=False, half_damage=(weapon.actions_required == 2))
            seen.add(target)
        self._whirling_hit_set = seen

    def action_vault(self, actor: CombatParticipant, dest_x: int, dest_y: int) -> bool:
        if not actor.has_feat("Combat Acrobat"):
            return False
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} needs 1 action to Vault.")
            return False
        if not self.tactical_map:
            return False
        base_movement = 5
        movement_penalty = 0
        if actor.armor:
            movement_penalty = actor.armor.movement_penalty_for(actor.character)
        if actor.has_status(StatusEffect.SLOWED):
            movement_penalty -= 2
        movement_allowance = (base_movement + movement_penalty) * 2
        start_x, start_y = actor.position
        path = self.tactical_map.find_path(start_x, start_y, dest_x, dest_y, actor)
        if not path:
            self.log(f"{actor.character.name} cannot find path to ({dest_x}, {dest_y}).")
            return False
        total_cost = 0
        for i in range(1, len(path)):
            x, y = path[i]
            tile = self.tactical_map.get_tile(x, y)
            if tile:
                total_cost += tile.move_cost
        if total_cost > movement_allowance:
            self.log(f"{actor.character.name} cannot reach ({dest_x}, {dest_y}) - needs {total_cost} movement, has {movement_allowance}.")
            return False
        self._maybe_opportunity_attacks(actor, (dest_x, dest_y))
        self.tactical_map.clear_occupant(start_x, start_y)
        actor.position = (dest_x, dest_y)
        self.tactical_map.set_occupant(dest_x, dest_y, actor)
        actor.is_evading = True
        self.log(f"{actor.character.name} vaults to ({dest_x}, {dest_y}) and prepares to Evade.")
        self._capture_snapshot(f"Vault: {actor.character.name}", actor, None)
        return True

    def action_momentum_strike(self, attacker: CombatParticipant, defender: CombatParticipant) -> Dict[str, Any]:
        if not attacker.has_feat("Momentum"):
            return {"used": False}
        if not attacker.dashed_this_turn:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        weapon = AVALORE_WEAPONS["Unarmed"]
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Momentum Strike.")
            return {"used": False}
        res = self.perform_attack(attacker, defender, weapon=weapon)
        if res.get("hit"):
            bonus = defender.take_damage(2, armor_piercing=False)
            res["damage"] += bonus
            self.log(f"Momentum adds +2 damage.")
        attacker.take_damage(1, armor_piercing=True)
        self.log(f"{attacker.character.name} suffers 1 AP damage from exertion.")
        return {"used": True, "result": res}

    def action_feint(self, attacker: CombatParticipant, defender: CombatParticipant) -> Dict[str, Any]:
        if not attacker.has_feat("Feint"):
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Feint.")
            return {"used": False}
        weapon = AVALORE_WEAPONS["Unarmed"]
        res = self.perform_attack(attacker, defender, weapon=weapon, ignore_quickfooted=True, ignore_shieldmaster=True)
        return {"used": True, "result": res}

    def action_rousing_inspiration(self, actor: CombatParticipant) -> Dict[str, Any]:
        if not actor.has_feat("Rousing Inspiration"):
            return {"used": False}
        if not actor.take_limited_action():
            return {"used": False}
        if not self._ensure_can_act(actor):
            return {"used": False}
        if not actor.spend_actions(1):
            return {"used": False}
        granted = 0
        if not self.tactical_map:
            return {"used": False}
        ax, ay = actor.position
        for p in self.participants:
            if p is actor or p.current_hp <= 0:
                continue
            px, py = p.position
            dist = self.tactical_map.manhattan_distance(ax, ay, px, py)
            if 2 <= dist <= 8 and not p.inspired_scene:
                temp = max(0, actor.character.get_modifier("Harmony", "Belief") + 2)
                p.temp_hp += temp
                p.inspired_scene = True
                granted += 1
                self.log(f"Rousing Inspiration: {p.character.name} gains {temp} temporary HP.")
        return {"used": True, "granted": granted}

    def action_commanding_inspiration(self, actor: CombatParticipant) -> Dict[str, Any]:
        if not actor.has_feat("Commanding Inspiration"):
            return {"used": False}
        if not actor.take_limited_action():
            return {"used": False}
        if not self._ensure_can_act(actor):
            return {"used": False}
        if not actor.spend_actions(1):
            return {"used": False}
        granted = 0
        for p in self.participants:
            if p is actor or p.current_hp <= 0:
                continue
            p.temp_attack_bonus = min(2, p.temp_attack_bonus + 1)
            granted += 1
        self.log(f"Commanding Inspiration: allies gain +1 aim (stacking).")
        return {"used": True, "granted": granted}

    def action_set_aberration_target(self, actor: CombatParticipant, creature_type: str) -> bool:
        if not actor.has_feat("Aberration Slayer"):
            return False
        actor.aberration_slayer_type = creature_type
        self.log(f"{actor.character.name} vows vengeance against {creature_type}.")
        return True

    def action_piercing_strike(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Piercing Strike"):
            return {"used": False}
        if weapon.name not in {"Arming Sword", "Dagger"}:
            return {"used": False}
        if not attacker.take_limited_action():
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            return {"used": False}
        ap = True
        dmg_bonus = 0
        if defender.shield and defender.shield.grants_ap_immunity and defender.is_blocking:
            ap = False
            dmg_bonus = 1
        res = self.perform_attack(attacker, defender, weapon=weapon)
        if res.get("hit"):
            dmg = weapon.damage + dmg_bonus
            applied = defender.take_damage(dmg, armor_piercing=ap)
            res["damage"] = applied
            self.log(f"Piercing Strike deals {applied} damage (AP={ap}).")
        attacker.apply_status(StatusEffect.VULNERABLE)
        attacker.status_durations[StatusEffect.VULNERABLE] = 1
        self.log(f"{attacker.character.name} is vulnerable: attacks against them gain +1 until next turn.")
        return {"used": True, "result": res}

    def action_hilt_strike(self, attacker: CombatParticipant, defender: CombatParticipant, base_weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Hilt Strike"):
            return {"used": False}
        if not base_weapon or not base_weapon.is_two_handed:
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Hilt Strike.")
            return {"used": False}
        half_damage = (base_weapon.damage + 1) // 2
        hilt_weapon = Weapon(name="Hilt Strike", damage=half_damage, accuracy_bonus=base_weapon.accuracy_bonus, actions_required=1, range_category=base_weapon.range_category, is_two_handed=base_weapon.is_two_handed, armor_piercing=False, traits=list(set(base_weapon.traits + ["grazing"])) )
        result = self.perform_attack(attacker, defender, weapon=hilt_weapon, accuracy_modifier=0, consume_actions=False, ignore_quickfooted=True, bypass_graze=True, force_non_ap=True)
        if result.get("hit") and attacker.has_feat("Mighty Strike"):
            self.apply_knockback(defender, 3, source_pos=attacker.position, source_name=attacker.character.name)
        return {"used": True, "result": result}

    def action_rangers_gambit(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Ranger's Gambit"):
            return {"used": False}
        if weapon.name not in {"Recurve Bow", "Longbow"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if self.tactical_map:
            dist = self.tactical_map.manhattan_distance(attacker.position[0], attacker.position[1], defender.position[0], defender.position[1])
            if dist > 1:
                self.log(f"{attacker.character.name} is not at melee distance for Ranger's Gambit.")
                return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Ranger's Gambit.")
            return {"used": False}
        if not self._ensure_weapon_ready(attacker, weapon):
            return {"used": False}
        ap_weapon = Weapon(name=weapon.name, damage=weapon.damage, accuracy_bonus=weapon.accuracy_bonus, actions_required=1, range_category=weapon.range_category, is_two_handed=weapon.is_two_handed, armor_piercing=True, traits=list(set(weapon.traits + ["grazing"])) )
        result = self.perform_attack(attacker, defender, weapon=ap_weapon, accuracy_modifier=-2, consume_actions=False, bypass_graze=True)
        if result.get("hit"):
            self.apply_knockback(defender, 3, source_pos=attacker.position, source_name=attacker.character.name)
        attacker.apply_status(StatusEffect.VULNERABLE)
        attacker.status_durations[StatusEffect.VULNERABLE] = 1
        self.log(f"{attacker.character.name} exposes themselves: melee attacks gain +1 aim against them until next turn.")
        return {"used": True, "result": result}

    def action_shove(self, attacker: CombatParticipant, defender: CombatParticipant) -> Dict[str, Any]:
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions to Shove.")
            return {"used": False}
        roll, dice = roll_2d10()
        atk_mod = attacker.character.get_modifier("Strength", "Athletics")
        total = roll + atk_mod
        unstoppable = attacker.forward_charge_ready
        success = total >= 12
        self.log(f"Shove roll {dice} -> {total} (unstoppable={unstoppable})")
        if success:
            if unstoppable:
                self._apply_knockback_force(defender, 1, attacker.position, attacker.character.name)
                self._move_toward(attacker, defender.position, 3)
                attacker.forward_charge_ready = False
            else:
                self.apply_knockback(defender, 1, source_pos=attacker.position, source_name=attacker.character.name)
            return {"used": True, "success": True}
        else:
            return {"used": True, "success": False}

    def action_topple(self, attacker: CombatParticipant, defender: CombatParticipant) -> Dict[str, Any]:
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions to Topple.")
            return {"used": False}
        roll, dice = roll_2d10()
        atk_mod = attacker.character.get_modifier("Strength", "Athletics")
        total = roll + atk_mod
        unstoppable = attacker.forward_charge_ready
        success = total >= 12
        self.log(f"Topple roll {dice} -> {total} (unstoppable={unstoppable})")
        if success:
            defender.apply_status(StatusEffect.PRONE)
            defender.status_durations[StatusEffect.PRONE] = 1
            self.log(f"{defender.character.name} is knocked prone.")
            if unstoppable:
                self._move_toward(attacker, defender.position, 3)
                attacker.forward_charge_ready = False
            return {"used": True, "success": True}
        else:
            return {"used": True, "success": False}

    def _reactive_maneuver(self, defender: CombatParticipant, attacker: CombatParticipant) -> None:
        if defender.reactive_maneuver_used:
            return
        if self.tactical_map:
            dist = self.tactical_map.manhattan_distance(defender.position[0], defender.position[1], attacker.position[0], attacker.position[1])
            if dist > 1:
                return
        roll, dice = roll_2d10()
        mod = defender.character.get_modifier("Strength", "Athletics")
        total = roll + mod
        self.log(f"Reactive maneuver roll {dice} -> {total}")
        defender.reactive_maneuver_used = True
        if total < 12:
            self.log("Reactive maneuver fails.")
            return
        if not attacker.has_status(StatusEffect.PRONE):
            attacker.apply_status(StatusEffect.PRONE)
            attacker.status_durations[StatusEffect.PRONE] = 1
            self.log(f"{defender.character.name} uses Reactive Stance to topple {attacker.character.name} prone.")
        else:
            self.apply_knockback(attacker, 1, source_pos=defender.position, source_name=defender.character.name)

    def action_trick_shot(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon, effect: str) -> Dict[str, Any]:
        if not attacker.has_feat("Trick Shot"):
            return {"used": False}
        if weapon.range_category != RangeCategory.RANGED:
            return {"used": False}
        if not attacker.can_use_limited("Trick Shot", per_scene=True, limit=3):
            self.log(f"No Trick Shot uses left this scene.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(2):
            self.log(f"{attacker.character.name} needs 2 actions for Trick Shot.")
            return {"used": False}
        shot_weapon = weapon
        if effect == "bodkin":
            shot_weapon = Weapon(name=weapon.name, damage=weapon.damage, accuracy_bonus=weapon.accuracy_bonus, actions_required=weapon.actions_required, range_category=weapon.range_category, is_two_handed=weapon.is_two_handed, armor_piercing=True, traits=list(weapon.traits))
        bypass_graze = (effect == "whistling")
        result = self.perform_attack(attacker, defender, weapon=shot_weapon, bypass_graze=bypass_graze)
        if result.get("hit"):
            if effect == "dazzling":
                defender.apply_status(StatusEffect.MARKED)
                defender.status_durations[StatusEffect.MARKED] = 1
                defender.spell_penalty_total = 3
                defender.spell_penalty_duration_rounds = max(defender.spell_penalty_duration_rounds, 1)
                self.log(f"Dazzling shot: {defender.character.name} suffers -3 to spellcasts for one round.")
            elif effect == "incendiary" and self.tactical_map:
                dx, dy = defender.position
                for nx, ny in self.tactical_map.get_neighbors(dx, dy):
                    tile = self.tactical_map.get_tile(nx, ny)
                    if tile and isinstance(tile.occupant, CombatParticipant):
                        ally = tile.occupant
                        dmg = ally.take_damage(3, armor_piercing=False)
                        self.log(f"Incendiary blast: {ally.character.name} takes 3 damage.")
        return {"used": True, "result": result, "effect": effect}

    def action_two_birds_one_stone(self, attacker: CombatParticipant, first: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if weapon.name not in {"Crossbow", "Spellbook"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Two Birds One Stone.")
            return {"used": False}
        res1 = self.perform_attack(attacker, first, weapon=weapon)
        res2: Optional[Dict[str, Any]] = None
        if res1.get("hit") and self.tactical_map:
            ax, ay = attacker.position
            fx, fy = first.position
            dx = fx - ax
            dy = fy - ay
            step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
            step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
            tx, ty = fx, fy
            for i in range(1, 6):
                tx += step_x
                ty += step_y
                tile = self.tactical_map.get_tile(tx, ty)
                if not tile:
                    break
                if tile.occupant and isinstance(tile.occupant, CombatParticipant):
                    second = tile.occupant
                    if second.current_hp <= 0:
                        continue
                    if self.tactical_map and not self.tactical_map.has_line_of_sight(attacker.position, (tx, ty)):
                        continue
                    af = getattr(attacker.character, "faction", None)
                    sf = getattr(second.character, "faction", None)
                    if af is not None and sf is not None and af == sf:
                        continue
                    damage = weapon.damage
                    applied = second.take_damage(damage, armor_piercing=False)
                    self.log(f"Two Birds: {second.character.name} behind takes {applied} non-AP damage.")
                    res2 = {"hit": True, "damage": applied}
                    break
        return {"used": True, "primary": res1, "secondary": res2}

    def _apply_control_push(self, attacker: CombatParticipant, defender: CombatParticipant, blocks: int) -> bool:
        if not self.tactical_map:
            self.log(f"{attacker.character.name} drives {defender.character.name} back {blocks} blocks.")
            return False
        start_tile = self.tactical_map.get_tile(attacker.position[0], attacker.position[1])
        def_tile = self.tactical_map.get_tile(defender.position[0], defender.position[1])
        if (start_tile and start_tile.move_cost > 1) or (def_tile and def_tile.move_cost > 1):
            self.log("Control: uneven terrain prevents push movement.")
            return True
        ax, ay = attacker.position
        dx = defender.position[0] - ax
        dy = defender.position[1] - ay
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        if abs(dx) > abs(dy):
            step_y = 0
        elif abs(dy) > abs(dx):
            step_x = 0
        blocked = False
        for _ in range(blocks):
            next_def_x = defender.position[0] + step_x
            next_def_y = defender.position[1] + step_y
            if not self.tactical_map.is_passable(next_def_x, next_def_y, defender):
                blocked = True
                break
            next_def_tile = self.tactical_map.get_tile(next_def_x, next_def_y)
            follow_x = next_def_x - step_x
            follow_y = next_def_y - step_y
            follow_tile = self.tactical_map.get_tile(follow_x, follow_y)
            if (next_def_tile and next_def_tile.move_cost > 1) or (follow_tile and follow_tile.move_cost > 1):
                blocked = True
                self.log("Control: uneven terrain prevents push movement.")
                break
            self.tactical_map.clear_occupant(defender.position[0], defender.position[1])
            defender.position = (next_def_x, next_def_y)
            self.tactical_map.set_occupant(next_def_x, next_def_y, defender)
            self.tactical_map.clear_occupant(attacker.position[0], attacker.position[1])
            attacker.position = (next_def_x - step_x, next_def_y - step_y)
            self.tactical_map.set_occupant(attacker.position[0], attacker.position[1], attacker)
        return blocked

    def _apply_knockback_force(self, target: CombatParticipant, blocks: int, source_pos: Tuple[int, int], source_name: str) -> Tuple[bool, bool]:
        if not self.tactical_map:
            self.log(f"{target.character.name} is knocked back {blocks} blocks by {source_name}!")
            return True, False
        start_x, start_y = target.position
        dx = start_x - source_pos[0]
        dy = start_y - source_pos[1]
        if abs(dx) > abs(dy):
            dx = 1 if dx > 0 else -1
            dy = 0
        else:
            dy = 1 if dy > 0 else -1
            dx = 0
        final_x, final_y = start_x, start_y
        blocked = False
        for i in range(1, blocks + 1):
            nx = start_x + dx * i
            ny = start_y + dy * i
            if not self.tactical_map.is_passable(nx, ny, target):
                blocked = True
                break
            final_x, final_y = nx, ny
        if (final_x, final_y) != (start_x, start_y):
            self.tactical_map.clear_occupant(start_x, start_y)
            target.position = (final_x, final_y)
            self.tactical_map.set_occupant(final_x, final_y, target)
            self.log(f"{target.character.name} is forced back {abs(final_x-start_x)+abs(final_y-start_y)} blocks by {source_name}!")
            return True, blocked
        else:
            self.log(f"{target.character.name} forced knockback blocked by terrain!")
            return False, True

    def action_block(self, actor: CombatParticipant) -> bool:
        if not self._ensure_can_act(actor):
            return False
        if not actor.shield:
            self.log(f"{actor.character.name} has no shield to block with.")
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} has no actions left to Block.")
            return False
        actor.is_blocking = True
        self.log(f"{actor.character.name} raises their shield to block.")
        return True

    def action_swap_weapons(self, actor: CombatParticipant) -> bool:
        if actor.is_dead or actor.current_hp <= 0:
            return False
        if actor.swap_used_turn:
            self.log(f"{actor.character.name} already used their free weapon swap this turn.")
            return False
        if actor.weapon_main and actor.weapon_offhand:
            actor.weapon_main, actor.weapon_offhand = actor.weapon_offhand, actor.weapon_main
            actor.swap_used_turn = True
            self.log(f"{actor.character.name} swaps weapons (free action).")
            return True
        self.log(f"{actor.character.name} has no offhand weapon to swap.")
        return False

    def action_second_wind(self, actor: CombatParticipant) -> bool:
        if not actor.has_feat("Second Wind"):
            return False
        if actor.feat_uses_this_fight.get("Second Wind", 0) >= 1:
            self.log(f"{actor.character.name} already used Second Wind this fight.")
            return False
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} has no actions left for Second Wind.")
            return False
        gained = max(0, actor.character.get_modifier("Strength", "Fortitude") + 2)
        actor.current_hp = min(actor.max_hp, actor.current_hp + gained)
        actor.is_critical = actor.current_hp == 0
        actor.feat_uses_this_fight["Second Wind"] = 1
        self.log(f"{actor.character.name} uses Second Wind and gains {gained} HP (now {actor.current_hp}/{actor.max_hp}).")
        return True

    def action_dual_striker(self, attacker: CombatParticipant, defender: CombatParticipant) -> Dict[str, Any]:
        if not attacker.has_feat("Dual Striker"):
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        main = attacker.weapon_main
        off = attacker.weapon_offhand
        if not main or not off:
            self.log(f"{attacker.character.name} needs two weapons for Dual Striker.")
            return {"used": False}
        eligible = {"Dagger", "Arming Sword", "Rapier", "Mace", "Whip", "Meteor Hammer", "Unarmed"}
        if main.name not in eligible or off.name not in eligible:
            self.log(f"Weapons not eligible for Dual Striker.")
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Dual Striker.")
            return {"used": False}
        death_save_used = False
        res1 = self.perform_attack(attacker, defender, weapon=main, accuracy_modifier=-1, is_dual_strike=True, allow_death_save_override=not death_save_used)
        death_save_used = death_save_used or defender.last_death_save_triggered
        res2 = self.perform_attack(attacker, defender, weapon=off, accuracy_modifier=-1, is_dual_strike=True, suppress_reactions=True, allow_death_save_override=not death_save_used)
        death_save_used = death_save_used or defender.last_death_save_triggered
        combined_damage = res1.get("damage", 0) + res2.get("damage", 0)
        return {"used": True, "damage": combined_damage, "results": (res1, res2)}

    def action_volley(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Volley"):
            return {"used": False}
        if weapon.name not in {"Recurve Bow", "Longbow"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Volley.")
            return {"used": False}
        res1 = self.perform_attack(attacker, defender, weapon=weapon, accuracy_modifier=-1)
        res2 = self.perform_attack(attacker, defender, weapon=weapon, accuracy_modifier=-1)
        combined_damage = res1.get("damage", 0) + res2.get("damage", 0)
        return {"used": True, "damage": combined_damage, "results": (res1, res2)}

    def action_armor_piercer(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Armor Piercer"):
            return {"used": False}
        if weapon.name not in {"Arming Sword", "Dagger"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            self.log(f"{attacker.character.name} lacks actions for Armor Piercer.")
            return {"used": False}
        ap = True
        if defender.shield and defender.shield.grants_ap_immunity and defender.is_blocking:
            ap = False
            damage_bonus = 1
        else:
            damage_bonus = 0
        result = self.perform_attack(attacker, defender, weapon=weapon, accuracy_modifier=0)
        if result.get("hit"):
            dmg = weapon.damage + damage_bonus
            actual = defender.take_damage(dmg, armor_piercing=ap)
            result["damage"] = actual
            self.log(f"Armor Piercer strike deals {actual} damage (AP={ap}).")
        return {"used": True, "result": result}

    def action_bastion_stance(self, actor: CombatParticipant) -> bool:
        if not actor.has_feat("Bastion Stance"):
            return False
        if not actor.shield:
            return False
        if not actor.take_limited_action():
            self.log(f"{actor.character.name} already used limited action this turn.")
            return False
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} has no actions left for Bastion Stance.")
            return False
        actor.is_blocking = True
        actor.bastion_active = True
        self.log(f"{actor.character.name} enters Bastion Stance - immune to knockback/push/prone!")
        return True

    def action_hamstring(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Hamstring"):
            return {"used": False}
        if weapon.name not in {"Whip", "Recurve Bow", "Crossbow"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Hamstring.")
            return {"used": False}
        result = self.perform_attack(attacker, defender, weapon=weapon, accuracy_modifier=-1, consume_actions=False)
        if result.get("hit"):
            self.log(f"Hamstring hits! {defender.character.name} is crippled (-2 movement, -2 evasion for 1 round).")
            defender.apply_status(StatusEffect.SLOWED)
            defender.status_durations[StatusEffect.SLOWED] = 1
        return {"used": True, "result": result}

    def action_patient_flow(self, actor: CombatParticipant) -> bool:
        if not actor.has_feat("Patient Flow"):
            return False
        if not actor.take_limited_action():
            self.log(f"{actor.character.name} already used a limited action this turn.")
            return False
        if not self._ensure_can_act(actor):
            return False
        if not actor.spend_actions(1):
            self.log(f"{actor.character.name} has no actions left for Patient Flow.")
            return False
        actor.is_evading = True
        actor.flowing_stance = True
        self.log(f"{actor.character.name} enters Flowing Stance, ready to redirect attacks.")
        return True

    def action_quickdraw(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon, mode: str) -> Dict[str, Any]:
        if not attacker.has_feat("Quickdraw"):
            return {"used": False}
        if weapon.name not in {"Longbow", "Crossbow", "Sling"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if mode not in {"dash", "evade"}:
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Quickdraw.")
            return {"used": False}
        if mode == "dash":
            self.log(f"{attacker.character.name} uses Quickdraw: Dash and Loose!")
            if self.tactical_map:
                self._quickdraw_move(attacker, defender, dash=True)
            attacker.dashed_this_turn = True
            attacker.free_move_used = True
        else:
            self.log(f"{attacker.character.name} uses Quickdraw: Evade and Loose!")
            attacker.is_evading = True
        result = self.perform_attack(attacker, defender, weapon=weapon, accuracy_modifier=-2, consume_actions=False)
        if result.get("hit"):
            reduced_damage = max(0, result["damage"] - 1)
            self.log(f"Quickdraw attack deals {reduced_damage} damage (base -1).")
            result["damage"] = reduced_damage
        return {"used": True, "result": result}

    def _quickdraw_move(self, actor: CombatParticipant, target: CombatParticipant, dash: bool) -> None:
        if not self.tactical_map:
            return
        base_movement = 5
        movement_penalty = actor.armor.movement_penalty_for(actor.character) if actor.armor else 0
        dash_bonus = 4 if dash else 0
        allowance = max(0, base_movement + movement_penalty + dash_bonus)
        sx, sy = actor.position
        tx, ty = target.position
        path = self.tactical_map.find_path(sx, sy, tx, ty, actor)
        if not path or len(path) <= 1:
            return
        traversed = 0
        walk: List[Tuple[int, int]] = [(sx, sy)]
        for i in range(1, len(path)):
            x, y = path[i]
            tile = self.tactical_map.get_tile(x, y)
            step_cost = tile.move_cost if tile else 1
            if traversed + step_cost > allowance:
                break
            traversed += step_cost
            walk.append((x, y))
        if len(walk) <= 1:
            return
        self._maybe_opportunity_attacks(actor, walk[-1])
        self.tactical_map.clear_occupant(sx, sy)
        actor.position = walk[-1]
        self.tactical_map.set_occupant(actor.position[0], actor.position[1], actor)
        self.log(f"{actor.character.name} quickdraw-moves {traversed} blocks toward {target.character.name}.")

    def action_vicious_mockery(self, actor: CombatParticipant, target: CombatParticipant) -> Dict[str, Any]:
        if not actor.has_feat("Vicious Mockery"):
            return {"used": False}
        if not self._ensure_can_act(actor):
            return {"used": False}
        if not actor.spend_actions(1):
            return {"used": False}
        prev = getattr(target, "mockery_penalty_total", 0)
        target.mockery_penalty_total = min(3, prev + 1)
        target.mockery_duration_rounds = max(target.mockery_duration_rounds, 1)
        self.log(f"{actor.character.name} mocks {target.character.name}: -1 penalty applied (total {target.mockery_penalty_total}).")
        return {"used": True, "penalty": target.mockery_penalty_total}

    def action_galestorm_strike(self, attacker: CombatParticipant, defender: CombatParticipant, weapon: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Galestorm Stance"):
            return {"used": False}
        if weapon.name not in {"Greatsword", "Polearm", "Staff"}:
            return {"used": False}
        if not attacker.take_limited_action():
            self.log(f"{attacker.character.name} already used a limited action this turn.")
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Galestorm Strike.")
            return {"used": False}
        extra = getattr(attacker, "evades_prev_turn", 0)
        results: List[Dict[str, Any]] = []
        res0 = self.perform_attack(attacker, defender, weapon=weapon)
        results.append(res0)
        for i in range(extra):
            resi = self.perform_attack(attacker, defender, weapon=weapon, consume_actions=False, suppress_reactions=True, half_damage=True)
            results.append(resi)
        return {"used": True, "results": results, "extra": extra}

    def action_fanning_blade(self, attacker: CombatParticipant, weapon: Weapon, center_x: int, center_y: int) -> Dict[str, Any]:
        if not attacker.has_feat("Fanning Blade"):
            return {"used": False}
        allowed = {"Throwing Knife", "Meteor Hammer", "Sling", "Arcane Wand"}
        if weapon.name not in allowed:
            return {"used": False}
        if not attacker.take_limited_action():
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(weapon.actions_required):
            self.log(f"{attacker.character.name} lacks actions for Fanning Blade.")
            return {"used": False}
        results: List[Tuple[CombatParticipant, Dict[str, Any]]] = []
        if not self.tactical_map:
            return {"used": False}
        tiles = []
        for y in range(max(0, center_y - 2), min(self.tactical_map.height, center_y + 3)):
            for x in range(max(0, center_x - 2), min(self.tactical_map.width, center_x + 3)):
                tiles.append((x, y))
        hit_set: Set[CombatParticipant] = set()
        for x, y in tiles:
            tile = self.tactical_map.get_tile(x, y)
            if not tile or not isinstance(tile.occupant, CombatParticipant):
                continue
            target = tile.occupant
            if target in hit_set:
                continue
            res = self.perform_attack(attacker, target, weapon=weapon, accuracy_modifier=-1, half_damage=(weapon.actions_required == 2))
            results.append((target, res))
            hit_set.add(target)
        return {"used": True, "results": results}

    def _count_lineage_feats(self, actor: CombatParticipant) -> int:
        names = [f.name for f in actor.feats]
        return sum(1 for n in names if n == "Lineage Weapon" or n.startswith("LW:"))

    def action_lineage_lacuna(self, actor: CombatParticipant, center_x: int, center_y: int) -> Dict[str, Any]:
        if not actor.has_feat("LW: Lacuna"):
            return {"used": False}
        if actor.lacuna_used_scene:
            return {"used": False}
        if not self._ensure_can_act(actor):
            return {"used": False}
        if not actor.spend_actions(2):
            return {"used": False}
        if not self.tactical_map:
            return {"used": False}
        actor.lacuna_used_scene = True
        lw_count = self._count_lineage_feats(actor)
        affected = 0
        for p in self.participants:
            if p is actor or p.current_hp <= 0:
                continue
            px, py = p.position
            dist = self.tactical_map.manhattan_distance(center_x, center_y, px, py)
            if dist <= 1:
                dmg = p.take_damage(lw_count, armor_piercing=False)
                affected += 1
                self.log(f"Lacuna: {p.character.name} takes {dmg} damage.")
            elif 2 <= dist <= 8:
                p.apply_status(StatusEffect.PRONE)
                p.status_durations[StatusEffect.PRONE] = 1
                affected += 1
                self.log(f"Lacuna: {p.character.name} is knocked prone.")
        return {"used": True, "affected": affected}

    def action_throw_small_blade(self, attacker: CombatParticipant, defender: CombatParticipant, blade: Weapon) -> Dict[str, Any]:
        if not attacker.has_feat("Harmonized Arsenal"):
            return {"used": False}
        if not blade or not getattr(blade, 'is_small_weapon', False):
            return {"used": False}
        if not self._ensure_can_act(attacker):
            return {"used": False}
        if not attacker.spend_actions(1):
            return {"used": False}
        throw_weapon = AVALORE_WEAPONS.get("Throwing Knife")
        if not throw_weapon:
            return {"used": False}
        res = self.perform_attack(attacker, defender, weapon=throw_weapon, accuracy_modifier=1)
        if attacker.weapon_offhand is blade:
            attacker.weapon_offhand = None
        return {"used": True, "result": res}

    def apply_knockback(
        self,
        target: CombatParticipant,
        blocks: int,
        source_pos: Optional[Tuple[int, int]] = None,
        source_name: str = ""
    ) -> Tuple[bool, bool]:
        if hasattr(target, 'bastion_active') and target.bastion_active:
            self.log(f"{target.character.name} is in Bastion Stance - knockback negated!")
            return False, False
        if hasattr(target, 'steadfast_active') and target.steadfast_active:
            self.log(f"{target.character.name} is braced - knockback negated!")
            return False, False
        if not self.tactical_map:
            self.log(f"{target.character.name} is knocked back {blocks} blocks{' by ' + source_name if source_name else ''}!")
            return True, False
        start_x, start_y = target.position
        if source_pos:
            dx = start_x - source_pos[0]
            dy = start_y - source_pos[1]
            if abs(dx) > abs(dy):
                dx = 1 if dx > 0 else -1
                dy = 0
            else:
                dy = 1 if dy > 0 else -1
                dx = 0
        else:
            import random
            directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
            dx, dy = random.choice(directions)
        final_x, final_y = start_x, start_y
        blocked = False
        for i in range(1, blocks + 1):
            next_x = start_x + dx * i
            next_y = start_y + dy * i
            if not self.tactical_map.is_passable(next_x, next_y, target):
                blocked = True
                break
            final_x, final_y = next_x, next_y
        if (final_x, final_y) != (start_x, start_y):
            self.tactical_map.clear_occupant(start_x, start_y)
            target.position = (final_x, final_y)
            self.tactical_map.set_occupant(final_x, final_y, target)
            distance_moved = abs(final_x - start_x) + abs(final_y - start_y)
            self.log(f"{target.character.name} is knocked back {distance_moved} blocks to ({final_x}, {final_y}){' by ' + source_name if source_name else ''}!")
            return True, blocked
        else:
            self.log(f"{target.character.name} knockback blocked by terrain!")
            return False, True

    def is_combat_ended(self) -> bool:
        alive_participants = [p for p in self.participants if p.current_hp > 0 and not p.is_dead]
        return len(alive_participants) <= 1

    def get_combat_summary(self) -> str:
        lines = ["\n=== Combat Status ==="]
        for p in self.participants:
            status = "CRITICAL" if p.is_critical else "ALIVE"
            lines.append(
                f"{p.character.name}: {p.current_hp}/{p.max_hp} HP | "
                f"Anima: {p.anima}/{p.max_anima} | {status}"
            )
        return "\n".join(lines)