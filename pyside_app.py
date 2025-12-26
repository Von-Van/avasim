import copy
import sys
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
    AVALORE_SPELLS,
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
)


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
        self.resize(1000, 800)

        layout = QVBoxLayout()
        self.setLayout(layout)

        editors_layout = QHBoxLayout()
        self.attacker_editor = CombatantEditor("Attacker")
        self.defender_editor = CombatantEditor("Defender")
        editors_layout.addWidget(self.attacker_editor)
        editors_layout.addWidget(self.defender_editor)

        self.simulate_button = QPushButton("Run full combat")
        self.simulate_button.clicked.connect(self.run_simulation)

        # Simple movement controls
        move_row = QHBoxLayout()
        move_row.addWidget(QLabel("Move to x:"))
        self.move_x = QSpinBox(); self.move_x.setRange(0, 99)
        move_row.addWidget(self.move_x)
        move_row.addWidget(QLabel("y:"))
        self.move_y = QSpinBox(); self.move_y.setRange(0, 99)
        move_row.addWidget(self.move_y)
        self.move_button = QPushButton("Move (attacker)")
        move_row.addWidget(self.move_button)
        self.move_button.clicked.connect(self.move_attacker)

        # Simple spell casting
        spell_row = QHBoxLayout()
        spell_row.addWidget(QLabel("Spell:"))
        self.spell_combo = QComboBox()
        self.spell_combo.addItems(list(AVALORE_SPELLS.keys()))
        spell_row.addWidget(self.spell_combo)
        self.cast_button = QPushButton("Cast (attacker -> defender)")
        spell_row.addWidget(self.cast_button)
        self.cast_button.clicked.connect(self.cast_spell)

        self.outcome_view = QTextEdit()
        self.outcome_view.setReadOnly(True)
        self.outcome_view.setPlaceholderText("Simulation results and combat log will appear here.")

        layout.addLayout(editors_layout)
        layout.addWidget(self.simulate_button)
        layout.addLayout(move_row)
        layout.addLayout(spell_row)
        layout.addWidget(QLabel("Outcome & Combat Log"))
        layout.addWidget(self.outcome_view)

    def run_simulation(self):
        attacker = self.attacker_editor.to_participant()
        defender = self.defender_editor.to_participant()

        engine = AvaCombatEngine([attacker, defender])

        # Capture stance preferences so we can reapply each turn
        stance = {
            id(attacker): (attacker.is_evading, attacker.is_blocking),
            id(defender): (defender.is_evading, defender.is_blocking),
        }

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

            # Reapply stance preferences each turn using proper actions
            ev, blk = stance.get(id(current), (False, False))
            if ev:
                engine.action_evade(current)
            if blk:
                engine.action_block(current)

            # Choose target: first alive opponent
            targets = [p for p in engine.participants if p is not current and p.current_hp > 0]
            if not targets:
                break
            target = targets[0]

            # Spend remaining actions on attacks while possible
            attack_cost = (current.weapon_main or AVALORE_WEAPONS["Unarmed"]).actions_required
            while current.actions_remaining >= attack_cost and target.current_hp > 0:
                engine.perform_attack(current, target, weapon=current.weapon_main)
                # Prevent runaway loops with multi-attack; at most two swings per turn
                if current.actions_remaining < attack_cost:
                    break
                # Limit to two swings to keep UI output concise
                if current.actions_per_turn - current.actions_remaining >= 2:
                    break

            engine.advance_turn()
            turns += 1

        engine.combat_log.append(engine.get_combat_summary())

        lines = ["Combat finished", f"Turns executed: {turns}", "", "Combat Log:"] + engine.combat_log
        self.outcome_view.setPlainText("\n".join(lines))

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
        engine.combat_log.append(engine.get_combat_summary())
        self.outcome_view.setPlainText("\n".join(engine.combat_log))

    def cast_spell(self):
        attacker = self.attacker_editor.to_participant()
        defender = self.defender_editor.to_participant()
        engine = AvaCombatEngine([attacker, defender])
        engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
        spell = AVALORE_SPELLS[self.spell_combo.currentText()]
        engine.perform_cast_spell(attacker, spell, defender)
        engine.combat_log.append(engine.get_combat_summary())
        self.outcome_view.setPlainText("\n".join(engine.combat_log))


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
