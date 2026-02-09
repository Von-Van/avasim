"""
Centralized feat handler system for Avalore Combat.

All feat logic is organized into handler classes that implement typed hooks.
The FeatRegistry dispatches calls to the appropriate handlers based on a
participant's equipped feats.

Hook categories:
  - modify_attack_roll: adjust aim total before hit/miss determination
  - modify_damage: adjust damage before it's applied
  - modify_evasion: adjust evasion total
  - modify_initiative: adjust initiative roll
  - modify_stealth: adjust stealth modifier
  - on_hit: triggered after a successful hit lands
  - on_miss: triggered after an attack misses
  - on_graze: triggered on a grazing hit
  - on_evade_success: triggered after fully evading
  - on_block_success: triggered after a successful block
  - on_turn_start: triggered at the start of a participant's turn
  - on_critical_action: triggered when a critical participant takes an action
  - execute_action: perform a feat's active ability
"""

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Tuple

if TYPE_CHECKING:
    from .participant import CombatParticipant
    from .items import Weapon, Shield
    from .engine import AvaCombatEngine


# ---------------------------------------------------------------------------
# Base class
# ---------------------------------------------------------------------------

class FeatHandler:
    """Base class for all feat handlers. Override hooks as needed."""

    feat_name: str = ""

    # --- Attack phase hooks (called during perform_attack) ---

    def modify_attack_roll(self, engine: AvaCombatEngine, attacker: CombatParticipant,
                           defender: CombatParticipant, weapon: Weapon,
                           current_total: int, context: Dict[str, Any]) -> int:
        """Return adjusted attack total. Called for the ATTACKER's feats."""
        return current_total

    def modify_defense_roll(self, engine: AvaCombatEngine, attacker: CombatParticipant,
                            defender: CombatParticipant, weapon: Weapon,
                            current_total: int, context: Dict[str, Any]) -> int:
        """Return adjusted attack total (negative = harder to hit). Called for DEFENDER's feats."""
        return current_total

    def modify_evasion(self, engine: AvaCombatEngine, defender: CombatParticipant,
                       weapon: Weapon, current_bonus: int, context: Dict[str, Any]) -> int:
        """Return adjusted evasion bonus. Called for DEFENDER's feats."""
        return current_bonus

    def modify_block(self, engine: AvaCombatEngine, defender: CombatParticipant,
                     weapon: Weapon, current_bonus: int, context: Dict[str, Any]) -> int:
        """Return adjusted block bonus. Called for DEFENDER's feats."""
        return current_bonus

    def modify_damage(self, engine: AvaCombatEngine, attacker: CombatParticipant,
                      defender: CombatParticipant, weapon: Weapon,
                      current_damage: int, context: Dict[str, Any]) -> int:
        """Return adjusted damage. Called for ATTACKER's feats after hit confirmed."""
        return current_damage

    # --- Post-resolution hooks ---

    def on_hit(self, engine: AvaCombatEngine, attacker: CombatParticipant,
               defender: CombatParticipant, weapon: Weapon,
               result: Dict[str, Any]) -> None:
        """Called after a successful hit (including graze)."""
        pass

    def on_miss(self, engine: AvaCombatEngine, attacker: CombatParticipant,
                defender: CombatParticipant, weapon: Weapon,
                result: Dict[str, Any]) -> None:
        """Called after an attack misses. Called for ATTACKER's feats."""
        pass

    def on_evade_success(self, engine: AvaCombatEngine, defender: CombatParticipant,
                         attacker: CombatParticipant, weapon: Weapon) -> None:
        """Called when defender fully evades. Called for DEFENDER's feats."""
        pass

    def on_graze(self, engine: AvaCombatEngine, attacker: CombatParticipant,
                 defender: CombatParticipant, weapon: Weapon,
                 context: Dict[str, Any]) -> None:
        """Called on a grazing hit, before damage. Called for DEFENDER's feats."""
        pass

    def on_block_success(self, engine: AvaCombatEngine, defender: CombatParticipant,
                         attacker: CombatParticipant) -> None:
        """Called after a successful block. Called for DEFENDER's feats."""
        pass

    # --- Turn lifecycle hooks ---

    def on_turn_start(self, engine: AvaCombatEngine, participant: CombatParticipant) -> None:
        """Called at the start of a participant's turn."""
        pass

    # --- Initiative / stealth hooks ---

    def modify_initiative(self, participant: CombatParticipant, current_bonus: int) -> int:
        """Return adjusted initiative bonus."""
        return current_bonus

    def modify_stealth(self, participant: CombatParticipant, current_mod: int,
                       engine: AvaCombatEngine) -> int:
        """Return adjusted stealth modifier."""
        return current_mod

    # --- Critical state hook ---

    def on_critical_action(self, participant: CombatParticipant, action_name: str,
                           context: Dict[str, Any]) -> bool:
        """Return True to suppress the death save for this action. Called for participant's feats."""
        return False


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

