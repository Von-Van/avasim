# Avalore Feat Catalog

Every feat published at <https://avalore.net/feats> (100 total). This document is
generated from the scraped source of truth in
`tests/data/avalore_feats_source.json` and mirrors the runtime catalog in
[`combat/feats.py`](../combat/feats.py) (exported to `data/avalore/v1/feats.json`).

Regenerate the source with `python scripts/fetch_feats.py --emit json` and the
Python catalog with `python scripts/fetch_feats.py --emit python`.

**Status legend**

- ✅ **Engine-wired** — the feat has mechanical behaviour in the combat engine
  (a handler, an `action_*`, or inline resolution) and/or AI usage.
- 📋 **Cataloged** — present with faithful text and requirements, but its effect is
  out-of-combat or narrative and is not simulated by the combat engine.

**A `⏱ Limited` badge** marks abilities that consume the single "one Limited action
per turn" budget shared with maneuvers (Shove/Topple/Pull).

| Category | Feats | Engine-wired |
|----------|------:|-------------:|
| Combat | 43 | 43 |
| Lineage Weapon | 7 | 7 |
| Mutation | 11 | 7 |
| Vampiric | 12 | 2 |
| Utility | 18 | 0 |
| Backgrounds | 9 | 0 |
| **Total** | **100** | **59** |


## Combat

### ✅ Aberration Slayer — _Requires HAR 0_

A long history with slaying aberrations leaves them trembling in your wake, able to sense your deeds. Choose one of the following: Fae, Beast, or Undead. Whichever the holder chooses will generally avoid you unless they have a superior force, and when fighting them, do +1 extra damage on a successful hit.

### ✅ Always Ready — _Requires DEX 0_

You get a +3 to your initiative. When surprised or ambushed, you lose this bonus but may instead negate any additional received penalties (lost actions, attack penalties, etc.).

### ✅ Backline Flanker — _Requires DEX: Stealth +2_

You have a knack for spotting the right moment to attack a distracted foe while working in synergy with a friend. While Hidden, whenever you make a Skirmishing or Melee weapon attack against a target in melee distance of one or more of your allies you do so with deadly efficiency. If your attack lands, it deals +1 damage to that target; if it misses, you make your next conceal action without the -3 penalty.

### ✅ Bastion Stance ⏱ Limited — _Requires STR: Fortitude +3_

The majority of your focus shifts to defense as you hunker down using your Large Shield like a protective wall. As a limited action you Block and enter a Bastion Stance. While in your Bastion Stance, Shield Bashes are made with a +1 bonus, and successful bashes knock the enemy Prone. If you did not move on your turn, your Bastion Stance renders you immune to knockback, pulling, pushing, and Prone until the start of your next turn.

### ✅ Combat Acrobat — _Requires DEX: Acrobatics +2_

You can make a vault action, which acts as both a dash and an evade.

### ✅ Commanding Inspiration ⏱ Limited — _Requires HAR: Belief +3_

Your words and performance are enough to guide others through the heat of battle. As a single limited action using your voice, playing an instrument, or a motivational command, your efforts grant allies a +1 to weapon aim rolls up to +2 when stacked with another until the start of your next turn.

### ✅ Control — _Requires STR: Athletics +3_

Once per turn after landing an attack with a polearm, greatsword, or large shield, you may take 4m (blocks) of free movement and leverage your weapon to push the target wherever you move. If the target ends up adjacent to a wall or stable structure any subsequent attack in the same turn will deal +1 damage. This movement does not trigger Steadfast Defender against your target, nor does this move apply while in uneven terrain.

### ✅ Death's Dance — _Requires STR: Fortitude +1_

You fight on, even when your lifeblood drips upon the ground. While critical, once per turn, you can use any action (i.e. not only dash / evade) without triggering a Death Save. Cannot be taken with Evasive Tactics or Second Wind.

### ✅ Dual Striker ⏱ Limited — _Requires DEX +1_

With any combination of two: small blades, arming swords, finesse blades, meteor hammers, whips, maces, or fists (unarmed), you can dual attack as a single limited action. Each aim roll has a -1 penalty added to the weapon's normal aim roll. For any mechanics or feats that this interacts with (e.g. Riposte or Death Saves), it counts as only one attack action. You can also draw, stow, or swap both Dual Striker weapons at the same time using your one weapon swap.

### ✅ Dueling Stance — _Requires DEX: Acrobatics +2_

Your mastery of single-weapon fighting shines in single combat. Once (successfully) per round, when you suffer a Grazing hit (including Graze Piercing attacks), you may attempt to Parry using a held Arming Sword, Small Weapon, Finesse Blade, or Staff, provided you have not held or attacked using more than one weapon (incl. unarmed) in the last round. Parry: Make a weapon roll with a -1 modifier; the attacker must be within Melee range. On a success, the Grazing hit is treated as a full evasion and triggers any feat or spell that requires one. This reaction is mutually exclusive with Riposte. Counterattack: After a successful Parry, your next turn's single-weapon attacks deal +1 damage as long as you remain single-wielding.

### ✅ Evasive Tactics — _Requires DEX: Acrobatics +1_

