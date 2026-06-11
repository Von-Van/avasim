"""Structured validation for canonical AvaSim builds and scenarios."""

from __future__ import annotations

from typing import Dict, Iterable, List

from avasim import SKILL_MAX, SKILL_MIN, STAT_MAX, STAT_MIN, STATS

from .contracts import CharacterBuild, RunRequest, ScenarioConfig, ValidationIssue
from .enums import RangeCategory, TerrainType, validate_loadout
from .feats import AVALORE_FEATS
from .items import AVALORE_ARMOR, AVALORE_SHIELDS, AVALORE_WEAPONS
from .spells import AVALORE_SPELLS, MAGE_LEVELS, OPPOSED_DISCIPLINES


def _issue(code: str, path: str, message: str, severity: str = "error") -> ValidationIssue:
    return ValidationIssue(code=code, path=path, severity=severity, message=message)


def _requirement_value(build: CharacterBuild, requirement: str) -> int:
    if requirement in build.feats:
        return 1
    if ":" in requirement:
        stat, skill = requirement.split(":", 1)
        return build.stats.get(stat, 0) + build.skills.get(stat, {}).get(skill, 0)
    return build.stats.get(requirement, 0)


def _check_requirements(
    build: CharacterBuild,
    requirements: Dict[str, int],
    path: str,
    label: str,
) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for requirement, minimum in requirements.items():
        current = _requirement_value(build, requirement)
        if current < minimum:
            issues.append(
                _issue(
                    "requirement_not_met",
                    path,
                    f"{label} requires {requirement} >= {minimum}; current value is {current}.",
                )
            )
    return issues


def validate_build(build: CharacterBuild | dict, path: str = "build") -> List[ValidationIssue]:
    build = CharacterBuild.from_dict(build) if isinstance(build, dict) else build
    issues: List[ValidationIssue] = []
    if not build.name.strip():
        issues.append(_issue("missing_name", f"{path}.name", "Build name is required."))

    for stat in STATS:
        value = build.stats.get(stat, 0)
        if not STAT_MIN <= value <= STAT_MAX:
            issues.append(_issue("stat_out_of_range", f"{path}.stats.{stat}", f"{stat} must be between {STAT_MIN} and {STAT_MAX}."))
        for skill in STATS[stat]:
            skill_value = build.skills.get(stat, {}).get(skill, 0)
            if not SKILL_MIN <= skill_value <= SKILL_MAX:
                issues.append(_issue("skill_out_of_range", f"{path}.skills.{stat}.{skill}", f"{skill} must be between {SKILL_MIN} and {SKILL_MAX}."))

    if build.current_hp < 0:
        issues.append(_issue("invalid_hp", f"{path}.current_hp", "Current HP cannot be negative."))
    if build.max_hp is not None and build.current_hp > build.max_hp:
        issues.append(_issue("invalid_hp", f"{path}.current_hp", "Current HP cannot exceed max HP."))
    if build.anima < 0 or build.max_anima < 0 or build.anima > build.max_anima:
        issues.append(_issue("invalid_anima", f"{path}.anima", "Anima must be between zero and max Anima."))

    def _hand_base(hand: str) -> tuple:
        improvised = hand.startswith("Improvised ")
        return (hand[len("Improvised "):] if improvised else hand), improvised

    hands = [hand for hand in (build.hand1, build.hand2) if hand and hand != "(None)"]
    resolved_hands = [(hand, *_hand_base(hand)) for hand in hands]
    for hand, base, _improvised in resolved_hands:
        if base not in AVALORE_WEAPONS and base not in AVALORE_SHIELDS:
            issues.append(_issue("unknown_equipment", f"{path}.equipment", f"Unknown hand equipment: {hand}."))
    for hand, base, improvised in resolved_hands:
        if improvised and base in AVALORE_WEAPONS and AVALORE_WEAPONS[base].range_category == RangeCategory.RANGED:
            issues.append(_issue("improvised_ranged", f"{path}.equipment",
                                 f"{hand}: ranged weapon templates cannot be improvised."))
    weapon_names = [base for _, base, _i in resolved_hands if base in AVALORE_WEAPONS]
    if not validate_loadout(weapon_names):
        issues.append(_issue("invalid_loadout", f"{path}.equipment", "Selected weapons exceed the supported loadout limits."))
    if any(AVALORE_WEAPONS[name].is_two_handed for name in weapon_names) and len(hands) > 1:
        issues.append(_issue("two_handed_conflict", f"{path}.equipment", "A two-handed weapon cannot be combined with another hand item."))
    if build.armor != "None" and build.armor not in AVALORE_ARMOR:
        issues.append(_issue("unknown_armor", f"{path}.armor", f"Unknown armor: {build.armor}."))

    for hand, base, _improvised in resolved_hands:
        item = AVALORE_WEAPONS.get(base) or AVALORE_SHIELDS.get(base)
        if item is not None:
            issues.extend(_check_requirements(build, item.stat_requirements, f"{path}.equipment", hand))
    if build.armor in AVALORE_ARMOR:
        issues.extend(_check_requirements(build, AVALORE_ARMOR[build.armor].stat_requirements, f"{path}.armor", build.armor))

    for feat_name in build.feats:
        feat = AVALORE_FEATS.get(feat_name)
        if feat is None:
            issues.append(_issue("unknown_feat", f"{path}.feats", f"Unknown feat: {feat_name}."))
        else:
            issues.extend(_check_requirements(build, feat.stat_requirements, f"{path}.feats", feat_name))
    issues.extend(_validate_arcana(build, path))
    return issues


