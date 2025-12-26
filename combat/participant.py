from dataclasses import dataclass, field
from typing import Any, Optional, Tuple, List, Dict, Set
from .items import Weapon, Armor, Shield
from .enums import StatusEffect, ArmorCategory

@dataclass
class CombatParticipant:
    character: Any
    current_hp: int
    max_hp: int
    anima: int = 0
    max_anima: int = 0
    weapon_main: Optional[Weapon] = None
    weapon_offhand: Optional[Weapon] = None
    armor: Optional[Armor] = None
    shield: Optional[Shield] = None
    is_evading: bool = False
    is_blocking: bool = False
    is_critical: bool = False
    bastion_active: bool = False
    steadfast_active: bool = False
    flowing_stance: bool = False
    _first_turn_used: bool = False
    feats: List[Any] = field(default_factory=list)
    feat_uses_this_turn: Dict[str, int] = field(default_factory=dict)
    feat_uses_this_fight: Dict[str, int] = field(default_factory=dict)
    has_overcast_today: bool = False
    status_effects: Set[StatusEffect] = field(default_factory=set)
    status_durations: Dict[StatusEffect, int] = field(default_factory=dict)
    limited_used_turn: Set[str] = field(default_factory=set)
    limited_used_scene: Set[str] = field(default_factory=set)
    limited_used_scene_counts: Dict[str, int] = field(default_factory=dict)
    temp_attack_bonus: int = 0
    last_hit_success: bool = False
    shield_wall_active: bool = False
    threatened_reach: int = 1
    forward_charge_ready: bool = False
    temp_hp: int = 0
    next_unarmed_bonus: Optional[str] = None
    dashed_this_turn: bool = False
    free_move_used: bool = False
    ignore_next_conceal_penalty: bool = False
    inspired_scene: bool = False
    graze_buffer_used: bool = False
    suppress_death_save_once: bool = False
    free_action_while_critical_used: bool = False
    whirling_devil_active: bool = False
    sentinel_retaliation_used_round: bool = False
    reactive_maneuver_used: bool = False
    swap_used_turn: bool = False
    creature_type: str = "Unknown"
    lineage_weapon: Optional[str] = None
    lineage_weapon_alt: Optional[str] = None
    lineage_elements: Set[str] = field(default_factory=set)
    active_lineage_element: Optional[str] = None
    slain_species: Set[str] = field(default_factory=set)
    lacuna_used_scene: bool = False
    mockery_penalty_total: int = 0
    mockery_duration_rounds: int = 0
    spell_penalty_total: int = 0
    spell_penalty_duration_rounds: int = 0
    parry_bonus_next_turn: bool = False
    parry_damage_bonus_active: bool = False
    control_wall_bonus_targets: Set[Any] = field(default_factory=set)
    last_death_save_triggered: bool = False
    actions_per_turn: int = 2
    actions_remaining: int = 2
    limited_action_used: bool = False
    death_save_failures: int = 0
    is_dead: bool = False
    position: Tuple[int, int] = (0, 0)
    weapons_equipped: List[str] = field(default_factory=list)
    loaded_weapon: Optional[str] = None
    drawn_weapon: Optional[str] = None

    def get_evasion_modifier(self) -> int:
        base = self.character.get_modifier("Dexterity", "Acrobatics")
        if self.armor:
            base += self.armor.evasion_penalty
        if self.has_status(StatusEffect.SLOWED):
            base -= 2
        return base - self.mockery_penalty_total

    def get_quickfooted_bonus(self, incoming_weapon: Weapon, incoming_shield: Optional[Shield]) -> int:
        from .items import Shield
        from .enums import ShieldType
        if not self.has_feat("Quickfooted"):
            return 0
        if self.armor and self.armor.category == ArmorCategory.HEAVY:
            return 0
        if incoming_shield and incoming_shield.shield_type == ShieldType.LARGE:
            return 0
        quickfooted_weapons = {
            "Unarmed", "Mace", "Greatsword", "Spear", "Polearm", "Sling", "Javelin", "Longbow"
        }
        return 3 if incoming_weapon.name in quickfooted_weapons else 0

    def get_initiative_roll(self) -> int:
        from .dice import roll_2d10
        total, _ = roll_2d10()
        bonus = self.character.get_stat("Dexterity")
        if self.has_feat("First Strike"):
            bonus += 5
        elif self.has_feat("Always Ready"):
            bonus += 3
        if hasattr(self, 'engine') and getattr(self.engine, 'party_initiated', False) and hasattr(self, 'position') and self.engine.tactical_map:
            ax, ay = self.position
            for p in self.engine.participants:
                if p is self or p.current_hp <= 0:
                    continue
                if p.has_feat("Skirmishing Party"):
                    px, py = p.position
                    dist = self.engine.tactical_map.manhattan_distance(ax, ay, px, py)
                    if 2 <= dist <= 8:
                        bonus += 2
                        break
        return total + bonus

    def get_stealth_modifier(self) -> int:
        base = self.character.get_modifier("Dexterity", "Stealth")
        if hasattr(self, 'engine') and self.engine and self.engine.tactical_map and hasattr(self, 'position'):
            ax, ay = self.position
            for p in self.engine.participants:
                if p is self or p.current_hp <= 0:
                    continue
                if p.has_feat("Skirmishing Party"):
                    px, py = p.position
                    dist = self.engine.tactical_map.manhattan_distance(ax, ay, px, py)
                    if 2 <= dist <= 8:
                        base += 1
                        break
        return base

    def has_feat(self, feat_name: str) -> bool:
        return any(f.name == feat_name for f in self.feats)

    def start_turn(self):
        if self.has_feat("First Strike") and hasattr(self, '_first_turn_used'):
            if not self._first_turn_used:
                self.actions_remaining = 3
                self._first_turn_used = True
            else:
                self.actions_remaining = self.actions_per_turn
        else:
            self.actions_remaining = self.actions_per_turn
        self.limited_action_used = False
        self.is_evading = False
        self.is_blocking = False
        self.feat_uses_this_turn.clear()
        self.limited_used_turn.clear()
        self.temp_attack_bonus = 0
        self.last_hit_success = False
        self.flowing_stance = False
        self.dashed_this_turn = False
        self.free_move_used = False
        self.graze_buffer_used = False
        self.free_action_while_critical_used = False
        self.whirling_devil_active = False
        self.sentinel_retaliation_used_round = False
        self.reactive_maneuver_used = False
        self.swap_used_turn = False
        self.control_wall_bonus_targets.clear()
        self.last_death_save_triggered = False
        if self.parry_bonus_next_turn:
            self.parry_damage_bonus_active = True
            self.parry_bonus_next_turn = False
        else:
            self.parry_damage_bonus_active = False
        if hasattr(self, "evades_since_last_turn"):
            self.evades_prev_turn = getattr(self, "evades_since_last_turn", 0)
            self.evades_since_last_turn = 0
        if self.mockery_duration_rounds > 0:
            self.mockery_duration_rounds -= 1
            if self.mockery_duration_rounds == 0:
                self.mockery_penalty_total = 0
        if self.spell_penalty_duration_rounds > 0:
            self.spell_penalty_duration_rounds -= 1
            if self.spell_penalty_duration_rounds == 0:
                self.spell_penalty_total = 0
        expired: List[StatusEffect] = []
        for status, remaining in list(self.status_durations.items()):
            new_val = remaining - 1
            if new_val <= 0:
                expired.append(status)
                self.status_durations.pop(status, None)
            else:
                self.status_durations[status] = new_val
        for status in expired:
            self.status_effects.discard(status)

    def spend_actions(self, amount: int) -> bool:
        if self.actions_remaining < amount:
            return False
        self.actions_remaining -= amount
        return True

    def apply_status(self, status: StatusEffect):
        self.status_effects.add(status)

    def clear_status(self, status: StatusEffect):
        self.status_effects.discard(status)

    def has_status(self, status: StatusEffect) -> bool:
        return status in self.status_effects

    def can_use_limited(self, feat: str, per_scene: bool = False, limit: int = 1) -> bool:
        if not per_scene:
            if feat in self.limited_used_turn:
                return False
            self.limited_used_turn.add(feat)
            return True
        count = self.limited_used_scene_counts.get(feat, 0)
        if count >= limit:
            return False
        self.limited_used_scene_counts[feat] = count + 1
        return True

    def take_limited_action(self) -> bool:
        if self.limited_action_used:
            return False
        self.limited_action_used = True
        return True

    def can_use_weapon(self, weapon: Weapon) -> bool:
        if not weapon.meets_requirements(self.character):
            return False
        if self.armor and self.armor.prohibits_weapon(weapon):
            return False
        return True

    def equip_weapon(self, weapon_name: str, offhand: bool = False) -> bool:
        from .items import AVALORE_WEAPONS
        from .enums import validate_loadout
        if weapon_name not in AVALORE_WEAPONS:
            return False
        test = self.weapons_equipped + [weapon_name]
        if not validate_loadout(test):
            return False
        self.weapons_equipped = test
        weapon_obj = AVALORE_WEAPONS[weapon_name]
        if offhand:
            self.weapon_offhand = weapon_obj
        else:
            self.weapon_main = weapon_obj
        return True

    def cover_bonus(self, cover: str) -> int:
        return {"none": 0, "half": 2, "three_quarter": 4, "full": 99}.get(cover, 0)

    def take_damage(self, amount: int, armor_piercing: bool = False, allow_death_save: bool = True) -> int:
        from .dice import roll_2d10
        self.last_death_save_triggered = False
        if amount <= 0:
            return 0
        if not armor_piercing and self.armor:
            meets_req = self.armor.meets_requirements(self.character)
            soak = self.armor.get_soak_value(meets_requirement=meets_req)
            amount = max(0, amount - soak)
        if self.temp_hp > 0 and amount > 0:
            absorbed = min(self.temp_hp, amount)
            self.temp_hp -= absorbed
            amount -= absorbed
        self.current_hp = max(0, self.current_hp - amount)
        if self.current_hp == 0:
            if self.is_critical:
                if allow_death_save and not self.suppress_death_save_once:
                    self.last_death_save_triggered = True
                    self.resolve_death_save()
                if self.suppress_death_save_once:
                    self.suppress_death_save_once = False
            else:
                self.is_critical = True
        return amount

    def resolve_death_save(self):
        from .dice import roll_2d10
        if self.is_dead:
            return
        roll, _ = roll_2d10()
        if roll < 12:
            self.death_save_failures += 1
            if self.death_save_failures >= 1:
                self.is_dead = True

    def heal(self, amount: int):
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        if self.current_hp > 0:
            self.is_critical = False
