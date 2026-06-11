# Avalore Combat Mechanics — Reference & Coverage

This document summarizes the canonical Avalore rules that the combat engine
models, and tracks how faithfully each is implemented. Sources:

- Core mechanics — <https://avalore.net/mechanics>
- Extended mechanics — <https://avalore.net/extended-mechanics>
- Feats — <https://avalore.net/feats> (see [feats_catalog.md](feats_catalog.md))
- Arcane & Grimoire — <https://avalore.net/arcane>, <https://avalore.net/grimoire>
  (see [spells_catalog.md](spells_catalog.md))

Status key: ✅ implemented · ◑ partial / simplified · ⛔ not modelled (optional).

## Action economy

- **2 actions + up to 5 blocks of movement** per turn; movement is one unbroken
  chunk. Actions: Dash (+4), Evade, Attack, Use, Conceal, Ability, Block, Hide,
  Maneuver.
- **Limited rule (linchpin):** only **one** ability marked *Limited* may be used
  per turn — and this single budget is **shared** between feat abilities and
  maneuvers (Shove/Topple/Pull). Implemented as the `limited_action_used` flag in
  [`combat/participant.py`](../combat/participant.py); `can_use_limited()`,
  `consume_action(is_limited=True)` and `take_limited_action()` all draw from it.

| Rule | Status | Where |
|------|:------:|-------|
| 2 actions per turn | ✅ | `participant.actions_per_turn`, `consume_action` |
| One Limited per turn (feats + maneuvers share it) | ✅ | `participant.can_use_limited` / `consume_action` |
| Free 5-block move, Dash (+4) | ✅ | `engine.action_move` / `action_dash` |
| Weapon swap once per turn; multi-action weapons | ✅ | `participant.swap_weapons`, `weapon.actions_required` |

## Tests, attacks, evasion & blocking

- **Tests:** 2d10, DC 12, mixed success 10–12, flat modifiers (no advantage).
- **Evasion:** DEX:Acrobatics (capped at **+3**) vs the attack total; `≥` evades,
  `12+` but lower **grazes** (half damage in light/no armour, full in medium/heavy).
- **Critical (10,10):** cannot be blocked/evaded/grazed; deals AP damage (+2 for
  already-AP weapons).
- **Block:** shield roll, +1 vs ranged; cannot combine with Evade.

| Rule | Status | Where |
|------|:------:|-------|
| 2d10 / DC 12 resolution | ✅ | `engine.perform_attack`, `dice.roll_2d10` |
| Evade cap +3 (feat bonuses may exceed) | ✅ | `participant.get_evasion_modifier` |
| Graze: half in light/none, full in medium/heavy | ✅ | `engine.perform_attack` |
| Critical = unblockable/unevadable, AP (+2 if AP) | ✅ | `engine.perform_attack` |
| Block, +1 vs ranged | ✅ | `items.Shield.roll_block` |
| Non-proficiency −2, cover, line-of-sight | ✅ | `participant.get_weapon_penalty`, `engine` |
| Improvised weapons (−1 aim / −1 dmg; no feat synergy except Rage) | ✅ | `items.make_improvised_weapon`, `engine.perform_attack` |
| Improvised shields (−1 block; no shield-feat synergy except Rage) | ✅ | `items.make_improvised_shield` |

## Maneuvers & conditions (extended)

Initiation is an attack roll (Block/Evade may negate; a critical auto-succeeds),
followed by a skill contest. See `_resolve_*`/`_maneuver_*` helpers and the
`action_*` maneuvers in [`combat/engine.py`](../combat/engine.py).

| Maneuver | Status | Notes |
|----------|:------:|-------|
| Shove *(Limited)* | ✅ | Unarmed damage + push STR:Athletics (min 2); crit → Prone |
| Topple *(Limited)* | ✅ | Athletics/Finesse contest → Prone, no damage |
| Pull *(Limited)* | ✅ | Whip/Meteor Hammer; damage + pull adjacent |
| Grapple | ✅ | contest → Grappled; `action_grapple` |
| Disarm | ✅ | while grappling; drops weapon, ends grapple |
| Struggle | ✅ | break free; Death-Save exempt |
| **Prone** condition | ✅ | +1 to hit it, no move, no reactions; ends grapples |
| **Grappled** condition | ✅ | −3 to physical rolls, movement 0; melee attacks vs the target gain +1 aim per grappler |

## Stealth (extended)

| Rule | Status | Where |
|------|:------:|-------|
| Hide / Conceal (DEX:Stealth) | ✅ | `engine.action_hide` / `action_conceal` |
| Sneak Attack: +1, unblockable/unevadable; reveals attacker | ✅ | `engine.perform_attack` |
| Perception may negate a sneak | ✅ | `engine._sneak_detected` |

## Health, death & bleedout

- 20 HP → 0 = **Critical**. While Critical, taking damage or acting triggers a
  **Death Save** (2d10 + STR:Fortitude halved, round up; DC 12) unless the action
  is exempt (Evade, Block, Dash, Preparatory, Struggle, Hide, Conceal, Bardic,
  Perception). A crit (10,10) exits Critical with 1 HP.