def _validate_arcana(build: CharacterBuild, path: str) -> List[ValidationIssue]:
    """Canonical arcane checks: known spells, the magic wheel, and mage tiers."""
    issues: List[ValidationIssue] = []
    opposed = OPPOSED_DISCIPLINES.get(build.primary_discipline, "")
    if build.primary_discipline and build.primary_discipline not in OPPOSED_DISCIPLINES:
        issues.append(_issue("unknown_discipline", f"{path}.primary_discipline",
                             f"Unknown primary discipline: {build.primary_discipline}."))
    for spell_name in build.spells:
        spell = AVALORE_SPELLS.get(spell_name)
        if spell is None:
            issues.append(_issue("unknown_spell", f"{path}.spells", f"Unknown spell: {spell_name}."))
            continue
        issues.extend(_check_requirements(build, spell.stat_requirements, f"{path}.spells", spell_name))
        if opposed and spell.discipline == opposed:
            issues.append(_issue(
                "opposed_discipline", f"{path}.spells",
                f"{spell_name} is {spell.discipline} - opposite {build.primary_discipline} on the magic wheel and cannot be learned."))
        if spell.tier == "capstone" and build.primary_discipline and spell.discipline != build.primary_discipline:
            issues.append(_issue(
                "foreign_capstone", f"{path}.spells",
                f"{spell_name} is the {spell.discipline} capstone; only the primary discipline's capstone is known."))
    if build.spells and not build.primary_discipline:
        issues.append(_issue("missing_discipline", f"{path}.primary_discipline",
                             "A mage must declare a primary discipline.", "warning"))
    if build.max_anima:
        pools = {anima for anima, _ in MAGE_LEVELS.values()}
        if build.max_anima not in pools:
            issues.append(_issue(
                "nonstandard_anima_pool", f"{path}.max_anima",
                f"Max anima {build.max_anima} does not match a mage level pool {sorted(pools)}.", "warning"))
        else:
            _, spell_cap = next(spec for spec in MAGE_LEVELS.values() if spec[0] == build.max_anima)
            learnable = [name for name in build.spells
                         if AVALORE_SPELLS.get(name)
                         and AVALORE_SPELLS[name].tier not in ("cantrip", "capstone")]
            if len(learnable) > spell_cap:
                issues.append(_issue(
                    "too_many_spells", f"{path}.spells",
                    f"{len(learnable)} learned spells exceed the {spell_cap} allowed at this anima pool.", "warning"))
    return issues