Dodge and weave. When critical, the first grazing hit you take each round does not trigger a Death Save (including those that normally bypass grazing). Additionally, you may make Riposte Attacks or Parry without triggering a Death Save. Cannot be taken with Death's Dance or Second Wind.

### ✅ Fanning Blade ⏱ Limited — _Requires DEX: Acrobatics +3_

When wielding a throwing knife, meteor hammer, sling, or arcane wand, you spread your attack as a Limited Action: make one attack roll for every target in a 5x5 area in front of you, each with a flat -1 penalty. Any allies in this zone are also at risk of being hit and you must target everyone within the area.

### ✅ First Strike — _Requires DEX +1 and Always Ready feat_

The bonus from Always Ready is increased to +5. During the first turn of combat, you act with three actions instead of two.

### ✅ Forward Charge — _Requires STR: Athletics +1_

Carry forward, always. After landing an attack with a greatsword, polearm, or staff, your next Topple or Shove maneuver in the same turn cannot be evaded or blocked. If the maneuver is successful, you may immediately move forward 3m (3 blocks). This effect bypasses immunity to pushing and being knocked prone. Alternatively, after successfully Blocking with a shield you may move forward 3 blocks before performing a shield bash if you are capable.

### ✅ Galestorm Stance ⏱ Limited — _Requires DEX: Acrobatics +3_

You adopt a stance that channels the force of your dodges into your attacks. After evading one or more attacks while wielding a Greatsword, Polearm, or Staff, you may make a Galestorm Strike as a limited action instead of a regular Strike on the following turn with that weapon. Galestorm adds an additional attack roll for each successful, full evasion on the prior turn in addition to your base strike. Each hit after the first on the same target has its damage halved, rounded up (e.g. 6 damage -> 3 damage -> 2 damage -> 1 damage for four attacks). Attacks against different targets do full damage. Additional hits from a Galestorm on the same target do not trigger additional reaction attacks.

### ✅ Hamstring ⏱ Limited — _Requires INT: Perception +2_

You focus on a target with a whip, recurve, or crossbow - aiming not to kill, but to stall. This attack, made with a -1 to aim, cripples the target for one round, reducing all forms of movement by 2 blocks and applying a -2 penalty to Evasion.

### ✅ Harmonized Arsenal — _Requires DEX: Finesse +1_

Bladed small weapons now double as throwing knives/hatchets. Throwing knife attacks made with these weapons receive +1 to their aim. Aim bonus does not stack with Lineage Weapon.

### ✅ Hilt Strike — _Requires STR: Athletics +1 and DEX: Acrobatics +1_

You've mastered the use of every part of your weapon, even its handle. As an action before Lifting or after Striking with a two-handed melee weapon you can strike with the weapon's haft or hilt for half (non-AP) damage. Hilt Strikes do not trigger quickfooted, and bypass Grazing.

### ✅ Martial Discipline

You may draw, stow, or swap an Arming Sword and Shield together using a single weapon swap. Whenever you successfully Block an attack, add a stacking +1 aim modifier to Arming Sword attacks made on your next turn while wielding your Shield.

### ✅ Mighty Strike — _Requires STR: Athletics +2_

Your athletic prowess has the potential to reshape the battlefield. Your attack actions (not reactive attacks) using a Staff, Polearm, Mace, Small/Large Shield, Unarmed, Hilt Strike, Sling, or Crossbow may now knock the affected targets back 3 blocks.

### ✅ Momentum ⏱ Limited — _Requires STR: Athletics +2 and DEX: Acrobatics +1_

You become adept at directly converting the energy of your movement to that of your fist. After taking a Dash action, on the same turn, you may make an unarmed attack with +2 damage as a limited action. You take 1 AP damage from the extreme force you exert.

### ✅ Patient Flow ⏱ Limited — _Requires DEX +2_

As a limited action with at least one hand free, you Evade and enter a Flowing Stance. While in this stance, if you Evade an attack made from a Melee or Skirmishing weapon and there is another target (besides your attacker) within Melee range, make a Riposte or Unarmed attack roll against them with a -2 modifier. On a success, the incoming attack and its effects are redirected to that alternate target. The attack roll used to redirect does not deal damage. The new target may still Evade or Block the redirected attack, but cannot make a Riposte Attack or Shield Bash from it.

### ✅ Piercing Strike ⏱ Limited — _Requires STR 0_

You throw your weight behind your blow, half-sword, or strike at a gap in armour. When wielding an arming sword or small weapon, you can make an armour-piercing attack as a single limited action. If the target has AP immunity, the strike does +1 damage instead. After attempting a piercing strike, attacks made against you are made with a +1 modifier until the start of your next turn.

### ✅ Quickdraw ⏱ Limited — _Requires DEX +1_

While wielding a longbow, crossbow, or sling, you may take a Quickdraw action. This can act as either a Dash and Loose or Evade and Loose and must be declared. Quickdraw attacks are made with a -2 penalty and do 1 less damage than normal (4 AP for crossbow, 5 damage for longbow & sling).

### ✅ Quickfooted — _Requires DEX: Acrobatics +2_

