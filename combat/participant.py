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
    concealed_next_action: bool = False
    inspired_scene: bool = False
    graze_buffer_used: bool = False
    suppress_death_save_once: bool = False
    free_action_while_critical_used: bool = False
    whirling_devil_active: bool = False
    sentinel_retaliation_used_round: bool = False
    reactive_maneuver_used: bool = False
    swap_used_turn: bool = False
    sentinel_needs_lift: bool = False
    team: str = ""
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
    spell_attack_penalty: int = 0
    spell_attack_penalty_duration: int = 0
    spell_evasion_bonus: int = 0
    spell_evasion_bonus_duration: int = 0
    spell_evasion_penalty: int = 0
    spell_evasion_penalty_duration: int = 0
    spell_soak_bonus: int = 0
    spell_soak_bonus_duration: int = 0
    # Spellcasting state (canonical arcane rules).
    primary_discipline: str = ""             # +1 to cast; miscasts cost no anima
    known_spells: List[str] = field(default_factory=list)
    check_penalties: Dict[str, int] = field(default_factory=dict)  # "Stat" / "Stat:Skill" -> penalty (overcast consequences)
    # Wired spell-effect state.
    active_dots: List[Dict[str, Any]] = field(default_factory=list)
    buffer_charges: int = 0                  # Buffer: next hit may become a graze
    barbs_charges: int = 0                   # Barbs: retaliation instances left
    kinetic_spike_ready: bool = False        # next successful attack +2 dmg + knockback
    duplicate_images: int = 0                # Eidetic Echo decoys
    ap_ward_rounds: int = 0                  # Fortify: immune to armor piercing
    bonus_actions_next_turn: int = 0         # Acceleration
    bonus_move_next_turn: int = 0
    bonus_move_this_turn: int = 0
    parry_bonus_next_turn: bool = False
    parry_damage_bonus_active: bool = False
    control_wall_bonus_targets: Set[Any] = field(default_factory=set)
    last_death_save_triggered: bool = False
    actions_per_turn: int = 2
    actions_remaining: int = 2
    limited_action_used: bool = False
    death_save_failures: int = 0
    is_dead: bool = False
    # Grapple relationships are tracked by id() because CombatParticipant is an
    # unhashable dataclass (see control_wall_bonus_targets for the same pattern).
    grappling_ids: Set[int] = field(default_factory=set)   # ids this one grapples
    grappled_by_ids: Set[int] = field(default_factory=set)  # ids grappling this one
    # Bleedout (failed Death Save) state.
    in_bleedout: bool = False
    bleedout_turns_remaining: int = 0
    stabilized: bool = False
    # Feat state for newly-wired combat feats.
    martial_discipline_stacks: int = 0       # active +aim to Arming Sword this turn
    martial_discipline_next: int = 0         # stacks earned from blocks this turn
    rage_active: bool = False
    rage_stats_applied: bool = False         # STR/DEX +1, INT/HAR -1 while raging
    unyielding_reflex_used_round: bool = False
    wounded_animal_used_scene: bool = False
    has_taken_turn: bool = False
    position: Tuple[int, int] = (0, 0)
    weapons_equipped: List[str] = field(default_factory=list)
    loaded_weapon: Optional[str] = None
    drawn_weapon: Optional[str] = None
    lifted_weapon: Optional[str] = None

    # Actions that do NOT trigger a Death Save while Critical (Avalore rules).
    # Bardic = inspiration abilities; Perception = Spot/Precise Senses; Preparatory
    # (Lift/Load/Draw) is matched by prefix below.
    DEATH_SAVE_EXEMPT_ACTIONS = {
        "dash", "evade", "block", "struggle", "hide", "conceal", "stabilize",
        "rousing inspiration", "commanding inspiration", "precise senses", "spot",
    }
    DEATH_SAVE_EXEMPT_PREFIXES = ("draw ", "load ", "lift")

    def _death_save_exempt(self, action_name: str) -> bool:
        return (action_name in self.DEATH_SAVE_EXEMPT_ACTIONS
                or action_name.startswith(self.DEATH_SAVE_EXEMPT_PREFIXES))

    def validate_action_cost(self, cost: int, is_limited: bool = False) -> bool:
        """Check if character can afford the action cost."""
        if cost > self.actions_remaining:
            return False
        if is_limited and self.limited_action_used:
            return False
        return True

    def consume_action(self, cost: int, is_limited: bool = False, action_name: str = "") -> bool:
        """Consume actions and mark limited if applicable. Returns success."""
        if not self.validate_action_cost(cost, is_limited):
            return False
        self.actions_remaining -= cost
        if is_limited:
            self.limited_action_used = True
        if self.is_critical and not self._death_save_exempt(action_name):
            # Critical state: most actions trigger a death save
            # Dispatch to feat handlers to check for suppression
            from .feat_handlers import FEAT_REGISTRY
            suppressed = FEAT_REGISTRY.dispatch_on_critical_action(
                self, action_name, {})
            if not suppressed:
                self.last_death_save_triggered = True
        return True

    def physical_penalty(self) -> int:
        """Penalty applied to physical rolls (Attack, Evade, Block, Cast) from
        conditions. Per the Avalore rules, both a grappler and a grappled target
        take -3 to physical rolls while the grapple is maintained."""
        pen = 0
        if self.has_status(StatusEffect.GRAPPLED) or self.grappling_ids:
            pen -= 3
        return pen

    def get_evasion_modifier(self) -> int:
        # The DEX:Acrobatics contribution to an Evade roll is capped at +3 per the
        # rules ("/roll evade ... capped at +3"). Feat bonuses (e.g. Quickfooted)
        # are added separately in the attack resolver and may exceed this cap.
        base = min(3, self.character.get_modifier("Dexterity", "Acrobatics"))
        if self.armor:
            base += self.armor.evasion_penalty
        if self.has_status(StatusEffect.SLOWED):
            base -= 2
        return base + self.physical_penalty() - self.mockery_penalty_total

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
        from .feat_handlers import FEAT_REGISTRY
        total, _ = roll_2d10()
        bonus = self.character.get_stat("Dexterity")
        # Dispatch initiative hooks (First Strike +5, Always Ready +3)
        bonus = FEAT_REGISTRY.dispatch_modify_initiative(self, bonus)
        # Skirmishing Party bonus (from nearby allies)
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
        from .feat_handlers import FEAT_REGISTRY
        # Bleedout: dying combatants count down toward death and take no actions.
        if self.in_bleedout:
            self.actions_remaining = 0
            self.limited_action_used = False
            self.has_taken_turn = True
            self.free_move_used = False  # the dying may crawl at half movement
            # Turn-start hooks first (e.g. Wounded Animal self-stabilizes) so a
            # mutant can halt their own countdown before it is decremented.
            engine = getattr(self, 'engine', None)
            if engine:
                FEAT_REGISTRY.dispatch_on_turn_start(engine, self)
            if not self.stabilized:
                self.bleedout_turns_remaining -= 1
                if self.bleedout_turns_remaining <= 0:
                    self.is_dead = True
            return
        # Default actions (+1 while hasted by Acceleration)
        self.actions_remaining = self.actions_per_turn + self.bonus_actions_next_turn
        self.bonus_actions_next_turn = 0
        self.bonus_move_this_turn = self.bonus_move_next_turn
        self.bonus_move_next_turn = 0
        self.limited_action_used = False
        self.has_taken_turn = True
        self.unyielding_reflex_used_round = False
        # Martial Discipline: stacks earned from blocking last turn apply this turn.
        self.martial_discipline_stacks = self.martial_discipline_next
        self.martial_discipline_next = 0
        self.is_evading = False
        self.is_blocking = False
        self.lifted_weapon = None  # Reset lift state each turn
        self.feat_uses_this_turn.clear()
        self.limited_used_turn.clear()
        self.temp_attack_bonus = 0
        self.last_hit_success = False
        self.flowing_stance = False
        self.dashed_this_turn = False
        self.free_move_used = False
        self.concealed_next_action = False
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
        if self.spell_attack_penalty_duration > 0:
            self.spell_attack_penalty_duration -= 1
            if self.spell_attack_penalty_duration == 0:
                self.spell_attack_penalty = 0
        if self.spell_evasion_bonus_duration > 0:
            self.spell_evasion_bonus_duration -= 1
            if self.spell_evasion_bonus_duration == 0:
                self.spell_evasion_bonus = 0
        if self.spell_evasion_penalty_duration > 0:
            self.spell_evasion_penalty_duration -= 1
            if self.spell_evasion_penalty_duration == 0:
                self.spell_evasion_penalty = 0
        if self.spell_soak_bonus_duration > 0:
            self.spell_soak_bonus_duration -= 1
            if self.spell_soak_bonus_duration == 0:
                self.spell_soak_bonus = 0
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
        if self.ap_ward_rounds > 0:
            self.ap_ward_rounds -= 1
        self._tick_damage_over_time()
        # Rage burns its host: 1 damage each turn while active.
        if self.rage_active and not self.is_dead:
            taken = self.take_damage(1, armor_piercing=True)
            engine = getattr(self, 'engine', None)
            if engine:
                engine.log(f"{self.character.name}'s Rage burns: {taken} self-damage.")
        # Dispatch turn-start feat hooks (First Strike 3 actions, etc.)
        engine = getattr(self, 'engine', None)
        if engine:
            FEAT_REGISTRY.dispatch_on_turn_start(engine, self)

    def _tick_damage_over_time(self):
        """Apply lingering spell damage (burning, blood loss) at turn start."""
        engine = getattr(self, 'engine', None)
        for dot in list(self.active_dots):
            taken = self.take_damage(dot["damage"], armor_piercing=dot.get("ap", True))
            if engine:
                engine.log(
                    f"{self.character.name} takes {taken} {dot.get('type', 'arcane')} damage "
                    f"from {dot['name']} ({dot['rounds'] - 1} rounds remain)."
                )
            dot["rounds"] -= 1
            dot["damage"] += dot.get("escalation", 0)
            if dot["rounds"] <= 0 or self.is_dead:
                self.active_dots.remove(dot)

    def spend_actions(self, amount: int) -> bool:
        if self.actions_remaining < amount:
            return False
        self.actions_remaining -= amount
        return True

    def swap_weapons(self) -> bool:
        """Once-per-turn convenience swap for main/offhand (dual-wield QoL)."""
        if self.swap_used_turn:
            return False
        self.weapon_main, self.weapon_offhand = self.weapon_offhand, self.weapon_main
        self.swap_used_turn = True
        return True

    def check_penalty(self, stat: str, skill: str = "") -> int:
        """Lingering penalty to a stat/skill check (overcast consequences)."""
        penalty = self.check_penalties.get(stat, 0)
        if skill:
            penalty += self.check_penalties.get(f"{stat}:{skill}", 0)
        return penalty

    # Rage shifts STR & DEX +1 and INT & HAR -1 (applied after other
    # modifiers, so directly on the base stats) until the Rage subsides.
    RAGE_STAT_SHIFTS = (("Strength", 1), ("Dexterity", 1), ("Intelligence", -1), ("Harmony", -1))

    def apply_rage_stat_shifts(self):
        if self.rage_stats_applied:
            return
        for stat, delta in self.RAGE_STAT_SHIFTS:
            self.character.base_stats[stat] = self.character.base_stats.get(stat, 0) + delta
        self.rage_stats_applied = True

    def end_rage(self):
        """End the Rage and revert its stat shifts (e.g. on entering Critical)."""
        if self.rage_stats_applied:
            for stat, delta in self.RAGE_STAT_SHIFTS:
                self.character.base_stats[stat] = self.character.base_stats.get(stat, 0) - delta
            self.rage_stats_applied = False
        self.rage_active = False

    def apply_status(self, status: StatusEffect):
        self.status_effects.add(status)

    def clear_status(self, status: StatusEffect):
        self.status_effects.discard(status)

    def has_status(self, status: StatusEffect) -> bool:
        return status in self.status_effects

    def can_use_limited(self, feat: str, per_scene: bool = False, limit: int = 1) -> bool:
        """Reserve this turn's single Limited slot.

        Per the Avalore rules a character may use only ONE Limited ability per
        turn, whether it is a feat ability or a maneuver (Shove/Topple/Pull/...).
        That shared per-turn budget is the ``limited_action_used`` flag, which is
        also set by :meth:`consume_action` (``is_limited=True``) and
        :meth:`take_limited_action`. Per-scene caps (e.g. "3x per scene") are an
        independent axis tracked via ``limited_used_scene_counts``.
        """
        # Shared per-turn budget: only one Limited action/ability per turn.
        if self.limited_action_used:
            return False
        if per_scene:
            # Per-scene cap is checked here; the matching
            # consume_action(is_limited=True) call claims the per-turn slot.
            count = self.limited_used_scene_counts.get(feat, 0)
            if count >= limit:
                return False
            self.limited_used_scene_counts[feat] = count + 1
            return True
        # Per-turn-only limited ability: claim the shared slot now.
        self.limited_used_turn.add(feat)
        self.limited_action_used = True
        return True

    def take_limited_action(self) -> bool:
        if self.limited_action_used:
            return False
        self.limited_action_used = True
        return True

    def can_use_weapon(self, weapon: Weapon) -> bool:
        """Check if character can use weapon (requirements + armor restrictions)."""
        if not weapon.meets_requirements(self.character):
            return False
        if self.armor and self.armor.prohibits_weapon(weapon):
            return False
        return True

    def get_weapon_penalty(self, weapon: Weapon) -> int:
        """Get accuracy penalty for not meeting weapon requirements."""
        if weapon.meets_requirements(self.character):
            return 0
        return -2  # Standard penalty for unmet requirements

    def can_dual_wield(self) -> bool:
        """Check if current loadout allows dual wielding."""
        if not self.weapon_main or not self.weapon_offhand:
            return False
        if self.weapon_main.is_two_handed or self.weapon_offhand.is_two_handed:
            return False
        return True

    def enforce_block_evade_exclusivity(self) -> bool:
        """Ensure block and evade aren't both active. Returns False if conflict."""
        if self.is_blocking and self.is_evading:
            return False  # Cannot do both
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

    def take_damage(self, amount: int, armor_piercing: bool = False, allow_death_save: bool = True, bypass_graze: bool = False) -> int:
        """Apply damage with armor soak, temp HP, and death save checks."""
        from .dice import roll_2d10
        self.last_death_save_triggered = False
        if amount <= 0:
            return 0
        # Fortify: the armour is sealed against armor-piercing effects.
        if armor_piercing and self.ap_ward_rounds > 0:
            armor_piercing = False
        # Apply armor soak unless AP
        if not armor_piercing and self.armor:
            meets_req = self.armor.meets_requirements(self.character)
            soak = self.armor.get_soak_value(meets_requirement=meets_req)
            amount = max(0, amount - soak)
        # Grazing hits and armor interaction
        if not bypass_graze and self.armor:
            # Medium/Heavy armor: no graze benefit (full damage)
            # Light armor: graze can halve damage (handled in attack resolution)
            pass
        # Temp HP absorbs first
        if self.temp_hp > 0 and amount > 0:
            absorbed = min(self.temp_hp, amount)
            self.temp_hp -= absorbed
            amount -= absorbed
        # Apply to real HP
        self.current_hp = max(0, self.current_hp - amount)
        # A character already in Bleedout that takes further damage dies.
        if self.in_bleedout:
            if amount > 0:
                self.is_dead = True
                self.in_bleedout = False
                self.clear_status(StatusEffect.BLEEDOUT)
            return amount
        # Check for critical/death
        if self.current_hp == 0:
            if self.is_critical:
                # Already critical: damage triggers a death save
                if allow_death_save and not self.suppress_death_save_once:
                    self.last_death_save_triggered = True
                    self.resolve_death_save()
                if self.suppress_death_save_once:
                    self.suppress_death_save_once = False
            else:
                # First time at 0 HP: become Critical
                self.is_critical = True
                if self.rage_active:
                    # The Rage ends immediately on entering Critical.
                    self.end_rage()
                    engine = getattr(self, 'engine', None)
                    if engine:
                        engine.log(f"{self.character.name}'s Rage ends as they fall Critical.")
        return amount

    def resolve_death_save(self):
        """Roll a Death Save (2d10 + STR:Fortitude halved, round up; DC 12).

        A critical success (10,10) exits Critical with 1 HP. A failure (< 12)
        drops the character into Bleedout rather than killing them outright."""
        import math
        from .dice import roll_2d10
        if self.is_dead or self.in_bleedout:
            return
        roll, dice = roll_2d10()
        is_crit_success = dice[0] == 10 and dice[1] == 10
        fort = self.character.get_modifier("Strength", "Fortitude")
        total = roll + math.ceil(fort / 2)
        if is_crit_success:
            self.is_critical = False
            self.current_hp = max(self.current_hp, 1)
            self.death_save_failures = 0
            return
        if total < 12:
            self.death_save_failures += 1
            self._enter_bleedout()

    def _enter_bleedout(self):
        """Enter Bleedout: out of the fight, dying after HAR:Belief (min 1) turns
        unless stabilized. A bleeding-out character is treated as incapacitated."""
        self.in_bleedout = True
        self.is_critical = False
        self.stabilized = False
        self.apply_status(StatusEffect.BLEEDOUT)
        belief = self.character.get_modifier("Harmony", "Belief")
        self.bleedout_turns_remaining = max(1, belief)
        self.actions_remaining = 0

    def heal(self, amount: int):
        # Corrupt: the body's own mending is turned against it.
        if self.has_status(StatusEffect.CORRUPTED):
            engine = getattr(self, 'engine', None)
            if engine:
                engine.log(f"{self.character.name} is Corrupted - the healing has no effect!")
            return
        self.current_hp = min(self.max_hp, self.current_hp + amount)
        if self.current_hp > 0:
            # Healing for any amount lifts Critical and Bleedout (per the rules).
            self.is_critical = False
            if self.in_bleedout:
                self.in_bleedout = False
                self.stabilized = False
                self.bleedout_turns_remaining = 0
                self.clear_status(StatusEffect.BLEEDOUT)
