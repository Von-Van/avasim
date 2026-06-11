"""Pure-Python conversion between canonical contracts and combat objects."""

from __future__ import annotations

import copy
from typing import Iterable, List

from avasim import Character

from .contracts import CharacterBuild, ScenarioConfig
from .enums import TerrainType
from .feats import AVALORE_FEATS
from .items import AVALORE_ARMOR, AVALORE_SHIELDS, AVALORE_WEAPONS
from .map import TacticalMap
from .participant import CombatParticipant


def build_to_participant(build: CharacterBuild | dict) -> CombatParticipant:
    build = CharacterBuild.from_dict(build) if isinstance(build, dict) else build
    character = Character(name=build.name)
    character.base_stats.update(build.stats)
    for stat, skills in build.skills.items():
        if stat in character.base_skills:
            character.base_skills[stat].update(skills)

    calculated_max_hp = character.get_max_hp()
    max_hp = int(build.max_hp) if build.max_hp is not None else calculated_max_hp
    current_hp = max(0, min(int(build.current_hp), max_hp))
    character.current_hp = current_hp

    weapon_main = None
    weapon_offhand = None
    shield = None

    def assign_hand(selection: str) -> None:
        nonlocal weapon_main, weapon_offhand, shield
        if not selection or selection == "(None)":
            return
        if weapon_main and weapon_main.is_two_handed:
            return
        if selection in AVALORE_WEAPONS:
            weapon = copy.deepcopy(AVALORE_WEAPONS[selection])
            if weapon.is_two_handed:
                weapon_main = weapon
                weapon_offhand = None
                shield = None
            elif weapon_main is None:
                weapon_main = weapon
            elif weapon_offhand is None:
                weapon_offhand = weapon
        elif selection in AVALORE_SHIELDS and shield is None:
            shield = copy.deepcopy(AVALORE_SHIELDS[selection])

    assign_hand(build.hand1)
    assign_hand(build.hand2)

    participant = CombatParticipant(
        character=character,
        current_hp=current_hp,
        max_hp=max_hp,
        anima=max(0, min(build.anima, build.max_anima)),
        max_anima=max(0, build.max_anima),
        weapon_main=weapon_main,
        weapon_offhand=weapon_offhand,
        armor=copy.deepcopy(AVALORE_ARMOR.get(build.armor)) if build.armor != "None" else None,
        shield=shield,
        feats=[copy.deepcopy(AVALORE_FEATS[name]) for name in build.feats if name in AVALORE_FEATS],
        team=build.team,
        creature_type=build.creature_type,
        lineage_weapon=build.lineage_weapon,
        lineage_weapon_alt=build.lineage_weapon_alt,
        lineage_elements=set(build.lineage_elements),
    )
    return participant


def builds_to_participants(builds: Iterable[CharacterBuild | dict]) -> List[CombatParticipant]:
    return [build_to_participant(build) for build in builds]


def scenario_to_map(
    scenario: ScenarioConfig | dict,
    participants: List[CombatParticipant],
) -> TacticalMap:
    scenario = ScenarioConfig.from_dict(scenario) if isinstance(scenario, dict) else scenario
    tactical_map = TacticalMap(scenario.width, scenario.height)
    terrain_costs = {
        "forest": 2,
        "water": 2,
        "mountain": 3,
        "road": 1,
        "wall": 999,
    }
    for cell in scenario.terrain:
        tile = tactical_map.get_tile(cell.x, cell.y)
        if tile is None:
            continue
        tile.terrain_type = (
            TerrainType(cell.terrain)
            if cell.terrain in TerrainType._value2member_map_
            else TerrainType.NORMAL
        )
        tile.height = cell.height
        if cell.terrain == "wall":
            tile.passable = False
        elif cell.terrain in terrain_costs:
            tile.move_cost = terrain_costs[cell.terrain]

    positions = list(scenario.positions)
    for index, participant in enumerate(participants):
        position = positions[index] if index < len(positions) else _fallback_position(index, scenario)
        participant.position = (int(position[0]), int(position[1]))
        tactical_map.set_occupant(*participant.position, participant)
    return tactical_map


def _fallback_position(index: int, scenario: ScenarioConfig) -> List[int]:
    x = index % max(1, scenario.width)
    y = (index // max(1, scenario.width)) % max(1, scenario.height)
    return [x, y]