class FeatRegistry:
    """Maps feat names to handler instances and dispatches hooks."""

    def __init__(self) -> None:
        self._handlers: Dict[str, FeatHandler] = {}

    def register(self, handler: FeatHandler) -> None:
        self._handlers[handler.feat_name] = handler

    def get(self, feat_name: str) -> Optional[FeatHandler]:
        return self._handlers.get(feat_name)

    def handlers_for(self, participant: CombatParticipant) -> List[FeatHandler]:
        """Return list of handlers matching the participant's feats, in order."""
        result = []
        for feat in participant.feats:
            h = self._handlers.get(feat.name)
            if h is not None:
                result.append(h)
        return result

    # --- Dispatchers for each hook ---

    def dispatch_modify_attack_roll(self, engine: AvaCombatEngine,
                                     attacker: CombatParticipant,
                                     defender: CombatParticipant,
                                     weapon: 'Weapon', total: int,
                                     context: Dict[str, Any]) -> int:
        for h in self.handlers_for(attacker):
            total = h.modify_attack_roll(engine, attacker, defender, weapon, total, context)
        return total

    def dispatch_modify_defense_roll(self, engine: AvaCombatEngine,
                                      attacker: CombatParticipant,
                                      defender: CombatParticipant,
                                      weapon: 'Weapon', total: int,
                                      context: Dict[str, Any]) -> int:
        for h in self.handlers_for(defender):
            total = h.modify_defense_roll(engine, attacker, defender, weapon, total, context)
        return total

    def dispatch_modify_evasion(self, engine: AvaCombatEngine,
                                 defender: CombatParticipant,
                                 weapon: 'Weapon', bonus: int,
                                 context: Dict[str, Any]) -> int:
        for h in self.handlers_for(defender):
            bonus = h.modify_evasion(engine, defender, weapon, bonus, context)
        return bonus

    def dispatch_modify_block(self, engine: AvaCombatEngine,
                               defender: CombatParticipant,
                               weapon: 'Weapon', bonus: int,
                               context: Dict[str, Any]) -> int:
        for h in self.handlers_for(defender):
            bonus = h.modify_block(engine, defender, weapon, bonus, context)
        return bonus

    def dispatch_modify_damage(self, engine: AvaCombatEngine,
                                attacker: CombatParticipant,
                                defender: CombatParticipant,
                                weapon: 'Weapon', damage: int,
                                context: Dict[str, Any]) -> int:
        for h in self.handlers_for(attacker):
            damage = h.modify_damage(engine, attacker, defender, weapon, damage, context)
        return damage

    def dispatch_on_hit(self, engine: AvaCombatEngine,
                         attacker: CombatParticipant,
                         defender: CombatParticipant,
                         weapon: 'Weapon', result: Dict[str, Any]) -> None:
        for h in self.handlers_for(attacker):
            h.on_hit(engine, attacker, defender, weapon, result)

    def dispatch_on_miss(self, engine: AvaCombatEngine,
                          attacker: CombatParticipant,
                          defender: CombatParticipant,
                          weapon: 'Weapon', result: Dict[str, Any]) -> None:
        for h in self.handlers_for(attacker):
            h.on_miss(engine, attacker, defender, weapon, result)

    def dispatch_on_evade_success(self, engine: AvaCombatEngine,
                                   defender: CombatParticipant,
                                   attacker: CombatParticipant,
                                   weapon: 'Weapon') -> None:
        for h in self.handlers_for(defender):
            h.on_evade_success(engine, defender, attacker, weapon)

    def dispatch_on_graze(self, engine: AvaCombatEngine,
                           attacker: CombatParticipant,
                           defender: CombatParticipant,
                           weapon: 'Weapon',
                           context: Dict[str, Any]) -> None:
        for h in self.handlers_for(defender):
            h.on_graze(engine, attacker, defender, weapon, context)

    def dispatch_on_block_success(self, engine: AvaCombatEngine,
                                   defender: CombatParticipant,
                                   attacker: CombatParticipant) -> None:
        for h in self.handlers_for(defender):
            h.on_block_success(engine, defender, attacker)

    def dispatch_on_turn_start(self, engine: AvaCombatEngine,
                                participant: CombatParticipant) -> None:
        for h in self.handlers_for(participant):
            h.on_turn_start(engine, participant)

    def dispatch_modify_initiative(self, participant: CombatParticipant,
                                    bonus: int) -> int:
        for h in self.handlers_for(participant):
            bonus = h.modify_initiative(participant, bonus)
        return bonus

    def dispatch_modify_stealth(self, participant: CombatParticipant,
                                 mod: int, engine: AvaCombatEngine) -> int:
        for h in self.handlers_for(participant):
            mod = h.modify_stealth(participant, mod, engine)
        return mod

    def dispatch_on_critical_action(self, participant: CombatParticipant,
                                     action_name: str,
                                     context: Dict[str, Any]) -> bool:
        """Return True if ANY handler suppresses the death save."""
        for h in self.handlers_for(participant):
            if h.on_critical_action(participant, action_name, context):
                return True
        return False


