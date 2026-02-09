from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
from .enums import RangeCategory


@dataclass
class SpellEffect:
    """Describes a secondary effect a spell can apply on the target."""
    status: str = ""              # e.g. "slowed", "prone", "vulnerable", "poisoned"
    duration_rounds: int = 1      # how long the status lasts
    penalty_type: str = ""        # e.g. "attack", "evasion", "spellcast", "all"
    penalty_value: int = 0        # e.g. -2
    push_blocks: int = 0          # knockback distance
    pull_blocks: int = 0          # pull toward caster


@dataclass
class Spell:
    name: str
    discipline: str               # Force, Ichor, Cursesmithy, Ether, Artifice, Tellurgy
    anima_cost: int
    actions_required: int = 1
    casting_dc: int = 10
    damage: int = 0
    healing: int = 0
    damage_type: str = "arcane"   # fire, ice, lightning, acid, force, psychic, arcane, necrotic
    range_category: RangeCategory = RangeCategory.RANGED
    requires_attack_roll: bool = False
    aoe_radius: int = 0           # 0 = single target; >0 = hits all enemies within N blocks of target
    save_stat: str = ""           # e.g. "Strength" - target rolls this stat+skill vs spell DC to resist
    save_skill: str = ""          # e.g. "Fortitude"
    save_dc: int = 12             # DC the target must meet to resist
    half_damage_on_save: bool = False   # if True, target takes half damage on successful save
    effects: List[SpellEffect] = field(default_factory=list)
    self_target: bool = False     # True = targets the caster (buffs/self-heals)
    ally_target: bool = False     # True = targets an ally (heals/buffs)
    description: str = ""

    def can_cast(self, character) -> bool:
        return character.anima >= self.anima_cost

# ─────────────────────────────────────────────────────────────────────
#  SPELL DEFINITIONS  (at least 3 per discipline)
# ─────────────────────────────────────────────────────────────────────