When evading, add a +3 evasion bonus against attacks from Maces, Greatswords, Polearms, Slings, Javelins, and Longbows. Does not take effect if you are holding a Large Shield or wearing heavy armour. Upon fully evading any attack, you may immediately take 2 blocks of free movement.

### ✅ Rakish Combination — _Requires DEX: Finesse +1 and STR: Athletics +1_

You are renowned for your ability to build and maintain momentum with every blow. After successfully landing an Unarmed attack, if your next attack is also an Unarmed attack or Unarmed Maneuver, make it with a +1 bonus to aim (does not stack) OR deal full Unarmed damage (4, if applicable), regardless of your STR: Athletics . Multi-attacks only need to land one hit to keep the combination flowing, and each attack in a multi-attack receives the same bonus. The combination may extend between turns but will end upon using a different form of attack.

### ✅ Ranger's Gambit ⏱ Limited — _Requires DEX: Finesse +1 and STR: Athletics 0_

As a single limited action while wielding a recurve bow or longbow, you can make a point-blank shot with that weapon at a target in melee distance with -2 to the aim roll. This shot is AP, bypasses grazing hits, and can push the target back 3 blocks in the direction away from you. Whether you hit or miss, all attacks made against you with a melee weapon have +1 to their aim roll until the start of your next turn.

### ✅ Reactive Stance — _Requires DEX: Finesse +2_

You have trained in the art of using your enemy's momentum against them. While Unarmed, if you successfully Evade a hit you can take a free, immediate Maneuver action (including limited Maneuver actions) with a -1 modifier against the target that attacked you so long as they are within your Melee distance (cannot be used at the same time as another reaction). This Maneuver cannot be Evaded or Blocked.

### ✅ Riposte — _Requires DEX: Acrobatics +1_

While holding a small weapon, finesse blade, or arming sword, if you successfully evade a hit you can make a free, immediate Riposte Attack with that weapon against the person that attacked you so long as they are within your range. A Riposte Attack is a regular weapon roll made with a -1 modifier that cannot be evaded or blocked.

### ✅ Rousing Inspiration ⏱ Limited — _Requires HAR +1_

Your presence inspires others to persevere in the face of death. As a single limited action using your voice, playing an instrument, or with a motivational command, you can bolster all allies within skirmishing range. They gain temporary HP equal to your HAR +2, but may only be bolstered this way from any source once per scene.

### ✅ Second Wind — _Requires STR: Fortitude +1_

You shall not falter. Once per fight, during your turn, you can use an action to give yourself temporary HP equal to your STR: Fortitude + 2. Cannot be taken with Death's Dance or Evasive Tactics.

### ✅ Sentinel — _Requires STR +1 and Shield Bash feat_

You can now wield a Polearm with a Shield. Once per round after you have taken the Lift action on your turn, and after you successfully Block an attack with your Shield, you may Strike in retaliation using your Polearm or Javelin. This attack is mutually exclusive with Shield Bash and consumes your Lift action. This attack can be blocked or evaded, but does not trigger other reactions.

### ✅ Shield Bash — _Requires STR: Athletics +1_

While holding a small or large shield, every successful block allows you to make an immediate, free Shield Bash attack against your attacker with that shield. A Shield Bash is a regular small/large shield attack roll (/roll smallshield or /roll largeshield) that cannot be evaded or blocked.

### ✅ Shield Wall — _Requires STR: Athletics +3 and STR: Fortitude +2_

Form a line with another large shield user directly adjacent to your left, right, or both. While positioned this way, each of you add +1 to your Sentinel or Shield Bash attack aim and to block rolls made against ranged attacks. If your line holds its position this effect extends to Steadfast Defender attacks as well. The shield wall can be extended by others with this feat, however its effects do not stack.

### ✅ Shieldmaster — _Requires STR: Fortitude +1_

You are adept with a shield. Blocking against unarmed, arming sword, small weapon, finesse weapon, meteor hammer, whip, throwing knife, staff, or recurve bows all get an extra +3 to your block roll. Ranged attacks are blocked with an additional +1 modifier.

### ✅ Skirmishing Party — _Requires DEX: Stealth +1_

When in a group, all allies within Skirmishing distance of you make DEX: Stealth checks with a +1 modifier until your party is discovered. If your party attacks first, each member adds a +2 bonus to their initiative.

### ✅ Steadfast Defender — _Requires STR: Athletics +2 and DEX: Acrobatics 0_

When ending your turn without having moved and with a Polearm, Greatsword, or Meteor Hammer in hand, you brace and prepare. While in this state you are immune to knockback, pulling, or pushing. If any foe enters or exits your attack range before the start of your next turn, you get an immediate free attack against them with a -2 aim penalty. In the case of a Meteor Hammer you can make a second attack as they enter Melee distance from Skirmishing. This free attack can be Blocked or Evaded, but does not trigger other reactions.

### ✅ Strategic Archer

If higher than 3m (3 blocks) above your target, any hits with a ranged weapon do an extra +1 damage on a successful hit.

### ✅ Trick Shot — _Requires INT: Research +1_