- A failed Death Save → **Bleedout**: out of the fight, dying after HAR:Belief
  (min 1) turns unless **stabilized** (an ally spends 2 actions + INT:Healing in
  Melee). Healing for any amount lifts Critical/Bleedout.

| Rule | Status | Where |
|------|:------:|-------|
| Critical at 0 HP; Death Save (Fort halved, DC 12) | ✅ | `participant.resolve_death_save` |
| Death-Save-exempt action set | ✅ | `participant.DEATH_SAVE_EXEMPT_ACTIONS` |
| Bleedout chain + HAR:Belief countdown | ✅ | `participant._enter_bleedout`, `start_turn` |
| Stabilize (2 actions, INT:Healing, Melee) | ✅ | `engine.action_stabilize` |
| Crit success exits Critical (+1 HP) | ✅ | `participant.resolve_death_save` |
| Bleedout half-movement crawl | ✅ | no actions, but `engine.action_move` allows crawling at half movement |

## Environmental (extended, opt-in)

Light/darkness, uneven terrain, shallow/deep water, fall/fire/poison are
consent-based extended mechanics. Only partial darkness penalties are modelled
today (`engine.environment_darkness`); the rest are intentionally out of scope.

| Rule | Status |
|------|:------:|
| Darkness perception penalty | ◑ |
| Terrain / water / hazards (fall, fire, poison) | ⛔ (optional) |

## Spellcasting (arcane)

All 217 Grimoire spells are cataloged ([spells_catalog.md](spells_catalog.md));
30 combat-decisive spells are engine-wired via `SPELL_MECHANICS` in
[`combat/spells.py`](../combat/spells.py). The casting procedure follows
<https://avalore.net/arcane>:

- **Cantrips** succeed automatically — no roll, no anima.
- **Casting roll:** 2d10 + HAR:Arcana vs **DC 10** (`engine.perform_cast_spell`).
- **Critical cast (10,10):** succeeds and consumes **no anima** (and skips the
  overcast consequence).
- **Miscast (< 10):** the spell fails and **half** the anima cost is lost;
  casting in the **primary discipline** loses no anima.
- **Primary discipline:** +1 to its casting rolls; the **opposite** discipline
  on the magic wheel cannot be learned (Ichor↔Artifice, Tellurgy↔Ether,
  Cursesmithy↔Force) — enforced by `validate_build`.
- **Overcasting:** once per day, only if the cost fits the maximum pool. On a
  success, roll the canonical 1d6 consequence (scarring / Prone / −3
  INT:Perception / −1 STR rolls / −1 INT:Perception / numb hands); on a
  miscast the caster falls unconscious with 0 anima.
- **Mage levels:** anima pools 8/14/20/30 with 6/10/14/20 learned spells
  (validation warns when exceeded).
- **Action economy:** `engine.action_cast_spell` consumes the listed casting
  actions; Cast is not Death-Save exempt; multi-action rituals that exceed the
  per-turn budget cannot be cast in combat.
- Defensive interaction: spells flagged evadable/blockable resolve Evade/Block
  **against the casting roll** (e.g. Kinetic Array, Geokinesis, Pyrebolt).

| Rule | Status | Where |
|------|:------:|-------|
| DC 10 casting roll, cantrip auto-success | ✅ | `engine.perform_cast_spell` |
| Crit cast free; primary +1 and free miscast | ✅ | `engine.perform_cast_spell` |
| Overcast gate, 1d6 consequence table, unconscious on miscast | ✅ | `engine._apply_overcast_consequence` |
| Magic-wheel learning restriction, mage tiers | ✅ | `validation._validate_arcana` |
| Saves, AoE radius/target caps, damage-over-time, wards | ✅ | `engine._apply_spell_effects`, `participant._tick_damage_over_time` |
| Cooperative casting (4+ action rituals split between mages) | ⛔ | out-of-combat ritual support |

## Documented simplifications

- **Spell line AoEs** (Geokinesis, Atmokinesis): the 1×8 line is resolved
  against a single target; alternate elemental modes are not modelled.
- **Detain:** wired as the one-action kneel (Slowed); the two-action straight-
  to-Prone variant is not modelled.
- **Shell:** armour-rank-up is approximated as +1 soak for 5 rounds.
- **Blur / Obscura / Intrusion:** scene-length or re-save effects use fixed
  round counts and a single initial save.
- **Pierce Penumbra / Shriek / Nebula:** caster-centred areas are resolved
  around the chosen target point.
- **Burning (Atmokinesis, Pyrebolt):** the spend-an-action-to-extinguish
  option is not modelled; the burn runs its listed duration.
- **LW: Skewer:** the −1 falloff is applied per additional enemy **in the
  line** (canon counts enemies actually hit), so it matches canon exactly when
  every target is hit and is slightly conservative otherwise.
- **Overcast consequences:** hour/day-scale penalties persist for the rest of
  the combat; the −3/−1 perception and −1 STR penalties apply to perception
  contests, maneuver contests, and saves (not weapon aim).
- **Pounce:** vertical (5-block fall → Prone) is not modelled on the 2-D map.
- A number of Mutant/Vampiric and all Utility/Background feats are out-of-combat
  and are cataloged-only — see [feats_catalog.md](feats_catalog.md); likewise
  187 of 217 Grimoire spells are cataloged-only — see
  [spells_catalog.md](spells_catalog.md).