AVALORE_SPELLS: Dict[str, Spell] = {

    # ── FORCE ────────────────────────────────────────────────────────
    "Force Bolt": Spell(
        name="Force Bolt", discipline="Force", anima_cost=1,
        actions_required=1, damage=4, damage_type="force",
        range_category=RangeCategory.RANGED,
        effects=[SpellEffect(push_blocks=2)],
        description="A bolt of force energy. 4 damage, pushes target 2 blocks.",
    ),
    "Firebolt": Spell(
        name="Firebolt", discipline="Force", anima_cost=2,
        actions_required=1, damage=6, damage_type="fire",
        range_category=RangeCategory.RANGED,
        description="A searing bolt of flame. 6 fire damage.",
    ),
    "Shockwave": Spell(
        name="Shockwave", discipline="Force", anima_cost=3,
        actions_required=2, damage=4, damage_type="force",
        range_category=RangeCategory.SKIRMISHING, aoe_radius=2,
        save_stat="Dexterity", save_skill="Acrobatics", save_dc=12,
        half_damage_on_save=True,
        effects=[SpellEffect(status="prone", duration_rounds=1)],
        description="Slam the ground sending a shockwave outward. 4 force damage in 2-block radius; DEX:Acrobatics save for half and to avoid being knocked prone.",
    ),
    "Lightning Arc": Spell(
        name="Lightning Arc", discipline="Force", anima_cost=3,
        actions_required=2, damage=5, damage_type="lightning",
        range_category=RangeCategory.RANGED,
        description="A crackling arc of lightning. 5 lightning damage, armor-piercing.",
    ),

    # ── ICHOR ────────────────────────────────────────────────────────
    "Healing Touch": Spell(
        name="Healing Touch", discipline="Ichor", anima_cost=2,
        actions_required=1, healing=5,
        range_category=RangeCategory.MELEE, ally_target=True,
        description="Restore 5 HP to a touched ally or yourself.",
    ),
    "Mending Wave": Spell(
        name="Mending Wave", discipline="Ichor", anima_cost=4,
        actions_required=2, healing=3,
        range_category=RangeCategory.SKIRMISHING,
        aoe_radius=2, ally_target=True,
        description="A wave of restorative energy heals all allies within 2 blocks for 3 HP.",
    ),
    "Vitality Surge": Spell(
        name="Vitality Surge", discipline="Ichor", anima_cost=3,
        actions_required=1, healing=0,
        range_category=RangeCategory.MELEE, ally_target=True,
        effects=[SpellEffect(status="temp_hp", duration_rounds=3, penalty_value=4)],
        description="Grant an ally 4 temporary HP lasting 3 rounds.",
    ),
    "Purge Affliction": Spell(
        name="Purge Affliction", discipline="Ichor", anima_cost=2,
        actions_required=1,
        range_category=RangeCategory.MELEE, ally_target=True,
        effects=[SpellEffect(status="cleanse", duration_rounds=0)],
        description="Remove one negative status effect from a touched ally.",
    ),

    # ── CURSESMITHY ──────────────────────────────────────────────────
    "Hex of Weakness": Spell(
        name="Hex of Weakness", discipline="Cursesmithy", anima_cost=2,
        actions_required=1, damage=0, damage_type="necrotic",
        range_category=RangeCategory.RANGED,
        save_stat="Harmony", save_skill="Belief", save_dc=12,
        effects=[SpellEffect(penalty_type="attack", penalty_value=-2, duration_rounds=2)],
        description="Curse a target with -2 to attack rolls for 2 rounds. HAR:Belief save negates.",
    ),
    "Enfeeble": Spell(
        name="Enfeeble", discipline="Cursesmithy", anima_cost=3,
        actions_required=1, damage=2, damage_type="necrotic",
        range_category=RangeCategory.RANGED,
        save_stat="Strength", save_skill="Fortitude", save_dc=12,
        effects=[SpellEffect(status="slowed", duration_rounds=2)],
        description="Sap a target's strength. 2 necrotic damage and slowed for 2 rounds. STR:Fortitude save negates slow.",
    ),
    "Soul Drain": Spell(
        name="Soul Drain", discipline="Cursesmithy", anima_cost=4,
        actions_required=2, damage=5, damage_type="necrotic",
        range_category=RangeCategory.RANGED, healing=3,
        save_stat="Harmony", save_skill="Belief", save_dc=12,
        half_damage_on_save=True,
        description="Drain life from a target. 5 necrotic damage (half on save), caster heals 3 HP. HAR:Belief save.",
    ),

    # ── ETHER ────────────────────────────────────────────────────────
    "Mind Spike": Spell(
        name="Mind Spike", discipline="Ether", anima_cost=2,
        actions_required=1, damage=3, damage_type="psychic",
        range_category=RangeCategory.RANGED,
        save_stat="Intelligence", save_skill="Perception", save_dc=12,
        effects=[SpellEffect(penalty_type="spellcast", penalty_value=-2, duration_rounds=1)],
        description="Psychic lance. 3 psychic damage and -2 to spellcasting for 1 round. INT:Perception save negates the penalty.",
    ),
    "Phantasmal Terror": Spell(
        name="Phantasmal Terror", discipline="Ether", anima_cost=3,
        actions_required=2, damage=0, damage_type="psychic",
        range_category=RangeCategory.RANGED,
        save_stat="Harmony", save_skill="Belief", save_dc=12,
        effects=[SpellEffect(status="vulnerable", duration_rounds=2)],
        description="Fill a target's mind with dread. Target becomes Vulnerable for 2 rounds. HAR:Belief save negates.",
    ),
    "Veil of Shadows": Spell(
        name="Veil of Shadows", discipline="Ether", anima_cost=2,
        actions_required=1,
        range_category=RangeCategory.MELEE, self_target=True,
        effects=[SpellEffect(status="hidden", duration_rounds=2)],
        description="Cloak yourself in shadow. Gain Hidden status for 2 rounds.",
    ),

    # ── ARTIFICE ─────────────────────────────────────────────────────
    "Arcane Shield": Spell(
        name="Arcane Shield", discipline="Artifice", anima_cost=2,
        actions_required=1,
        range_category=RangeCategory.MELEE, self_target=True,
        effects=[SpellEffect(status="arcane_shield", duration_rounds=3, penalty_value=2)],
        description="Conjure a magical barrier granting +2 to evasion for 3 rounds.",
    ),
    "Animate Weapon": Spell(
        name="Animate Weapon", discipline="Artifice", anima_cost=3,
        actions_required=2, damage=4, damage_type="force",
        range_category=RangeCategory.SKIRMISHING,
        description="Animate your weapon to strike a target at skirmishing range. 4 force damage, armor-piercing.",
    ),
    "Ironhide": Spell(
        name="Ironhide", discipline="Artifice", anima_cost=3,
        actions_required=1,
        range_category=RangeCategory.MELEE, ally_target=True,
        effects=[SpellEffect(status="ironhide", duration_rounds=2, penalty_value=2)],
        description="Harden an ally's armor magically. +2 to armor soak rolls for 2 rounds.",
    ),

    # ── TELLURGY ─────────────────────────────────────────────────────
    "Stone Spike": Spell(
        name="Stone Spike", discipline="Tellurgy", anima_cost=2,
        actions_required=1, damage=5, damage_type="force",
        range_category=RangeCategory.SKIRMISHING,
        save_stat="Dexterity", save_skill="Acrobatics", save_dc=12,
        half_damage_on_save=True,
        description="Erupt a spike of stone beneath a target. 5 damage, DEX:Acrobatics save for half.",
    ),
    "Entangle": Spell(
        name="Entangle", discipline="Tellurgy", anima_cost=3,
        actions_required=2, damage=0,
        range_category=RangeCategory.SKIRMISHING, aoe_radius=2,
        save_stat="Strength", save_skill="Athletics", save_dc=12,
        effects=[SpellEffect(status="slowed", duration_rounds=2)],
        description="Vines erupt in a 2-block radius. Targets are Slowed for 2 rounds. STR:Athletics save negates.",
    ),
    "Tremor": Spell(
        name="Tremor", discipline="Tellurgy", anima_cost=4,
        actions_required=2, damage=3, damage_type="force",
        range_category=RangeCategory.SKIRMISHING, aoe_radius=3,
        save_stat="Dexterity", save_skill="Acrobatics", save_dc=12,
        half_damage_on_save=True,
        effects=[SpellEffect(status="prone", duration_rounds=1)],
        description="Shake the earth in a 3-block radius. 3 damage and knock prone. DEX:Acrobatics save for half damage and no prone.",
    ),
}
