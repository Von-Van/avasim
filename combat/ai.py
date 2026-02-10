"""
Avalore Combat AI - standalone decision-making module.

Extracted from pyside_app.py so the AI logic is reusable, testable,
and importable independently of the GUI.

Usage:
    ai = CombatAI(strategy="balanced")
    actions = ai.decide_turn(engine, participant)

Strategies:
    - "aggressive": prioritise damage, fewer defensive stances
    - "defensive": prioritise survival, more blocking/evading
    - "balanced": EV-driven mix of offense and defense (default)
"""

from __future__ import annotations

import random as _random
from collections import deque
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

from .enums import RangeCategory, StatusEffect
from .items import AVALORE_WEAPONS, Weapon

if TYPE_CHECKING:
    from .engine import AvaCombatEngine
    from .map import TacticalMap
    from .participant import CombatParticipant


# ---------------------------------------------------------------------------
# Strategy configuration
# ---------------------------------------------------------------------------

STRATEGY_DEFAULTS = {
    "aggressive": {
        "defend_hp_threshold": 0.25,
        "defend_prob_threshold": 0.70,
        "ev_attack_floor": 0.0,
        "prefer_attack_over_stance": True,
    },
    "defensive": {
        "defend_hp_threshold": 0.60,
        "defend_prob_threshold": 0.45,
        "ev_attack_floor": 0.5,
        "prefer_attack_over_stance": False,
    },
    "balanced": {
        "defend_hp_threshold": 0.50,
        "defend_prob_threshold": 0.55,
        "ev_attack_floor": 0.0,
        "prefer_attack_over_stance": False,
    },
    "random": {
        "defend_hp_threshold": 0.50,
        "defend_prob_threshold": 0.50,
        "ev_attack_floor": 0.0,
        "prefer_attack_over_stance": False,
    },
}


# ---------------------------------------------------------------------------
# CombatAI
# ---------------------------------------------------------------------------