# ============================================================================
# Offensive feat handlers
# ============================================================================

class DuelingStanceHandler(FeatHandler):
    feat_name = "Dueling Stance"

    def _is_dueling(self, actor: CombatParticipant, weapon: Weapon) -> bool:
        return (weapon is not None
                and not weapon.is_two_handed
                and actor.weapon_offhand is None
                and actor.shield is None)

    def modify_attack_roll(self, engine, attacker, defender, weapon, total, ctx):
        if self._is_dueling(attacker, weapon):
            ctx["dueling_bonus"] = 1
            return total + 1
        return total

    def modify_damage(self, engine, attacker, defender, weapon, damage, ctx):
        if self._is_dueling(attacker, weapon):
            return damage + 1
        return damage

    def on_graze(self, engine, attacker, defender, weapon, ctx):
        """Dueling Stance parry: on graze, defender with single 1H can attempt parry."""
        # This is a defender feat check, called for defender's feats
        parry_weapon = defender.weapon_main
        if not parry_weapon:
            return
        if not self._is_dueling(defender, parry_weapon):
            return
        if parry_weapon.name not in {"Dagger", "Rapier", "Arming Sword"}:
            return
        in_range = True
        if engine.tactical_map:
            dist = engine.tactical_map.manhattan_distance(
                defender.position[0], defender.position[1],
                attacker.position[0], attacker.position[1])
            in_range = dist <= 1
        if not in_range:
            return
        from .dice import roll_2d10
        parry_roll, pr_dice = roll_2d10()
        is_parry_crit = (pr_dice[0] == 10 and pr_dice[1] == 10)
        parry_total = parry_roll + parry_weapon.accuracy_bonus - 1
        engine.log(f"{defender.character.name} attempts a Parry! Roll {pr_dice} -> {parry_total}")
        if parry_total >= 12 or is_parry_crit:
            defender.parry_bonus_next_turn = True
            engine.log(f"Parry successful! Grazing hit deflected. {defender.character.name} gains +1 damage on next turn while single-wielding.")
            ctx["parry_deflected"] = True