Three times per scene, a ranged attack may use both actions to add one of the following effects: Bodkin (armour piercing); Whistling (bypasses grazing hits); Dazzling (-3 to spellcasts for one round); or Incendiary (target + those in Melee range take 3 damage from an explosive blast). The effect must be declared before the attack and is considered spent regardless of success. Trick Arrows used to interact with the environment outside of combat do so better than normal ones, with a +2 to those rolls.

### ✅ Two Birds One Stone ⏱ Limited — _Requires INT: Perception 0_

As a limited action, whenever you fire a Crossbow or use a Spellbook you can choose to have your bolt pierce one enemy and hit another behind them as long as they are in-line with you. Both targets must be within 5m (5 blocks) of each other and the second target does not take AP damage.

### ✅ Vicious Mockery — _Requires HAR +1_

Instead of serving as an inspiration, you channel your talents for ill. As an action, you can direct a scathing song, sonnet, or quip at a target within Ranged distance. They receive a -1 penalty to their skill checks OR attack, block, evade, & spellcast rolls for one round. This effect stacks with others up to a maximum of a -3 penalty.

### ✅ Volley ⏱ Limited — _Requires DEX +1_

With a recurve bow or longbow, you can take two rapid shots in quick succession in the same time as a normal attack (1 action for recurve, 2 actions for longbow). Each aim roll has a -1 penalty added to the weapon's normal aim roll. Can only be used once per turn.

### ✅ Whirling Devil ⏱ Limited — _Requires Combat Acrobat feat_

As a single limited action, you can strike at every enemy you pass with a melee weapon in hand. Roll to attack for each unique target you become adjacent to for the rest of the turn with a -1 modifier. Whirling Devil attacks can be blocked or evaded (triggering retaliatory attacks), and Whirling Devil attacks made with a two-action weapon deal half damage, rounded up.


## Lineage Weapon

### ✅ LW: Elemental — _Requires Lineage Weapon feat_

Select one of the following elemental effects: fire, lightning, ice, acid, or force. Your lineage weapon can attack with this elemental effect, with a visual flair matching the element. The effect of the element is at DM discretion.

### ✅ LW: Flexible Design ⏱ Limited — _Requires Lineage Weapon feat_

Select an additional weapon template. Your Lineage Weapon can switch between the two templates freely on your turn.

### ✅ LW: Lacuna — _Requires Lineage Weapon feat_

Once per scene for two actions, you can unleash the destructive power of your weapon. Pick a block within the range category of your weapon; all enemies within Melee distance of that block take damage equal to your number of Lineage Weapon feats. All enemies within Skirmishing distance of that block are knocked prone.

### ✅ LW: Mastery Of The Elements — _Requires LW: Elemental feat_

Your lineage weapon can attack with any of the five elements (fire, lightning, ice, acid, or force), with a visual flair matching the element. You must attune the weapon to a specific element when entering combat and it takes one action to switch it to a different element while in combat. The effects of the element are at DM discretion but are greater than they would be normally.

### ✅ LW: Questing Bane — _Requires Lineage Weapon feat_

'It grows as you do.' Lineage Weapon's bonus is upgraded to a +2 when facing a creature that belongs to a distinct species that it has assisted in slaying in a previous scene / event. Note down each unique species your Lineage Weapon has defeated.

### ✅ LW: Skewer ⏱ Limited — _Requires Lineage Weapon feat_

As a limited action, strike all enemies along a 2m (2 block) wide line stretching out 6m (6 blocks) behind the first target you hit or from a point within your weapon's range. For every additional enemy you hit after the first, you deal 1 less damage to all of them.

### ✅ Lineage Weapon — _Requires STR: Forging +1 and HAR: Belief +1_

Select one template weapon (excluding unarmed) to become your lineage weapon; it gains a permanent +1 aim modifier when used by you. The weapon may be visually remarkable in some mundane or low-magic way (e.g. glowing, exceptional metalwork, engineered design, coated in embers).


## Mutation

### ✅ Acidic Blood