class CombatAI:
    """Autonomous combat decision maker.

    Parameters
    ----------
    strategy : str
        One of ``"aggressive"``, ``"defensive"``, ``"balanced"`` (default).
    decision_log : list[str] | None
        Optional list to append decision explanations to (for UI transparency).
    show_decisions : bool
        If True, decision reasons are appended to *decision_log* and *engine.combat_log*.
    """

    def __init__(
        self,
        strategy: str = "balanced",
        decision_log: Optional[List[str]] = None,
        show_decisions: bool = True,
    ) -> None:
        if strategy not in STRATEGY_DEFAULTS:
            strategy = "balanced"
        self.strategy = strategy
        self.config: Dict[str, Any] = dict(STRATEGY_DEFAULTS[strategy])
        self.decision_log: List[str] = decision_log if decision_log is not None else []
        self.show_decisions = show_decisions

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def decide_turn(self, engine: AvaCombatEngine, current: CombatParticipant) -> None:
        """Execute one full turn of decisions for *current*.

        The method directly calls engine action methods.  It is designed
        to be a drop-in replacement for the old ``_take_auto_actions``.
        """
        if self.strategy == "random":
            self._decide_turn_random(engine, current)
            return

        target = self._pick_target(engine, current)
        if target is None:
            return

        weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]
        dist = (engine.tactical_map.manhattan_distance(*current.position, *target.position)
                if engine.tactical_map else 1)
        expected = self.expected_attack_value(current, target, weapon)
        attack_mod = self.attack_mod_for_weapon(current, weapon)
        evasion_mod = self._evasion_mod(target)
        soak = self.expected_soak(target)
        self._log(engine,
                  f"Decision: Auto acting with {weapon.name} (dist {dist}, "
                  f"range {weapon.range_category.name}, EV {expected:.1f})")
        self._log(engine,
                  f"EV breakdown: aim {attack_mod:+d}, evade {evasion_mod:+d}, "
                  f"expected soak {soak:.1f}")

        # --- Movement phase ---
        self._move_to_preferred_range(engine, current, target, weapon)
        weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]

        # --- Pre-attack feat phase ---
        if self._try_pre_attack_feats(engine, current, target, weapon):
            return

        # --- Defensive phase (low HP) ---
        if self._try_defensive_feats(engine, current, target, weapon):
            return

        # --- Offensive feat phase ---
        if self._try_offensive_feats(engine, current, target, weapon):
            return

        # --- Stance selection ---
        self._choose_stance(engine, current, target)

        # --- Basic attack loop ---
        expected_value = self.expected_attack_value(current, target, weapon)
        attack_cost = weapon.actions_required
        swings = 0
        ev_floor = self.config["ev_attack_floor"]
        while (current.actions_remaining >= attack_cost
               and target.current_hp > 0
               and swings < 2):
            if expected_value <= ev_floor:
                break
            engine.perform_attack(current, target, weapon=weapon)
            swings += 1
            expected_value = self.expected_attack_value(current, target, weapon)

    # ------------------------------------------------------------------
    # Random strategy
    # ------------------------------------------------------------------

    def _decide_turn_random(self, engine: AvaCombatEngine,
                             current: CombatParticipant) -> None:
        """Random strategy: pick random targets and random actions each turn."""
        target = self._pick_target(engine, current)
        if target is None:
            return
        weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]
        self._log(engine, "Decision (random): choosing actions randomly.")

        # Random movement phase
        if engine.tactical_map and not current.free_move_used:
            allowance = self._movement_allowance(current, use_dash=False)
            if allowance > 0:
                reachable = self._reachable_tiles(
                    engine.tactical_map, current.position, allowance)
                tiles = [t for t in reachable if t != target.position]
                if tiles:
                    dest = _random.choice(tiles)
                    engine.action_move(current, *dest)

        # Random stance (50% chance)
        if _random.random() < 0.5:
            if current.shield and _random.random() < 0.5:
                engine.action_block(current)
            else:
                engine.action_evade(current)

        # Attack with remaining actions
        attack_cost = weapon.actions_required
        while (current.actions_remaining >= attack_cost
               and target.current_hp > 0):
            engine.perform_attack(current, target, weapon=weapon)

    # ------------------------------------------------------------------
    # Target selection
    # ------------------------------------------------------------------

    def _pick_target(self, engine: AvaCombatEngine, current: CombatParticipant) -> Optional[CombatParticipant]:
        """Choose the best target: nearest alive opponent."""
        enemies = [
            p for p in engine.participants
            if p is not current and p.current_hp > 0 and not p.is_dead
            and not self._is_ally(engine, current, p)
        ]
        if not enemies:
            return None
        if engine.tactical_map:
            enemies.sort(key=lambda e: engine.get_distance(current, e))
        return enemies[0]

    # ------------------------------------------------------------------
    # Pre-attack feat logic (setup / single-use abilities)
    # ------------------------------------------------------------------

    def _try_pre_attack_feats(self, engine: AvaCombatEngine,
                               current: CombatParticipant,
                               target: CombatParticipant,
                               weapon: Weapon) -> bool:
        """Try setup feats. Returns True if turn was consumed."""

        # Aberration Slayer: set target type once
        if current.has_feat("Aberration Slayer"):
            if getattr(target, "creature_type", None) and not getattr(current, "aberration_slayer_type", None):
                engine.action_set_aberration_target(current, target.creature_type)

        # Support inspirations (only when allies exist)
        allies = [
            p for p in engine.participants
            if p is not current and p is not target
            and p.current_hp > 0 and self._is_ally(engine, current, p)
        ]
        if allies:
            if current.has_feat("Rousing Inspiration") and engine.tactical_map:
                if any(not getattr(p, "inspired_scene", False) for p in allies):
                    res = engine.action_rousing_inspiration(current)
                    if res.get("used") and res.get("granted"):
                        return True
            if current.has_feat("Commanding Inspiration"):
                if any(getattr(p, "temp_attack_bonus", 0) < 1 for p in allies):
                    res = engine.action_commanding_inspiration(current)
                    if res.get("used") and res.get("granted"):
                        return True

        return False

    # ------------------------------------------------------------------
    # Defensive feat logic
    # ------------------------------------------------------------------

    def _try_defensive_feats(self, engine: AvaCombatEngine,
                              current: CombatParticipant,
                              target: CombatParticipant,
                              weapon: Weapon) -> bool:
        """Try defensive feats when HP is low. Returns True if turn consumed."""
        hp_ratio = current.current_hp / max(1, current.max_hp)
        threshold = self.config["defend_hp_threshold"]

        if hp_ratio >= threshold:
            return False

        if current.has_feat("Patient Flow"):
            if engine.action_patient_flow(current):
                return True
        if current.has_feat("Bastion Stance") and current.shield:
            if engine.action_bastion_stance(current):
                return True
        if current.has_feat("Second Wind"):
            if engine.action_second_wind(current):
                return True
        return False

    # ------------------------------------------------------------------
    # Offensive feat logic
    # ------------------------------------------------------------------

    def _try_offensive_feats(self, engine: AvaCombatEngine,
                              current: CombatParticipant,
                              target: CombatParticipant,
                              weapon: Weapon) -> bool:
        """Try offensive feats in priority order. Returns True if turn consumed."""
        hp_ratio = current.current_hp / max(1, current.max_hp)

        # Lineage Lacuna (scene) if clustered targets nearby
        if current.has_feat("LW: Lacuna") and engine.tactical_map:
            if not getattr(current, "lacuna_used_scene", False):
                cx, cy = target.position
                res = engine.action_lineage_lacuna(current, cx, cy)
                if res.get("used") and res.get("affected"):
                    return True

        # Quickdraw (limited) if weapon supports it
        if current.has_feat("Quickdraw") and weapon.name in {"Longbow", "Crossbow", "Sling"}:
            mode = "evade" if hp_ratio < 0.5 else "dash"
            used = engine.action_quickdraw(current, target, weapon, mode=mode)
            if used.get("used"):
                return True

        # Hamstring (limited) if applicable weapon
        if current.has_feat("Hamstring") and weapon.name in {"Whip", "Recurve Bow", "Crossbow"}:
            used = engine.action_hamstring(current, target, weapon)
            if used.get("used"):
                self._log(engine, "Feat hook: Hamstring (eligible weapon, limited action).")
                return True

        # Fanning Blade for small/throwing when multiple foes nearby
        if current.has_feat("Fanning Blade") and engine.tactical_map:
            allowed = {"Throwing Knife", "Meteor Hammer", "Sling", "Arcane Wand"}
            if weapon.name in allowed:
                cx, cy = target.position
                nearby = self._count_nearby_enemies(engine, current, cx, cy)
                if nearby >= 2:
                    used = engine.action_fanning_blade(current, weapon, cx, cy)
                    if used.get("used"):
                        self._log(engine, f"Feat hook: Fanning Blade (clustered targets={nearby}).")
                        return True

        # Galestorm Strike (two-handed heavy)
        if current.has_feat("Galestorm Stance") and weapon.name in {"Greatsword", "Polearm", "Staff"}:
            used = engine.action_galestorm_strike(current, target, weapon)
            if used.get("used"):
                self._log(engine, "Feat hook: Galestorm Strike (two-handed stance).")
                return True

        # Whirling Devil: activate before moving through foes
        if current.has_feat("Whirling Devil") and not current.whirling_devil_active:
            engine.action_whirling_devil(current)

        # Vault to close distance with defense
        if current.has_feat("Combat Acrobat") and engine.tactical_map:
            dist = engine.get_distance(current, target)
            if dist > 1:
                tx, ty = target.position
                engine.action_vault(current, tx, ty)

        # Ranger's Gambit at melee with bows
        if current.has_feat("Ranger's Gambit") and weapon.name in {"Recurve Bow", "Longbow"}:
            if engine.tactical_map:
                dist = engine.tactical_map.manhattan_distance(
                    current.position[0], current.position[1],
                    target.position[0], target.position[1])
                if dist <= 1:
                    used = engine.action_rangers_gambit(current, target, weapon)
                    if used.get("used"):
                        self._log(engine, "Feat hook: Ranger's Gambit (bow at melee range).")
                        return True

        # Piercing Strike / Armor Piercer vs blocking target
        if target.shield and target.is_blocking and weapon.name in {"Arming Sword", "Dagger"}:
            if current.has_feat("Piercing Strike"):
                used = engine.action_piercing_strike(current, target, weapon)
                if used.get("used"):
                    self._log(engine, "Feat hook: Piercing Strike (target blocking with shield).")
                    return True
            if current.has_feat("Armor Piercer"):
                used = engine.action_armor_piercer(current, target, weapon)
                if used.get("used"):
                    self._log(engine, "Feat hook: Armor Piercer (target blocking with shield).")
                    return True

        # Feint when EV is low
        if current.has_feat("Feint"):
            if self.expected_attack_value(current, target, weapon) < 1.0:
                used = engine.action_feint(current, target)
                if used.get("used"):
                    self._log(engine, "Feat hook: Feint (low expected value).")
                    return True

        # Trick Shot (ranged)
        if current.has_feat("Trick Shot") and weapon.range_category == RangeCategory.RANGED:
            effect = "dazzling" if not target.has_status(StatusEffect.MARKED) else "bodkin"
            used = engine.action_trick_shot(current, target, weapon, effect)
            if used.get("used"):
                self._log(engine, f"Feat hook: Trick Shot ({effect}).")
                return True

        # Two Birds One Stone
        if current.has_feat("Two Birds One Stone") and weapon.name in {"Crossbow", "Spellbook"}:
            if self._has_trailing_target(engine, current, target):
                used = engine.action_two_birds_one_stone(current, target, weapon)
                if used.get("used"):
                    self._log(engine, "Feat hook: Two Birds One Stone (lined-up target).")
                    return True

        # Volley for bows
        if current.has_feat("Volley") and weapon.name in {"Recurve Bow", "Longbow"}:
            used = engine.action_volley(current, target, weapon)
            if used.get("used"):
                self._log(engine, "Feat hook: Volley (bow burst).")
                return True

        # Topple/Shove when Forward Charge primed
        if current.forward_charge_ready:
            used = engine.action_topple(current, target)
            if used.get("used") and used.get("success"):
                return True
            used = engine.action_shove(current, target)
            if used.get("used") and used.get("success"):
                return True

        # Hilt Strike as follow-up for two-handed weapons
        if current.has_feat("Hilt Strike") and weapon.is_two_handed:
            used = engine.action_hilt_strike(current, target, weapon)
            if used.get("used"):
                return True

        # Momentum Strike if already dashed
        if current.has_feat("Momentum") and current.dashed_this_turn:
            used = engine.action_momentum_strike(current, target)
            if used.get("used"):
                return True

        # Dual Striker when dual-wielding
        if current.has_feat("Dual Striker") and current.weapon_main and current.weapon_offhand:
            used = engine.action_dual_striker(current, target)
            if used.get("used"):
                return True

        # Vicious Mockery when attack EV is poor
        expected_value = self.expected_attack_value(current, target, weapon)
        if current.has_feat("Vicious Mockery") and expected_value < 0.8:
            used = engine.action_vicious_mockery(current, target)
            if used.get("used"):
                self._log(engine, "Feat hook: Vicious Mockery (attack EV low).")

        return False

    # ==================================================================
    # Movement helpers
    # ==================================================================

    def _move_to_preferred_range(self, engine: AvaCombatEngine,
                                  current: CombatParticipant,
                                  target: CombatParticipant,
                                  weapon: Weapon) -> None:
        if not engine.tactical_map:
            return
        dist = engine.get_distance(current, target)
        # Desired distance bands per weapon range category
        if weapon.range_category == RangeCategory.MELEE:
            desired_min, desired_max = 1, 1
        elif weapon.range_category == RangeCategory.SKIRMISHING:
            desired_min, desired_max = 2, 8
        else:
            desired_min, desired_max = 6, 30

        if desired_min <= dist <= desired_max:
            return

        best: Optional[Tuple[int, int]] = None
        best_score: Optional[Tuple[int, int, int, int]] = None
        best_use_dash = False

        for use_dash in (False, True):
            allowance = self._movement_allowance(current, use_dash)
            if allowance <= 0:
                continue
            reachable = self._reachable_tiles(engine.tactical_map, current.position, allowance)
            for (x, y), cost in reachable.items():
                if (x, y) == target.position:
                    continue
                new_dist = engine.tactical_map.manhattan_distance(x, y, target.position[0], target.position[1])
                score = abs(max(desired_min, min(desired_max, new_dist)) - new_dist)
                in_band = desired_min <= new_dist <= desired_max
                rank = (0 if in_band else 1, score, cost, 1 if use_dash else 0)
                if best_score is None or rank < best_score:
                    best_score = rank
                    best = (x, y)
                    best_use_dash = use_dash
            if best_score and best_score[0] == 0:
                break

        if best and current.actions_remaining > 0:
            new_dist = engine.tactical_map.manhattan_distance(
                best[0], best[1], target.position[0], target.position[1])
            move_kind = "Dash" if best_use_dash else "Move"
            self._log(engine, f"Range move: {dist} → {new_dist} via {move_kind} to {best}")
            if best_use_dash:
                if not engine.action_dash(current, *best):
                    engine.action_move(current, *best)
            else:
                if not engine.action_move(current, *best):
                    engine.action_dash(current, *best)

    @staticmethod
    def _movement_allowance(actor: CombatParticipant, use_dash: bool) -> int:
        base_movement = 5
        movement_penalty = actor.armor.movement_penalty_for(actor.character) if actor.armor else 0
        if actor.has_status(StatusEffect.SLOWED):
            movement_penalty -= 2
        base_allow = max(0, base_movement + movement_penalty)
        if use_dash:
            dash_bonus = 4
            return dash_bonus if actor.free_move_used else base_allow + dash_bonus
        return 0 if actor.free_move_used else base_allow

    @staticmethod
    def _reachable_tiles(tactical_map: TacticalMap, start: Tuple[int, int],
                          allowance: int) -> Dict[Tuple[int, int], int]:
        from .participant import CombatParticipant as CP
        reachable: Dict[Tuple[int, int], int] = {}
        q: deque = deque()
        q.append((start, 0))
        seen: Set[Tuple[int, int]] = {start}
        while q:
            (x, y), cost = q.popleft()
            reachable[(x, y)] = cost
            for nx, ny in tactical_map.get_neighbors(x, y):
                if (nx, ny) in seen:
                    continue
                tile = tactical_map.get_tile(nx, ny)
                if not tile or not tile.passable:
                    continue
                step_cost = tile.move_cost
                new_cost = cost + step_cost
                if new_cost > allowance:
                    continue
                if tile.occupant and isinstance(tile.occupant, CP):
                    continue
                seen.add((nx, ny))
                q.append(((nx, ny), new_cost))
        return reachable

    # ==================================================================
    # Stance selection
    # ==================================================================

    def _choose_stance(self, engine: AvaCombatEngine,
                        current: CombatParticipant,
                        target: CombatParticipant) -> None:
        hp_ratio = current.current_hp / max(1, current.max_hp)
        t_weapon = (target.weapon_main or AVALORE_WEAPONS["Unarmed"]) if target else AVALORE_WEAPONS["Unarmed"]

        p_block = 0.0
        if current.shield:
            threshold = current.shield.get_block_dc() - current.shield.block_modifier
            p_block = self.prob_2d10_at_least(threshold)

        attack_base = t_weapon.accuracy_bonus + self.attack_mod_for_weapon(target, t_weapon)
        ev_mod = self._evasion_mod(current)
        diff_counts: Dict[int, int] = {}
        total = 0
        for a in range(1, 11):
            for b in range(1, 11):
                for c in range(1, 11):
                    for d in range(1, 11):
                        diff = (c + d) - (a + b)
                        diff_counts[diff] = diff_counts.get(diff, 0) + 1
                        total += 1
        threshold_val = attack_base - ev_mod
        valid = sum(count for diff, count in diff_counts.items() if diff > threshold_val)
        p_evade = valid / total if total else 0.0

        hp_thresh = self.config["defend_hp_threshold"]
        prob_thresh = self.config["defend_prob_threshold"]

        defend = False
        if hp_ratio < hp_thresh and max(p_evade, p_block) > prob_thresh:
            defend = True
        elif max(p_evade, p_block) > 0.70:
            defend = True

        if self.config.get("prefer_attack_over_stance") and not defend:
            return

        if defend:
            if p_block >= p_evade and current.shield:
                self._log(engine, f"Stance: Block (p_block={p_block:.2f} vs p_evade={p_evade:.2f})")
                engine.action_block(current)
            else:
                self._log(engine, f"Stance: Evade (p_evade={p_evade:.2f} vs p_block={p_block:.2f})")
                engine.action_evade(current)

    # ==================================================================
    # Expected-value math (public for testability)
    # ==================================================================

    @staticmethod
    def prob_2d10_at_least(threshold: int) -> float:
        """Exact probability for 2d10 >= threshold."""
        total = 0
        valid = 0
        for a in range(1, 11):
            for b in range(1, 11):
                s = a + b
                total += 1
                if s >= threshold:
                    valid += 1
        return valid / total if total else 0.0

    @staticmethod
    def expected_soak(defender: CombatParticipant) -> float:
        armor = defender.armor
        if armor is None:
            return 0.0
        from .enums import ArmorCategory
        meets = armor.meets_requirements(defender.character)
        base = 0.0
        if armor.category == ArmorCategory.LIGHT:
            base = 0.5
        elif armor.category == ArmorCategory.MEDIUM:
            base = 1.0
        elif armor.category == ArmorCategory.HEAVY:
            base = 2.0
        if not meets:
            base = max(0.0, base - 1.0)
        return base

    @staticmethod
    def attack_mod_for_weapon(attacker: CombatParticipant, weapon: Optional[Weapon] = None) -> int:
        if weapon is None:
            weapon = attacker.weapon_main or AVALORE_WEAPONS["Unarmed"]
        if weapon.range_category == RangeCategory.MELEE:
            return attacker.character.get_modifier("Strength", "Athletics")
        else:
            return attacker.character.get_modifier("Dexterity", "Acrobatics")

    @staticmethod
    def _evasion_mod(defender: CombatParticipant) -> int:
        base = defender.character.get_modifier("Dexterity", "Acrobatics")
        if defender.armor:
            base += defender.armor.evasion_penalty
        return base

    @staticmethod
    def expected_attack_value(attacker: CombatParticipant,
                               defender: CombatParticipant,
                               weapon: Weapon) -> float:
        """Expected damage per action considering contested evasion."""
        attack_base = weapon.accuracy_bonus + CombatAI.attack_mod_for_weapon(attacker, weapon)
        ev_mod = CombatAI._evasion_mod(defender)

        diff_counts: Dict[int, int] = {}
        total = 0
        for a in range(1, 11):
            for b in range(1, 11):
                for c in range(1, 11):
                    for d in range(1, 11):
                        diff = (a + b) - (c + d)
                        diff_counts[diff] = diff_counts.get(diff, 0) + 1
                        total += 1
        threshold = ev_mod - attack_base
        valid = sum(count for diff, count in diff_counts.items() if diff > threshold)
        p_hit = valid / total if total else 0.0

        soak = 0.0 if weapon.is_piercing() else CombatAI.expected_soak(defender)
        base_damage = max(0.0, weapon.damage - soak)
        expected = p_hit * base_damage
        actions = max(1, weapon.actions_required)
        return expected / actions

    # ==================================================================
    # Misc helpers
    # ==================================================================

    @staticmethod
    def _is_ally(engine: AvaCombatEngine, a: CombatParticipant, b: CombatParticipant) -> bool:
        team_a = getattr(a, "team", "") or ""
        team_b = getattr(b, "team", "") or ""
        if team_a and team_b:
            return team_a == team_b
        # Empty team = FFA / no team → never allies
        return False

    @staticmethod
    def _count_nearby_enemies(engine: AvaCombatEngine,
                               current: CombatParticipant,
                               cx: int, cy: int) -> int:
        if not engine.tactical_map:
            return 0
        from .participant import CombatParticipant as CP
        count = 0
        for nx in range(max(0, cx - 2), min(engine.tactical_map.width, cx + 3)):
            for ny in range(max(0, cy - 2), min(engine.tactical_map.height, cy + 3)):
                tile = engine.tactical_map.get_tile(nx, ny)
                if (tile and isinstance(tile.occupant, CP)
                        and tile.occupant is not current
                        and tile.occupant.current_hp > 0):
                    count += 1
        return count

    @staticmethod
    def _has_trailing_target(engine: AvaCombatEngine,
                              attacker: CombatParticipant,
                              first: CombatParticipant) -> bool:
        if not engine.tactical_map:
            return False
        from .participant import CombatParticipant as CP
        ax, ay = attacker.position
        fx, fy = first.position
        dx = fx - ax
        dy = fy - ay
        if dx == 0 and dy == 0:
            return False
        step_x = 0 if dx == 0 else (1 if dx > 0 else -1)
        step_y = 0 if dy == 0 else (1 if dy > 0 else -1)
        tx, ty = fx, fy
        for _ in range(1, 6):
            tx += step_x
            ty += step_y
            tile = engine.tactical_map.get_tile(tx, ty)
            if not tile:
                break
            if (tile.occupant and isinstance(tile.occupant, CP)
                    and tile.occupant.current_hp > 0):
                other = tile.occupant
                if other is not attacker and other is not first:
                    return True
        return False

    def _log(self, engine: AvaCombatEngine, message: str) -> None:
        if self.show_decisions:
            self.decision_log.append(message)
            engine.combat_log.append(message)