class LineageWeaponHandler(FeatHandler):
    feat_name = "Lineage Weapon"

    def modify_attack_roll(self, engine, attacker, defender, weapon, total, ctx):
        if not (attacker.lineage_weapon or attacker.lineage_weapon_alt):
            return total
        if weapon and (weapon.name == attacker.lineage_weapon or weapon.name == attacker.lineage_weapon_alt):
            aim_bonus = 1
            # LW: Questing Bane upgrade
            if attacker.has_feat("LW: Questing Bane") and defender and hasattr(defender, "creature_type"):
                if defender.creature_type in attacker.slain_species:
                    aim_bonus = 2
            ctx["lineage_aim_bonus"] = aim_bonus
            if attacker.active_lineage_element:
                ctx["attack_element"] = attacker.active_lineage_element
            return total + aim_bonus
        return total


class LWQuestingBaneHandler(FeatHandler):
    """Track slain species for Questing Bane. Aim bonus handled by LineageWeaponHandler."""
    feat_name = "LW: Questing Bane"

    def on_hit(self, engine, attacker, defender, weapon, result):
        if defender.is_dead and hasattr(defender, "creature_type"):
            attacker.slain_species.add(defender.creature_type)


class PreciseSensesHandler(FeatHandler):
    feat_name = "Precise Senses"

    def modify_attack_roll(self, engine, attacker, defender, weapon, total, ctx):
        # Negate hidden/darkness penalties - these are added elsewhere, we cancel them
        penalty_removed = 0
        if defender.has_status(_get_status("HIDDEN")):
            penalty_removed += 3
        if getattr(engine, "environment_darkness", False):
            penalty_removed += 2
        if penalty_removed > 0:
            ctx["precise_senses_restored"] = penalty_removed
        # Don't add here - we prevent the penalty from being applied in the first place
        # The engine applies the penalties, then we restore them
        return total


class ParryHandler(FeatHandler):
    feat_name = "Parry"

    def modify_defense_roll(self, engine, attacker, defender, weapon, total, ctx):
        if defender.can_use_limited("Parry"):
            engine.log(f"{defender.character.name} parries, reducing attack by 2 (now {total - 2}).")
            return total - 2
        return total


class RakishCombinationHandler(FeatHandler):
    feat_name = "Rakish Combination"

    def on_hit(self, engine, attacker, defender, weapon, result):
        if weapon.name != "Unarmed":
            return
        if result.get("damage", 0) <= 0 and not result.get("is_graze"):
            return
        str_ath = attacker.character.get_modifier("Strength", "Athletics")
        base_unarmed = 2 + (3 if str_ath >= 5 else 2 if str_ath >= 3 else 1 if str_ath >= 1 else 0)
        attacker.next_unarmed_bonus = "aim" if base_unarmed >= 4 else "damage"


class BacklineFlankerHandler(FeatHandler):
    feat_name = "Backline Flanker"

    def modify_damage(self, engine, attacker, defender, weapon, damage, ctx):
        if not attacker.has_status(_get_status("HIDDEN")):
            return damage
        if not engine.tactical_map:
            return damage
        dx, dy = defender.position
        for nx, ny in engine.tactical_map.get_neighbors(dx, dy):
            tile = engine.tactical_map.get_tile(nx, ny)
            if tile and hasattr(tile, 'occupant') and tile.occupant is not None:
                from .participant import CombatParticipant as CP
                if isinstance(tile.occupant, CP):
                    other = tile.occupant
                    if other is not attacker and other is not defender:
                        engine.log(f"Backline Flanker: +1 damage applied for flanking from hidden.")
                        ctx["flanker_bonus"] = True
                        return damage + 1
        return damage

    def on_miss(self, engine, attacker, defender, weapon, result):
        if attacker.has_status(_get_status("HIDDEN")):
            attacker.ignore_next_conceal_penalty = True
            engine.log(f"Backline Flanker: next Conceal ignores -3 penalty.")


class AberrationSlayerHandler(FeatHandler):
    feat_name = "Aberration Slayer"

    def modify_damage(self, engine, attacker, defender, weapon, damage, ctx):
        chosen = getattr(attacker, "aberration_slayer_type", None)
        if chosen and hasattr(defender, "creature_type") and defender.creature_type == chosen:
            engine.log(f"Aberration Slayer: +1 damage vs {chosen}.")
            return damage + 1
        return damage