Your blood sizzles like acid, melting through flesh and armour alike. When someone successfully hits you with an attack, they are dealt 1 damage in return. If that hit was part of a maneuver, the damage is 1 AP. When struck with a Critical Hit they are dealt 2 AP damage back. When you take the Struggle action, anyone who is grappling you is dealt 1 AP damage. Likewise, if you are grappling a target and they take the Struggle action, they are dealt 1 AP damage. These effects only apply within Melee distance. At DM discretion, splattered blood may have an effect. This otherwise offers little to no offensive capability (e.g. cannot be used on one's own fists).

### 📋 Adrenal Rush

You tap into unnatural strength at your most dire moments. Once per round immediately take any single action when entering Critical. This action is independent of your turn, can be Limited, and does not trigger a Death Save. Potent adrenaline courses through your veins as you walk the line of death; your movement from all sources is increased by +1 while Critical. Mutant-specific actions such as activating Rage no longer provoke a Death Save, but any self-inflicted damage or attacks made as part of a Mutant action will still trigger a normal Death Save.

### ✅ Ambush Predator

You are at your most dangerous when you catch your prey off guard. During the first round of combat, your rolls involving targets who have not had a turn yet are made with an extra +1 bonus.

### 📋 Corporeal Weapon

As a Weapon Swap per hand, you can reshape the flesh and bones of your arms until they resemble one-handed melee weapon templates of Average quality that still utilize the default stat requirements. Corporeal weapons count in place of Unarmed for other Mutant feats. Corporeal weapons cannot be a Lineage Weapon, and taking this feat will permanently reduce the number of weapons you can carry by 1.

### 📋 Eagle Eye — _Requires INT: Perception +1_

Your mutation allows you to see and aim at long distances. Your Ranged distance is increased from 30 to 35 blocks, and visual perception checks yield finer details than normal (e.g. what equipment someone is carrying, what they are doing, facial features & expressions, etc.) from up to 35 blocks with no negative modifiers related to distance.

### 📋 Inhuman Resilience — _Requires STR: Fortitude +1_

Your skin thickens and your bones harden like steel; Corporeal Weapons now count as Exceptional quality. Your body acts as medium armour, or may act as heavy if you have 4 or more mutant feats, excluding this one (does not stack with other armour rolls, can change once per scene). You still incur the evasion and ranged armour penalties, but do not need to meet the normal requirements to use that armour type, nor do you incur movement or DEX: Stealth penalties. Any damage mitigated can be flavoured as rapid regeneration and you seem to heal from some injuries in a matter of minutes.

### ✅ Pounce ⏱ Limited — _Requires STR: Athletics +2 and DEX: Acrobatics +1_

Using both actions, pounce to a point in Skirmishing distance (can be vertical). If you land within Melee distance of a target you may choose to make an Unarmed attack against them as a free action. If you were 5m+ (5+ blocks) above the target, your impact knocks them Prone before you roll to attack.

### ✅ Precise Senses

You have a supernatural relation to your senses. You incur no penalty in Dim lighting, roll all scent-and-sound-related perception checks with an additional +1 bonus, and can use an action to determine the direction of any smell without requiring a roll. When any target within Ranged distance does a Concealed action or Hides, you can make a free INT: Perception contest against their DEX: Stealth .

### ✅ Rage

Rip and tear; nothing is safe from your craving for violence. As an action you enter a rage-filled state for the duration of combat or scene at DM discretion. When doing so, any target within your Melee distance is knocked Prone. Your muscles flood with inhuman strength and you deal +1 damage on every successful hit. Your STR & DEX stats and derived mechanics are increased by +1 until the Rage subsides (applied after calculating other modifiers). Consequently, your INT & HAR stats and derived mechanics are temporarily reduced by -1 (Bleedout safe rounds remain minimum 1), and you take 1 damage each turn Rage is active. Once started, the Rage cannot be stopped until the situation ends, or until placated by a spell or relevant feat. When you enter Critical, the Rage ends immediately but may be re-activated using an action.

### ✅ Unyielding Reflex — _Requires DEX: Finesse +2_

Supernatural reflexes empower you. Once per round when you or a target within Melee distance of you is attacked by a Ranged weapon, you may make a DEX: Finesse check with a -2 modifier intercept the projectile, nullifying the hit and any of its effects on a success.

### ✅ Wounded Animal

A rapid burst of regeneration goes straight to the muscles necessary for escape--the heart, lungs, and legs. Once per scene on your turn, you can stabilize yourself for free during Bleedout. You immediately gain your entire base movement when stabilizing this way. Your Stabilized movement is normal instead of halved.


## Vampiric

### 📋 LW: Vampiric — _Requires Lineage Weapon feat and Vampire trait_

Boon: Your Lineage Weapon is corrupted through its attunement with your Vampiric curse, twisting its aesthetic and tarnishing its repute. For one round after striking a target with your Lineage Weapon, Bites against them grant +1 HP. Attacks from your Lineage Weapon apply a -1 modifier to the target's Death Save against that attack. Bane: Whispers of craving echo through your mind relentlessly whenever blood is drawn. At the start of your turn, if anybody within Skirmishing distance of you is on the brink of death (stabilized out of Bleedout) you must succeed a HAR: Belief check or else you are irresistibly compelled to finish them off, friend or foe.

### 📋 Monstrous Form — _Requires Vampire trait_

Boon: As a limited action, you may shift into or out of your Monstrous Form: Your figure grows gaunt and sinewy, any measure of physical appeal you might have carried before is utterly twisted until you are a disfigured husk of your former self. While in this state you gain heavy armour without its usual requirements or drawbacks; if you were already wearing heavy armour, you are no longer affected by its penalties. Non-silver weapons that deal AP damage to you now deal regular damage instead. This can be flavoured as regeneration from wounds sustained over the course of combat. Bane: While this form is active, you lose 1 HP at the start of your turn, all weapons made of silver deal AP damage to you, and weapons made from starsilver deal an additional +1 damage on top of it. Cannot be used while exposed to Daylight or its equivalent, which will cause the vampire to revert.

### 📋 Nocturnal Gaze — _Requires Vampire trait_

Boon: As a single limited action, your eyes ignite into a haunting glow, locking onto a single, visible target within Skirmishing distance. Regardless of eye-contact, they feel your gaze piercing into their soul, an incursion from the Nocturne. Make a contested HAR: Belief check with your prey. If you beat their roll, they are unable to move away from you or to make an effort that would carry them away (e.g. mounting a steed or falling over an edge) for one round. During this time, the target's HAR or INT based skill checks made against you and your spells are made with a -2 modifier (not including casting). Bane: In daylight the target need only pass a HAR: Belief check to resist. For a round after this ability is used, any form of resistance check you make against Cursesmithy spells is made with a -2 modifier.

### 📋 Persistent Hunter — _Requires Vampire trait_

Boon: Your time spent hunting prey has honed your senses and improved your capacity to stalk them. For the remainder of a scene after a successful Bite, that target's location is known to you while they are in Ranged distance; they cannot perform Sneak Attacks against you. When you make a successful Sneak Attack Bite against this target, you can draw extra blood for +1 HP. You can change which target you track by making another successful Bite. Bane: The limits of your tracking are tested by your fixation upon a single target. INT: Perception checks made against any other target than the one you are tracking are made with a -3 penalty.

### ✅ Razor Claws — _Requires Vampire trait_

Boon: Able to be formed or dismissed as a free action, you can brandish a set of small, sharp claws on each hand. Your Unarmed attacks bypass grazing and do not trigger Quickfooted. Bane: When struck by silver your claws become brittle for one round. Making an attack with them in this state causes them to break, dealing 1 AP damage back to yourself and rendering the attack useless against its intended target.

### 📋 Sensus Sanguinis — _Requires Vampire trait_

Boon: As an action to activate and deactivate, your eyes grow bloodshot and glaze over as you look into the sanguine. Your perception heightens toward those within Skirmishing distance with open wounds or who are below full HP, making their scent and heartbeat more noticable, and even letting their silhouette be 'seen' through walls - granting line of sight for any spell or ability that requires it. Targets spotted by your Sensus Sanguinis cannot Hide from you. Bane: This effect cannot be used in Daylight, and while it is active, all attacks against you are made with a +1 modifier.

### 📋 Skulker — _Requires Vampire trait_

Boon: You are supernaturally gifted at staying out of sight when avoiding the light. While in a Dim or Dark area, after making a successful Hide or Conceal check, your next Hide or Conceal check (not the action it is concealing) can be made as a free action that does not trigger free INT: Perception checks (this can chain across turns). While in a Dark area, you blend in with your surroundings; visual INT: Perception checks to spot you are made with an additional -1 penalty, even for those who can see in the dark. Bane: In daylight or the equivalent, all Hide or Conceal checks you make prompt a free INT: Perception check from those in Skirmishing distance of you as your vampiric guise is exposed.

### 📋 Smoke And Mirrors — _Requires Vampire trait_

Boon: As an action, or when Dashing, your form quickly dissolves into an illusory effect of your choosing (e.g smoke or mist) that allows you to bypass obstacles such as cell bars, a net trap, grapples, uneven terrain, or attacks that react to your movement. Non-living objects worn or carried on your person will come with you. You can move vertically in this state, but you will rematerialize when you stop moving, at the end of your turn, or when performing another (non-Dash) action. You can use normal movement speed while in mist form to extend its range. Bane: You cannot utilize this ability in daylight or the equivalent, nor after making contact with silver in the last round. The effect ends immediately should you come into contact with silver while in mist form (such as silver bars).

### 📋 Sommelier — _Requires Vampire trait_

Boon: You have an unparalleled understanding of the nuances of blood, much like a sommelier with wine; this allows you to re-identify blood you've tasted before. After tasting blood, you can determine if it belongs to an animal, mutant, mage, vampire, mundane, or combination thereof. Choose one specialization from the previous list (mundane implies purely mundane); your efforts to track a target via blood receive a +2 bonus if it matches your specialization, and yield +1 HP when you Bite them. Bane: Negative qualities in blood (i.e Saltblood, acidic blood, and toxic blood) are more potent to you; take an additional 2 AP dmg when consuming them.

### 📋 Supernatural Perch — _Requires Vampire trait_

Boon: You can crawl along vertical and horizontal planes such as walls and ceilings with halved movement. When doing so, you do not require a DEX: Stealth check to move stealthily. You can also hang or perch on these surfaces when not moving. You may Evade after moving, but can only Attack or Block if you did not move last round. Successful DEX: Acrobatics checks after falling now negate fall damage instead of halving it. Bane: You are unable to move in this way when exposed to silver. If struck by silver while crawling or perched, you will lose the ability to negate fall damage for one round and fall from that point.

### 📋 Tempered Fang — _Requires Vampire trait_

Boon: You've made a considerable effort to learn how to control your feeding urges. Your Bites now do 1 AP/GP damage, while still restoring you for 2 HP. This manner of feeding lessens the bloodloss on the target, with the typical after-effects staying only for 12 hours instead of 24. Attempts to resist the urge to feed can be made with a +3 modifier. Bane: Your Bites no longer impose a -1 penalty on Death Saves made against them.

### ✅ Vampiric Speed — _Requires Vampire trait_

Boon: As the moon rises, you feel your reflexes heighten; you feel good. After a successful Block or Evade (does not include grazed hits) you may make a free, immediate Dash unaffected by movement penalties. Your evasion rolls receive a +1 bonus (can exceed the base +3, but does not stack with other feat bonuses). Bane: This ability cannot be used in daylight or the equivalent, nor for one round after making contact with silver. You receive 1 less HP from Biting a target.


## Utility

### 📋 Animal Kinship — _Requires HAR: Nature +2_

You gain ownership and bond with a small creature (e.g. cats, stoats, snakes), which while unfit for combat can be useful for the right tasks. The pet is capable of following simple commands (go, stay, follow, fetch); more complex commands can be made with a successful HAR: Nature check. Their natural abilities allow them to fit through small spaces, produce simple sounds to warn of distress/interlopers, and carry small objects.

### 📋 Arcane Bloodline — _Requires HAR: Arcana 0_

An ancient mage with magic in their blood lay in your heritage. You gain the ability to use a single general cantrip (not a branch cantrip) even as a non-mage, and can cast it without limitation. A patron cantrip can only be used if an agreement is reached with that patron.

### 📋 Bardic Inspiration — _Requires HAR 0_

You've mastered the art of inspiring others to the point of improving their performance. As an action using your voice, playing an instrument, or a motivational instruction, you grant allies who hear it a +1 to skill checks (excluding spellcasting, evasion, blocking, attacking, and death saves) for one round. This effect stacks with others up to a maximum of +3.

### 📋 Bonded

Choose someone else that also has this feat, you two are bonded (the bond may be changed semi-regularly). You and your bonded benefit from the following: You share the same initiative in combat, taking the higher of your two rolls and discarding the lower - you can act at the same time; When one of you succeeds against a save test that includes both of you, you both succeed; and You act with a +1 on actions that directly apply to the other (healing, aid, etc.).

### 📋 Elementary ⏱ Limited — _Requires INT +1_

You can briefly test an action in your mind before committing to it. Once per round on your turn, when you take an action that requires a roll, you may make an Intelligence check first. On a success, you roll for the action as normal, then decide: - Follow through with the action and keep the result OR - Cancel the action and choose something else instead If you cancel, you cannot repeat the same action that triggered Elementary this turn.

### 📋 Hostile Architecture — _Requires STR: Forging +1_

You have a penchant for demolition; locked doors, walls, supports, chandeliers, etc. are no match for you. When using two actions with a suitable tool or spell, you may cause significant damage to an inanimate structure or surface at DM discretion. The destructive act will rarely directly harm you or your allies, but may lead to unexpected consequences. If any of the broken pieces are used as an improvised weapon, it functions without penalties.

### 📋 Lightning Speed

You are quick on your feet. If travelling on flat / even terrain, your passive movement is increased from 5 to 8. If travelling in uneven terrain or uphill, your movement is only increased to 6.

### 📋 Linguistics Expert — _Requires INT: Perception +2_

You have the ability to speak and understand all common languages. If you have an unobstructed view of someone's mouth, you can interpret most of what they're saying. Finally, you are able to craft ciphers that can only be understood by your intended targets, so long as you have significant history with or understanding of those targets.

### 📋 Pathworker — _Requires HAR: Nature +2_

Some consider you 'in tune' with the roads; Whenever engaging in significant overland travel you seem to always reap some boon, a DM may choose to give you a useful rumour, encounter, bonus, item, positional advantage, or similar when you declare this feat.

### 📋 Physician — _Requires INT: Healing +2_

You're a master of medicine, whether in a controlled environment or in the field. It only takes you one action to attempt to stabilize a target in Bleedout, and once per turn you can attempt to stabilize yourself as a free action. Additionally, all healing checks or checks to diagnose a target are rolled with an added +2 modifier.

### 📋 Ready Disguise — _Requires DEX: Stealth +2_

You always have the right fashion and makeup to forge a quick disguise. Once during a given scene/combat, you can fashion disguises for you and your party that fit a broad role (e.g. soldier, servant, bard) and receive the natural benefits of.

### 📋 Saboteur — _Requires DEX: Finesse +1 and INT: Research +1_

As an action, you can make an INT: Research check can be made to investigate any physical item (not a person). On a success, a subsequent DEX: Finesse check to disable, lockpick, or sabotage the item is made with a +3 modifier.

### 📋 Soaring Leap — _Requires STR: Athletics +2_

You can freely summit on top of walls up to four (4) blocks in height in a turn, without movement penalty or cost. For taller walls that can be climbed, you can leap four blocks up then proceed with normal climbing. You can also leap across gaps up to three (3) blocks wide, though this costs movement.

### 📋 Softstep — _Requires DEX: Stealth +2_

You are light on your feet. When wearing light or no armour, you leave no footprints, avoid stepping on noisy terrain (branches, creaky floorboards, etc), and leave minimal to no trace of your presence. While Hidden, you can move undetected without needing a DEX: Stealth roll unless someone is keeping watch.

### 📋 Spotter — _Requires INT: Perception 0_

Your keen eyes are well adjusted for keeping watch. As an action, you can make an INT: Perception check of your surroundings with a +2 modifier, and can see through obfuscation such as light fog, smoke, dense foliage, or near-darkness (dim lighting). You may still check through more intense conditions, such as Darkness, without penalty or bonus. This action may be used to spot Hidden targets so long as they are not fully concealed behind a solid material.

### 📋 Tinkerer — _Requires STR: Forging +1 and INT: Research +1_

You always seem to carry a menagerie of miscellaneous materials, and you have the know-how to employ them in creative ways. With a few minutes and the right inspiration, you can create an improvised version of nearly any tool. Make an INT: Research check with a -1 modifier. On success, you improvise that tool for the duration of the scene. If you fail, you're unable to plan out how to improvise that tool or don't have the parts you need. You can't try to make it again for the duration of the scene or event.

### 📋 Waking Dreamer — _Requires HAR: Arcana +3_

Closer to the Nocturne than most, you suffer from waking dreams and ticklings upon your hindbrain. A listener to the wakes of the conscious unconscious. Nothing is guaranteed, but anything is possible, you will be privy to whispers faraway, and stirrings of the world; But what is prophecy and what is nightmare? (Feat-owners will be given access to a private channel where semi-prophecies will be given by DMs, in addition to anything extra that may be given during events.)

### 📋 Well-Organized

You know how to organize your gear so perfectly that you can carry more with the same amount of space. You can carry an extra tool, consumable, weapon, and free carry weapon.


## Backgrounds

### 📋 Courtly Esteem

Your bearing and appearance hold the likeness of nobility. When interacting with nobles and their courts their tone may retain a degree of respect regardless of their personal opinion of you. You have an easier 'in' to social events that require high repute. You additionally have myriad connections throughout the realm. At the start of an event, you can call in a favour with a professional (e.g. an investigator, appraiser, scout, scholar) for information relevant to the event. It is at DM discretion what this professional can learn.

### 📋 Dubious Origins — _Requires DEX: Finesse +1_

There is honor among thieves, or so they say. In scenarios where you find yourself faced with shady individuals, thieves' guilds, or corrupt nobles, the way you carry yourself is recognized and accepted. You have an 'in' with these organizations and can communicate with their members through a thieves' cant. You are familiar enough with basic locks and traps to attempt to pick or disarm them without needing a proper tool

### 📋 Folk Hero

Be it through story or song, your good deeds are well known among serfs and commoners throughout the lands. You have an 'in' with common folk and may receive insight or basic supplies (ranging from home cooked meals to improvised weapons) to aid you in your journey. Once per event, you can make an INT: Perception or HAR: Belief check with a +2 modifier to look at a tough situation from a new perspective. On a success, you may receive inspiration from the DM to solve the problem in a creative or daring manner.

### 📋 Golden Touch

Whether a merchant trading fine silks, an experienced artisan, or an appraiser with a keen eye, you understand the intricacies of material goods. You have an 'in' with traders, craftsmen, and those of similar ilk. Once per item, you can study an object over the course of several minutes. Make an INT: Perception check to inspect its features, such as maker's marks, the materials in its construction, or place of origin. What can be learned is at DM discretion. Additionally, you gain access to a special NPC merchant that you can purchase rare and valuable materials from.

### 📋 Performer

Your name and talents bring a smile to the faces of many, even those in distant lands. Your attempts at performance—be it song, dance, acting, or theatrical acrobatics—are made with a +3 bonus, and you have an 'in' with people deemed as fans by a DM. You can fall from 8m (blocks) without taking damage, and add +3 to the DEX: Acrobatics check made when taking fall damage.

### 📋 Renowned

You have mastered combat with your weapon category of choice (one template picked from the Weapons Index) and drawn attention for it from past contests and feats of prowess. In fighting circles, your name is well known, and you may have an 'in' with NPC warriors. In addition, you may use the selected weapon template without penalties applied from it being improvised, broken, or affected by mundane effects such as vicious mockery. Penalties from magic or self-imposed penalties from feats still apply.

### 📋 Scholarly Acumen — _Requires INT: Research +1_

You've spent a long time in the halls of academia and know the ins-and-outs of scholarly debate. You have an 'in' with individuals and groups of higher learning, such as scholars and the academies they come from. Additionally, you've read and heard of many esoteric things. Three times per event, you can make an INT: Research check with an additional +2 bonus on any topic to see if you know something about it. At the DM's discretion you might not be able to use this for especially obscure things.

### 📋 Seafarer

The dark depths of the sea might intimidate others, but you are unfazed. Your time aboard vessels has given you a certain swagger characteristic of sailors, giving you an 'in' with other sea-faring individuals, and allows you to scale ropes, netting, and ladders with ease using your normal movement. Ships do not count as uneven terrain for you, and shallow water does not slow you.

### 📋 Trailblazer — _Requires HAR: Nature +1_

You've spent more time traversing the wild than most, and are capable of masking your presence to maximize your efficiency therein. Your bearing and knowledge marks you as one attuned to the wilds; you have an 'in' with other woodsmen and hunters. Your HAR: Nature checks add a +1 bonus, harvesting twice as much from wild plants and animals on a success. Dense foliage does not count as uneven terrain for you, and while Hidden, attempts to spot you through scent receive a -1 penalty to the check.