def validate_scenario(
    scenario: ScenarioConfig | dict,
    build_count: int = 0,
) -> List[ValidationIssue]:
    scenario = ScenarioConfig.from_dict(scenario) if isinstance(scenario, dict) else scenario
    issues: List[ValidationIssue] = []
    if not 1 <= scenario.width <= 40 or not 1 <= scenario.height <= 40:
        issues.append(_issue("invalid_dimensions", "scenario", "Scenario dimensions must be between 1 and 40."))
    seen_cells = set()
    wall_cells = set()
    for index, cell in enumerate(scenario.terrain):
        path = f"scenario.terrain[{index}]"
        if not (0 <= cell.x < scenario.width and 0 <= cell.y < scenario.height):
            issues.append(_issue("terrain_out_of_bounds", path, f"Terrain cell ({cell.x}, {cell.y}) is out of bounds."))
        if cell.terrain not in TerrainType._value2member_map_:
            issues.append(_issue("unknown_terrain", path, f"Unknown terrain type: {cell.terrain}."))
        if (cell.x, cell.y) in seen_cells:
            issues.append(_issue("duplicate_terrain", path, f"Terrain cell ({cell.x}, {cell.y}) is duplicated.", "warning"))
        seen_cells.add((cell.x, cell.y))
        if cell.terrain == "wall":
            wall_cells.add((cell.x, cell.y))

    seen_positions = set()
    for index, position in enumerate(scenario.positions[:build_count or None]):
        path = f"scenario.positions[{index}]"
        point = (int(position[0]), int(position[1]))
        if not (0 <= point[0] < scenario.width and 0 <= point[1] < scenario.height):
            issues.append(_issue("position_out_of_bounds", path, f"Position {point} is out of bounds."))
        if point in seen_positions:
            issues.append(_issue("duplicate_position", path, f"Position {point} is occupied by multiple builds."))
        if point in wall_cells:
            issues.append(_issue("position_on_wall", path, f"Position {point} is on an impassable wall."))
        seen_positions.add(point)
    if build_count and len(scenario.positions) < build_count:
        issues.append(_issue("missing_positions", "scenario.positions", "Not every build has an explicit starting position.", "warning"))
    if scenario.time_of_day not in {"day", "night"}:
        issues.append(_issue("invalid_time", "scenario.time_of_day", "Time of day must be day or night."))
    return issues


def validate_run_request(request: RunRequest | dict) -> List[ValidationIssue]:
    request = RunRequest.from_dict(request) if isinstance(request, dict) else request
    issues: List[ValidationIssue] = []
    if not request.builds:
        issues.append(_issue("missing_builds", "builds", "At least one build is required."))
    names = set()
    teams = set()
    has_ffa = False
    for index, build in enumerate(request.builds):
        issues.extend(validate_build(build, f"builds[{index}]"))
        if build.name in names:
            issues.append(_issue("duplicate_name", f"builds[{index}].name", f"Build name {build.name!r} is duplicated."))
        names.add(build.name)
        if build.team:
            teams.add(build.team)
        else:
            has_ffa = True
    if teams and has_ffa:
        issues.append(_issue("mixed_team_mode", "builds", "Team combatants and FFA combatants are mixed.", "warning"))
    issues.extend(validate_scenario(request.scenario, len(request.builds)))
    if request.execution.turn_limit < 1:
        issues.append(_issue("invalid_turn_limit", "execution.turn_limit", "Turn limit must be at least one."))
    return issues


def has_errors(issues: Iterable[ValidationIssue]) -> bool:
    return any(issue.severity == "error" for issue in issues)