class StrategicArcherHandler(FeatHandler):
    feat_name = "Strategic Archer"

    def on_hit(self, engine, attacker, defender, weapon, result):
        from .enums import RangeCategory
        if weapon.range_category != RangeCategory.RANGED:
            return
        if not engine.tactical_map:
            return
        ax, ay = attacker.position
        dx, dy = defender.position
        atile = engine.tactical_map.get_tile(ax, ay)
        dtile = engine.tactical_map.get_tile(dx, dy)
        if atile and dtile and (atile.height - dtile.height) >= 3:
            bonus = defender.take_damage(1, armor_piercing=result.get("is_ap", False))
            result["damage"] = result.get("damage", 0) + bonus
            engine.log(f"Strategic Archer: high ground bonus +1 damage applied.")


class ControlHandler(FeatHandler):
    feat_name = "Control"

    def modify_damage(self, engine, attacker, defender, weapon, damage, ctx):
        if id(defender) in getattr(attacker, "control_wall_bonus_targets", set()):
            engine.log("Control: wall pressure grants +1 damage.")
            return damage + 1
        return damage

    def on_hit(self, engine, attacker, defender, weapon, result):
        control_weapons = {"Spear", "Polearm", "Greatsword", "Large Shield"}
        if weapon.name not in control_weapons:
            return
        wall_blocked = engine._apply_control_push(attacker, defender, 4)
        if wall_blocked:
            attacker.control_wall_bonus_targets.add(id(defender))
            engine.log("Control: target is pinned against a wall; +1 damage on subsequent attacks this turn.")


class MightyStrikeHandler(FeatHandler):
    feat_name = "Mighty Strike"

    def on_hit(self, engine, attacker, defender, weapon, result):
        mighty_weapons = {
            "Greatsword", "Greataxe", "Sling", "Staff", "Crossbow",
            "Mace", "Large Shield", "Unarmed"
        }
        if weapon.name in mighty_weapons:
            engine.apply_knockback(defender, 3, source_pos=attacker.position,
                                   source_name=attacker.character.name)


class ForwardChargeHandler(FeatHandler):
    feat_name = "Forward Charge"

    def on_hit(self, engine, attacker, defender, weapon, result):
        if weapon.name in {"Greatsword", "Polearm", "Staff"}:
            attacker.forward_charge_ready = True
            engine.log(f"Forward Charge primed: next Topple/Shove cannot be evaded or blocked.")


# ============================================================================
# Defensive feat handlers
# ============================================================================

class QuickfootedHandler(FeatHandler):
    feat_name = "Quickfooted"

    def on_evade_success(self, engine, defender, attacker, weapon):
        engine.apply_knockback(defender, 2, source_pos=attacker.position,
                               source_name=defender.character.name)


class GalestormStanceHandler(FeatHandler):
    feat_name = "Galestorm Stance"

    def on_evade_success(self, engine, defender, attacker, weapon):
        d_wep = defender.weapon_main or defender.weapon_offhand
        if d_wep and d_wep.name in {"Greatsword", "Polearm", "Staff"}:
            defender.evades_since_last_turn = getattr(defender, "evades_since_last_turn", 0) + 1


class ReactiveStanceHandler(FeatHandler):
    feat_name = "Reactive Stance"

    def on_evade_success(self, engine, defender, attacker, weapon):
        engine._reactive_maneuver(defender, attacker)


class EvasiveTacticsHandler(FeatHandler):
    feat_name = "Evasive Tactics"

    def on_graze(self, engine, attacker, defender, weapon, ctx):
        if defender.is_critical and not defender.graze_buffer_used:
            defender.suppress_death_save_once = True
            defender.graze_buffer_used = True

    def on_critical_action(self, participant, action_name, ctx):
        if action_name in {"riposte", "parry"}:
            return True  # Suppress death save
        return False


class DeathsDanceHandler(FeatHandler):
    feat_name = "Death's Dance"

    def on_critical_action(self, participant, action_name, ctx):
        if not participant.free_action_while_critical_used:
            participant.free_action_while_critical_used = True
            return True  # Suppress death save
        return False


