import copy
import sys
from collections import deque
from typing import Dict

from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QTabWidget,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from avasim import Character, STATS
from combat import (
    AVALORE_ARMOR,
    AVALORE_SHIELDS,
    AVALORE_WEAPONS,
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
)
from combat.enums import RangeCategory, StatusEffect


class CombatantEditor(QGroupBox):
    """Editor widget for a single combatant."""

    def __init__(self, title: str, parent: QWidget | None = None):
        super().__init__(title, parent)
        self.setLayout(QVBoxLayout())

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Name")

        self.hp_input = self._spin_box(0, 200, 20)
        self.anima_input = self._spin_box(0, 50, 0)
        self.max_anima_input = self._spin_box(0, 50, 0)

        # Stats
        self.stat_spins: Dict[str, QSpinBox] = {}
        stats_box = QGroupBox("Stats (-3..3)")
        stats_layout = QGridLayout()
        for idx, stat in enumerate(STATS.keys()):
            spin = self._spin_box(-3, 3, 0)
            self.stat_spins[stat] = spin
            stats_layout.addWidget(QLabel(stat), idx, 0)
            stats_layout.addWidget(spin, idx, 1)
        stats_box.setLayout(stats_layout)

        # Skills
        self.skill_spins: Dict[str, Dict[str, QSpinBox]] = {}
        skills_box = QGroupBox("Skills (-3..3)")
        skills_layout = QGridLayout()
        row = 0
        for stat, skills in STATS.items():
            skills_layout.addWidget(QLabel(f"{stat}"), row, 0)
            self.skill_spins[stat] = {}
            for col, skill in enumerate(skills, start=1):
                spin = self._spin_box(-3, 3, 0)
                self.skill_spins[stat][skill] = spin
                skills_layout.addWidget(QLabel(skill), row, col * 2 - 1)
                skills_layout.addWidget(spin, row, col * 2)
            row += 1
        skills_box.setLayout(skills_layout)

        # Equipment choices
        self.weapon_choice = QComboBox()
        self.weapon_choice.addItems(list(AVALORE_WEAPONS.keys()))
        self.weapon_choice.setCurrentText("Arming Sword")

        self.armor_choice = QComboBox()
        self.armor_choice.addItem("None")
        self.armor_choice.addItems(list(AVALORE_ARMOR.keys()))
        self.armor_choice.setCurrentText("Light Armor")

        self.shield_choice = QComboBox()
        self.shield_choice.addItem("(None)")
        self.shield_choice.addItems(list(AVALORE_SHIELDS.keys()))

        self.evade_check = QCheckBox("Evading this attack")
        self.block_check = QCheckBox("Blocking with shield")

        equip_box = QGroupBox("Equipment")
        equip_layout = QGridLayout()
        equip_layout.addWidget(QLabel("Weapon"), 0, 0)
        equip_layout.addWidget(self.weapon_choice, 0, 1)
        equip_layout.addWidget(QLabel("Armor"), 1, 0)
        equip_layout.addWidget(self.armor_choice, 1, 1)
        equip_layout.addWidget(QLabel("Shield"), 2, 0)
        equip_layout.addWidget(self.shield_choice, 2, 1)
        equip_layout.addWidget(self.evade_check, 3, 0, 1, 2)
        equip_layout.addWidget(self.block_check, 4, 0, 1, 2)
        equip_box.setLayout(equip_layout)

        # HP/Anima
        core_box = QGroupBox("Vitals")
        core_layout = QGridLayout()
        core_layout.addWidget(QLabel("Current HP"), 0, 0)
        core_layout.addWidget(self.hp_input, 0, 1)
        core_layout.addWidget(QLabel("Anima"), 1, 0)
        core_layout.addWidget(self.anima_input, 1, 1)
        core_layout.addWidget(QLabel("Max Anima"), 2, 0)
        core_layout.addWidget(self.max_anima_input, 2, 1)
        core_box.setLayout(core_layout)

        # Compose layout
        self.layout().addWidget(QLabel("Name"))
        self.layout().addWidget(self.name_input)
        self.layout().addWidget(stats_box)
        self.layout().addWidget(skills_box)
        self.layout().addWidget(equip_box)
        self.layout().addWidget(core_box)

    def _spin_box(self, min_val: int, max_val: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(value)
        return spin

    def to_participant(self) -> CombatParticipant:
        char = Character(name=self.name_input.text() or self.title())
        # apply stats
        for stat, spin in self.stat_spins.items():
            char.base_stats[stat] = int(spin.value())
        # apply skills
        for stat, skills in self.skill_spins.items():
            for skill, spin in skills.items():
                char.base_skills[stat][skill] = int(spin.value())

        # clamp HP to max
        max_hp = char.get_max_hp()
        current_hp = max(0, min(int(self.hp_input.value()), max_hp))
        char.current_hp = current_hp

        weapon = copy.deepcopy(AVALORE_WEAPONS[self.weapon_choice.currentText()])
        armor_name = self.armor_choice.currentText()
        armor = None if armor_name == "None" else copy.deepcopy(AVALORE_ARMOR[armor_name])
        shield_name = self.shield_choice.currentText()
        shield = None if shield_name == "(None)" else copy.deepcopy(AVALORE_SHIELDS[shield_name])

        participant = CombatParticipant(
            character=char,
            current_hp=current_hp,
            max_hp=char.get_max_hp(),
            anima=int(self.anima_input.value()),
            max_anima=int(self.max_anima_input.value()),
            weapon_main=weapon,
            armor=armor,
            shield=shield,
            is_evading=self.evade_check.isChecked(),
            is_blocking=self.block_check.isChecked(),
        )
        return participant


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AvaSim — Qt Combat Sandbox")
        self.resize(1000, 700)

        root_layout = QVBoxLayout()
        self.setLayout(root_layout)

        # Tabs: Character Editor and Simulation
        self.tabs = QTabWidget()
        root_layout.addWidget(self.tabs)

        # Character Editor Tab
        self.character_tab = QWidget()
        char_layout = QVBoxLayout()
        self.character_tab.setLayout(char_layout)

        editors_layout = QHBoxLayout()
        self.attacker_editor = CombatantEditor("Character 1")
        self.defender_editor = CombatantEditor("Character 2")
        editors_layout.addWidget(self.attacker_editor)
        editors_layout.addWidget(self.defender_editor)
        char_layout.addLayout(editors_layout)

        self.tabs.addTab(self.character_tab, "Character")

        # Simulation Tab
        self.simulation_tab = QWidget()
        sim_layout = QVBoxLayout()
        self.simulation_tab.setLayout(sim_layout)

        self.simulate_button = QPushButton("Run full combat")
        self.simulate_button.clicked.connect(self.run_simulation)
        sim_layout.addWidget(self.simulate_button)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Full Auto (both AI)",
            "Player controls Character 1",
        ])
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        sim_layout.addLayout(mode_row)

        player_action_row = QHBoxLayout()
        player_action_row.addWidget(QLabel("Character 1 actions:"))
        self.player_action1_combo = QComboBox()
        self.player_action2_combo = QComboBox()
        for combo in (self.player_action1_combo, self.player_action2_combo):
            combo.addItems(["Attack", "Evade", "Block", "Skip"])
        player_action_row.addWidget(self.player_action1_combo)
        player_action_row.addWidget(self.player_action2_combo)
        sim_layout.addLayout(player_action_row)
        self._set_player_controls_enabled(False)

        # Simple movement controls
        move_row = QHBoxLayout()
        move_row.addWidget(QLabel("Move to x:"))
        self.move_x = QSpinBox(); self.move_x.setRange(0, 99)
        move_row.addWidget(self.move_x)
        move_row.addWidget(QLabel("y:"))
        self.move_y = QSpinBox(); self.move_y.setRange(0, 99)
        move_row.addWidget(self.move_y)
        self.move_button = QPushButton("Move (Character 1)")
        move_row.addWidget(self.move_button)
        self.move_button.clicked.connect(self.move_attacker)
        sim_layout.addLayout(move_row)

        # Spell casting disabled; UI elements removed for now

        log_row = QHBoxLayout()
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        self.action_view = QTextEdit()
        self.action_view.setReadOnly(True)
        self.action_view.setPlaceholderText("Turn-by-turn actions will appear here.")
        left_col.addWidget(QLabel("Action Log"))
        left_col.addWidget(self.action_view)

        self.map_view = QTextEdit()
        self.map_view.setReadOnly(True)
        self.map_view.setPlaceholderText("Post-turn maps will appear here.")
        right_col.addWidget(QLabel("Map Log"))
        right_col.addWidget(self.map_view)

        log_row.addLayout(left_col)
        log_row.addLayout(right_col)
        sim_layout.addLayout(log_row)

        self.tabs.addTab(self.simulation_tab, "Simulation")

    def run_simulation(self):
        attacker = self.attacker_editor.to_participant()
        defender = self.defender_editor.to_participant()
        tactical_map = TacticalMap(10, 10)
        attacker.position = (0, 0)
        defender.position = (3, 0)
        tactical_map.set_occupant(*attacker.position, attacker)
        tactical_map.set_occupant(*defender.position, defender)

        engine = AvaCombatEngine([attacker, defender], tactical_map=tactical_map)

        # Override logger to keep output in-app (no stdout noise)
        def ui_log(message: str):
            engine.combat_log.append(message)

        engine.log = ui_log  # type: ignore

        engine.roll_initiative()

        turn_limit = 200  # safety to prevent infinite loops
        turns = 0
        while not engine.is_combat_ended() and turns < turn_limit:
            current = engine.get_current_participant()
            if current is None or current.current_hp <= 0:
                engine.advance_turn()
                turns += 1
                continue

            # Choose target: first alive opponent
            targets = [p for p in engine.participants if p is not current and p.current_hp > 0]
            if not targets:
                break
            target = targets[0]

            if self.mode_combo.currentText() == "Player controls Attacker" and current is attacker:
                self._execute_player_turn(engine, current, target)
            else:
                self._take_auto_actions(engine, current, target)

            engine._log_map_state(f"End turn: {current.character.name}")

            engine.advance_turn()
            turns += 1

        engine.combat_log.append(engine.get_combat_summary())

        action_lines = ["Combat finished", f"Turns executed: {turns}", "", "Combat Log:"] + engine.combat_log
        self.action_view.setPlainText("\n".join(action_lines))
        self.map_view.setPlainText("\n".join(engine.map_log))

    def move_attacker(self):
        attacker = self.attacker_editor.to_participant()
        defender = self.defender_editor.to_participant()
        tactical_map = TacticalMap(10, 10)
        attacker.position = (0, 0)
        defender.position = (3, 0)
        tactical_map.set_occupant(*attacker.position, attacker)
        tactical_map.set_occupant(*defender.position, defender)
        engine = AvaCombatEngine([attacker, defender], tactical_map=tactical_map)
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
        success = engine.action_move(attacker, int(self.move_x.value()), int(self.move_y.value()))
        if not success:
            engine.combat_log.append("Move failed.")
        engine._log_map_state("After move")
        engine.combat_log.append(engine.get_combat_summary())
        self.action_view.setPlainText("\n".join(engine.combat_log))
        self.map_view.setPlainText("\n".join(engine.map_log))

    def cast_spell(self):
        # Spell casting disabled in this UI for now.
        self.outcome_view.setPlainText("Spell casting is currently disabled.")

    def _on_mode_changed(self):
        player_mode = self.mode_combo.currentText() == "Player controls Character 1"
        self._set_player_controls_enabled(player_mode)

    def _set_player_controls_enabled(self, enabled: bool):
        self.player_action1_combo.setEnabled(enabled)
        self.player_action2_combo.setEnabled(enabled)

    def _selected_player_actions(self) -> list[str]:
        actions: list[str] = []
        for combo in (self.player_action1_combo, self.player_action2_combo):
            val = combo.currentText()
            if val != "Skip":
                actions.append(val)
        return actions

    def _execute_player_turn(self, engine: AvaCombatEngine, current: CombatParticipant, target: CombatParticipant) -> None:
        actions = self._selected_player_actions()
        for action in actions:
            if current.current_hp <= 0 or current.actions_remaining <= 0 or target.current_hp <= 0:
                break
            if action == "Attack":
                weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]
                if not engine.is_in_range(current, target, weapon):
                    engine.combat_log.append("Player attack out of range; action wasted.")
                    current.spend_actions(weapon.actions_required)
                    continue
                engine.perform_attack(current, target, weapon=weapon)
            elif action == "Evade":
                engine.action_evade(current)
            elif action == "Block":
                engine.action_block(current)

    def _take_auto_actions(self, engine: AvaCombatEngine, current: CombatParticipant, target: CombatParticipant) -> None:
        # Movement-to-range step before feats/attacks
        weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]
        self._move_to_preferred_range(engine, current, target, weapon)

        weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]

        # Aberration Slayer: set target type once for bonus damage
        if getattr(current, "has_feat", lambda x: False)("Aberration Slayer"):
            if getattr(target, "creature_type", None) and not getattr(current, "aberration_slayer_type", None):
                engine.action_set_aberration_target(current, target.creature_type)

        # Support inspirations: only fire when a third ally exists to avoid buffing the enemy
        allies = [p for p in engine.participants if p is not current and p is not target and p.current_hp > 0]
        if allies:
            if getattr(current, "has_feat", lambda x: False)("Rousing Inspiration") and engine.tactical_map:
                if any(not getattr(p, "inspired_scene", False) for p in allies):
                    res = engine.action_rousing_inspiration(current)
                    if res.get("used") and res.get("granted"):
                        return
            if getattr(current, "has_feat", lambda x: False)("Commanding Inspiration"):
                if any(getattr(p, "temp_attack_bonus", 0) < 1 for p in allies):
                    res = engine.action_commanding_inspiration(current)
                    if res.get("used") and res.get("granted"):
                        return

        # Defensive stance: Patient Flow / Bastion / Second Wind if low HP
        hp_ratio = current.current_hp / max(1, current.max_hp)
        if hp_ratio < 0.5:
            if getattr(current, "has_feat", lambda x: False)("Patient Flow"):
                if engine.action_patient_flow(current):
                    return
            if getattr(current, "has_feat", lambda x: False)("Bastion Stance") and current.shield:
                if engine.action_bastion_stance(current):
                    return
            if getattr(current, "has_feat", lambda x: False)("Second Wind"):
                if engine.action_second_wind(current):
                    return

        # Lineage Lacuna (scene) if clustered targets are nearby
        if getattr(current, "has_feat", lambda x: False)("LW: Lacuna") and engine.tactical_map:
            if not getattr(current, "lacuna_used_scene", False):
                cx, cy = target.position
                res = engine.action_lineage_lacuna(current, cx, cy)
                if res.get("used") and res.get("affected"):
                    return

        # Quickdraw (limited) if available and weapon supports it
        if getattr(current, "has_feat", lambda x: False)("Quickdraw") and weapon.name in {"Longbow", "Crossbow", "Sling"}:
            mode = "evade" if hp_ratio < 0.5 else "dash"
            used = engine.action_quickdraw(current, target, weapon, mode=mode)
            if used.get("used"):
                return

        # Hamstring (limited) if applicable weapon
        if getattr(current, "has_feat", lambda x: False)("Hamstring") and weapon.name in {"Whip", "Recurve Bow", "Crossbow"}:
            used = engine.action_hamstring(current, target, weapon)
            if used.get("used"):
                return

        # Fanning Blade for small/throwing style when multiple foes are nearby
        if getattr(current, "has_feat", lambda x: False)("Fanning Blade") and engine.tactical_map:
            allowed = {"Throwing Knife", "Meteor Hammer", "Sling", "Arcane Wand"}
            if weapon.name in allowed:
                cx, cy = target.position
                nearby = 0
                for nx in range(max(0, cx - 2), min(engine.tactical_map.width, cx + 3)):
                    for ny in range(max(0, cy - 2), min(engine.tactical_map.height, cy + 3)):
                        tile = engine.tactical_map.get_tile(nx, ny)
                        if tile and isinstance(tile.occupant, CombatParticipant) and tile.occupant is not current and tile.occupant.current_hp > 0:
                            nearby += 1
                if nearby >= 2:
                    used = engine.action_fanning_blade(current, weapon, cx, cy)
                    if used.get("used"):
                        return

        # Galestorm Strike (two-handed heavy) for burst knockdown potential
        if getattr(current, "has_feat", lambda x: False)("Galestorm Stance") and weapon.name in {"Greatsword", "Polearm", "Staff"}:
            used = engine.action_galestorm_strike(current, target, weapon)
            if used.get("used"):
                return

        # Whirling Devil: activate before moving through foes
        if getattr(current, "has_feat", lambda x: False)("Whirling Devil") and not current.whirling_devil_active:
            engine.action_whirling_devil(current)

        # Vault to close distance with defense if available
        if getattr(current, "has_feat", lambda x: False)("Combat Acrobat") and engine.tactical_map:
            dist = engine.get_distance(current, target)
            if dist > 1:
                tx, ty = target.position
                engine.action_vault(current, tx, ty)

        # Ranger's Gambit at melee with bows
        if getattr(current, "has_feat", lambda x: False)("Ranger's Gambit") and weapon.name in {"Recurve Bow", "Longbow"}:
            if engine.tactical_map:
                dist = engine.tactical_map.manhattan_distance(current.position[0], current.position[1], target.position[0], target.position[1])
                if dist <= 1:
                    used = engine.action_rangers_gambit(current, target, weapon)
                    if used.get("used"):
                        return

        # Piercing/AArmor piercer when target blocking with shield
        if target.shield and target.is_blocking and weapon.name in {"Arming Sword", "Dagger"}:
            if getattr(current, "has_feat", lambda x: False)("Piercing Strike"):
                used = engine.action_piercing_strike(current, target, weapon)
                if used.get("used"):
                    return
            if getattr(current, "has_feat", lambda x: False)("Armor Piercer"):
                used = engine.action_armor_piercer(current, target, weapon)
                if used.get("used"):
                    return

        # Feint to ignore Shieldmaster/Quickfooted if EV is low
        if getattr(current, "has_feat", lambda x: False)("Feint"):
            if self._expected_attack_value(current, target, weapon) < 1.0:
                used = engine.action_feint(current, target)
                if used.get("used"):
                    return

        # Trick Shot (ranged) choose effect: dazzling if not marked, else bodkin
        if getattr(current, "has_feat", lambda x: False)("Trick Shot") and weapon.range_category == RangeCategory.RANGED:
            effect = "dazzling" if not target.has_status(StatusEffect.MARKED) else "bodkin"
            used = engine.action_trick_shot(current, target, weapon, effect)
            if used.get("used"):
                return

        # Two Birds One Stone when a second target is lined up behind the first
        if getattr(current, "has_feat", lambda x: False)("Two Birds One Stone") and weapon.name in {"Crossbow", "Spellbook"}:
            if self._has_trailing_target(engine, current, target):
                used = engine.action_two_birds_one_stone(current, target, weapon)
                if used.get("used"):
                    return

        # Volley for bows if feat available
        if getattr(current, "has_feat", lambda x: False)("Volley") and weapon.name in {"Recurve Bow", "Longbow"}:
            used = engine.action_volley(current, target, weapon)
            if used.get("used"):
                return

        # Topple/Shove when Forward Charge primed
        if current.forward_charge_ready:
            used = engine.action_topple(current, target)
            if used.get("used") and used.get("success"):
                return
            used = engine.action_shove(current, target)
            if used.get("used") and used.get("success"):
                return

        # Hilt Strike as follow-up for two-handed weapons
        if getattr(current, "has_feat", lambda x: False)("Hilt Strike") and weapon.is_two_handed:
            used = engine.action_hilt_strike(current, target, weapon)
            if used.get("used"):
                return

        # Momentum Strike if already dashed
        if getattr(current, "has_feat", lambda x: False)("Momentum") and current.dashed_this_turn:
            used = engine.action_momentum_strike(current, target)
            if used.get("used"):
                return

        # Dual Striker when dual-wielding eligible weapons
        if getattr(current, "has_feat", lambda x: False)("Dual Striker") and current.weapon_main and current.weapon_offhand:
            used = engine.action_dual_striker(current, target)
            if used.get("used"):
                return

        # Vicious Mockery if present and attacks have poor EV
        expected_value = self._expected_attack_value(current, target, weapon)
        if getattr(current, "has_feat", lambda x: False)("Vicious Mockery") and expected_value < 0.8:
            used = engine.action_vicious_mockery(current, target)
            if used.get("used"):
                expected_value = self._expected_attack_value(current, target, weapon)

        # Decide stance mathematically based on stats and equipment
        self._choose_stance(engine, current, target)

        attack_cost = weapon.actions_required
        swings = 0
        while current.actions_remaining >= attack_cost and target.current_hp > 0 and swings < 2:
            if expected_value <= 0:
                break
            engine.perform_attack(current, target, weapon=weapon)
            swings += 1
            expected_value = self._expected_attack_value(current, target, weapon)

    # ======== Movement Helpers ========
    def _is_passable(self, tactical_map: TacticalMap, x: int, y: int) -> bool:
        tile = tactical_map.get_tile(x, y)
        if not tile or not tile.passable:
            return False
        if tile.occupant and isinstance(tile.occupant, CombatParticipant):
            return False
        return True

    def _movement_allowance(self, actor: CombatParticipant, use_dash: bool) -> int:
        base_movement = 5
        movement_penalty = actor.armor.movement_penalty_for(actor.character) if actor.armor else 0
        if actor.has_status(StatusEffect.SLOWED):
            movement_penalty -= 2
        base_allow = max(0, base_movement + movement_penalty)
        if use_dash:
            dash_bonus = 4
            return dash_bonus if actor.free_move_used else base_allow + dash_bonus
        return 0 if actor.free_move_used else base_allow

    def _reachable_tiles(self, tactical_map: TacticalMap, start: tuple[int, int], allowance: int) -> Dict[tuple[int, int], int]:
        reachable: Dict[tuple[int, int], int] = {}
        q = deque()
        q.append((start, 0))
        seen = {start}
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
                if tile.occupant and isinstance(tile.occupant, CombatParticipant):
                    continue
                seen.add((nx, ny))
                q.append(((nx, ny), new_cost))
        return reachable

    def _step_toward(self, tactical_map: TacticalMap, ax: int, ay: int, tx: int, ty: int, direction: int) -> tuple[int, int] | None:
        dx = tx - ax
        dy = ty - ay
        # Try axis with greater distance first
        axes = [(1 if dx > 0 else -1 if dx < 0 else 0, 0), (0, 1 if dy > 0 else -1 if dy < 0 else 0)]
        if abs(dy) > abs(dx):
            axes = axes[::-1]
        for sx, sy in axes:
            nx, ny = ax + direction * sx, ay + direction * sy
            if nx == ax and ny == ay:
                continue
            if self._is_passable(tactical_map, nx, ny):
                return (nx, ny)
        return None

    def _move_to_preferred_range(self, engine: AvaCombatEngine, current: CombatParticipant, target: CombatParticipant, weapon) -> None:
        if not engine.tactical_map:
            return
        dist = engine.get_distance(current, target)
        # Desired bands
        if weapon.range_category == RangeCategory.MELEE:
            desired_min, desired_max = 1, 1
        elif weapon.range_category == RangeCategory.SKIRMISHING:
            desired_min, desired_max = 2, 8
        else:
            desired_min, desired_max = 6, 30

        # If already in band, skip
        if desired_min <= dist <= desired_max:
            return

        # Compute reachable tiles for free move; if none fit, consider dash
        best = None
        best_score = None
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
                # Prefer in-band, then closer to band, then lower cost, then avoid using dash if possible
                in_band = desired_min <= new_dist <= desired_max
                rank = (0 if in_band else 1, score, cost, 1 if use_dash else 0)
                if best_score is None or rank < best_score:
                    best_score = rank
                    best = (x, y)
                    best_use_dash = use_dash
            if best_score and best_score[0] == 0:
                break  # found in-band without needing dash or with current mode

        if best and current.actions_remaining > 0:
            if best_use_dash:
                if not engine.action_dash(current, *best):
                    engine.action_move(current, *best)
            else:
                if not engine.action_move(current, *best):
                    engine.action_dash(current, *best)

    def _has_trailing_target(self, engine: AvaCombatEngine, attacker: CombatParticipant, first: CombatParticipant) -> bool:
        if not engine.tactical_map:
            return False
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
            if tile.occupant and isinstance(tile.occupant, CombatParticipant) and tile.occupant.current_hp > 0:
                other = tile.occupant
                if other is not attacker and other is not first:
                    return True
        return False

    # ======== Decision Helpers ========
    def _prob_2d10_at_least(self, threshold: int) -> float:
        # Exact probability for 2d10 >= threshold
        counts = [0] * 21  # index by sum
        total = 0
        for a in range(1, 11):
            for b in range(1, 11):
                s = a + b
                counts[s] += 1
                total += 1
        valid = sum(count for s, count in enumerate(counts) if s >= threshold)
        return valid / total if total else 0.0

    def _expected_soak(self, defender: CombatParticipant) -> float:
        armor = defender.armor
        if armor is None:
            return 0.0
        from combat.enums import ArmorCategory
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

    def _attack_mod_for_weapon(self, attacker: CombatParticipant) -> int:
        from combat.enums import RangeCategory
        weapon = attacker.weapon_main or AVALORE_WEAPONS["Unarmed"]
        if weapon.range_category == RangeCategory.MELEE:
            return attacker.character.get_modifier("Strength", "Athletics")
        else:
            return attacker.character.get_modifier("Dexterity", "Acrobatics")

    def _evasion_mod(self, defender: CombatParticipant) -> int:
        base = defender.character.get_modifier("Dexterity", "Acrobatics")
        if defender.armor:
            base += defender.armor.evasion_penalty
        return base

    def _expected_attack_value(self, attacker: CombatParticipant, defender: CombatParticipant, weapon) -> float:
        # Expected damage per action considering contested evasion
        attack_base = weapon.accuracy_bonus + self._attack_mod_for_weapon(attacker)
        ev_mod = self._evasion_mod(defender)

        # Compute P( (2d10 attack) - (2d10 evasion) > ev_mod - attack_base )
        # Build diff distribution
        diff_counts = {}
        total = 0
        for a in range(1, 11):
            for b in range(1, 11):
                for c in range(1, 11):
                    for d in range(1, 11):
                        diff = (a + b) - (c + d)
                        diff_counts[diff] = diff_counts.get(diff, 0) + 1
                        total += 1
        threshold = ev_mod - attack_base
        # strict > threshold
        valid = sum(count for diff, count in diff_counts.items() if diff > threshold)
        p_hit = valid / total if total else 0.0

        # Armor soak expectation
        soak = 0.0 if weapon.is_piercing() else self._expected_soak(defender)
        base_damage = max(0.0, weapon.damage - soak)
        expected = p_hit * base_damage
        # Normalize per action
        actions = max(1, weapon.actions_required)
        return expected / actions

    def _choose_stance(self, engine: AvaCombatEngine, current: CombatParticipant, target: CombatParticipant) -> None:
        # Decide between evade and block based on probabilities and HP
        hp_ratio = current.current_hp / max(1, current.max_hp)
        weapon = (target.weapon_main or AVALORE_WEAPONS["Unarmed"]) if target else AVALORE_WEAPONS["Unarmed"]

        # Block success probability
        p_block = 0.0
        if current.shield:
            threshold = current.shield.get_block_dc() - current.shield.block_modifier
            p_block = self._prob_2d10_at_least(threshold)

        # Evasion success approximation against target
        # Using contested model like expected attack calc, but swap roles
        attack_base = weapon.accuracy_bonus + self._attack_mod_for_weapon(target)
        ev_mod = self._evasion_mod(current)
        diff_counts = {}
        total = 0
        for a in range(1, 11):
            for b in range(1, 11):
                for c in range(1, 11):
                    for d in range(1, 11):
                        diff = (c + d) - (a + b)  # defender vs attacker
                        diff_counts[diff] = diff_counts.get(diff, 0) + 1
                        total += 1
        threshold = attack_base - ev_mod
        valid = sum(count for diff, count in diff_counts.items() if diff > threshold)
        p_evade = valid / total if total else 0.0

        # Strategy: if low HP and high defense chance, defend; otherwise attack
        defend = False
        if hp_ratio < 0.5 and max(p_evade, p_block) > 0.55:
            defend = True
        elif max(p_evade, p_block) > 0.7:
            defend = True

        if defend:
            # Prefer the better stance
            if p_block >= p_evade and current.shield:
                engine.action_block(current)
            else:
                engine.action_evade(current)
        else:
            # Clear stances by not re-applying; the engine resets per turn
            pass


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