class ShieldmasterHandler(FeatHandler):
    feat_name = "Shieldmaster"

    def modify_block(self, engine, defender, weapon, bonus, ctx):
        from .enums import RangeCategory
        if ctx.get("ignore_shieldmaster"):
            return bonus
        melee_bonus_weapons = {
            "Unarmed", "Arming Sword", "Dagger", "Rapier", "Mace", "Spear",
            "Polearm", "Whip", "Meteor Hammer", "Throwing Knife", "Staff",
            "Recurve Bow"
        }
        extra = 0
        if weapon.name in melee_bonus_weapons:
            extra += 3
        if weapon.range_category == RangeCategory.RANGED:
            extra += 1
        return bonus + extra


class ShieldWallHandler(FeatHandler):
    feat_name = "Shield Wall"

    def modify_block(self, engine, defender, weapon, bonus, ctx):
        from .enums import RangeCategory
        if weapon.range_category == RangeCategory.RANGED and engine._has_shield_wall(defender):
            return bonus + 1
        return bonus


class BastionStanceHandler(FeatHandler):
    feat_name = "Bastion Stance"
    # Mainly active ability; knockback immunity is in apply_knockback


# ============================================================================
# Turn lifecycle handlers
# ============================================================================

class FirstStrikeHandler(FeatHandler):
    feat_name = "First Strike"

    def modify_initiative(self, participant, bonus):
        return bonus + 5  # Replaces Always Ready's +3

    def on_turn_start(self, engine, participant):
        if not participant._first_turn_used:
            participant.actions_remaining = 3
            participant._first_turn_used = True


class AlwaysReadyHandler(FeatHandler):
    feat_name = "Always Ready"

    def modify_initiative(self, participant, bonus):
        # Only add +3 if First Strike isn't present (First Strike gives +5 and replaces this)
        if participant.has_feat("First Strike"):
            return bonus  # First Strike handler adds +5
        return bonus + 3


class SkirmishingPartyHandler(FeatHandler):
    feat_name = "Skirmishing Party"

    def modify_stealth(self, participant, mod, engine):
        # This feat boosts NEARBY allies, not the feat holder.
        # Logic: iterate allies in range and give them +1.
        # But since this is called for the participant checking stealth,
        # we need the inverse: check if any ally with this feat is nearby.
        # This is handled in participant.get_stealth_modifier's registry call.
        return mod


# ============================================================================
# Utility: StatusEffect access
# ============================================================================

def _get_status(name: str):
    """Helper to get StatusEffect by name without circular import at module level."""
    from .enums import StatusEffect
    return getattr(StatusEffect, name)


# ============================================================================
# Global registry singleton
# ============================================================================

def build_default_registry() -> FeatRegistry:
    """Create and return a FeatRegistry with all feat handlers registered."""
    registry = FeatRegistry()

    # Offensive
    registry.register(DuelingStanceHandler())
    registry.register(LineageWeaponHandler())
    registry.register(LWQuestingBaneHandler())
    registry.register(PreciseSensesHandler())
    registry.register(ParryHandler())
    registry.register(RakishCombinationHandler())
    registry.register(BacklineFlankerHandler())
    registry.register(AberrationSlayerHandler())
    registry.register(StrategicArcherHandler())
    registry.register(ControlHandler())
    registry.register(MightyStrikeHandler())
    registry.register(ForwardChargeHandler())

    # Defensive
    registry.register(QuickfootedHandler())
    registry.register(GalestormStanceHandler())
    registry.register(ReactiveStanceHandler())
    registry.register(EvasiveTacticsHandler())
    registry.register(DeathsDanceHandler())
    registry.register(ShieldmasterHandler())
    registry.register(ShieldWallHandler())
    registry.register(BastionStanceHandler())

    # Turn lifecycle
    registry.register(FirstStrikeHandler())
    registry.register(AlwaysReadyHandler())
    registry.register(SkirmishingPartyHandler())

    return registry


# Default singleton used by the engine
FEAT_REGISTRY = build_default_registry()
