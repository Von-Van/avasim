import copy
import sys
import os
from collections import deque
from typing import Dict
import json
import html
import csv
import io
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTabWidget,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QMenuBar,
    QTableWidget,
    QTableWidgetItem,
    QCheckBox,
    QProgressBar,
    QGraphicsScene,
    QGraphicsView,
    QSlider,
    QScrollArea,
    QSplitter,
    QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QFont, QAction, QColor, QBrush, QPen, QDesktopServices

from avasim import Character, STATS
from combat import (
    AVALORE_ARMOR,
    AVALORE_SHIELDS,
    AVALORE_WEAPONS,
    AVALORE_FEATS,
    Feat,
    AvaCombatEngine,
    CombatParticipant,
    TacticalMap,
)
from combat.ai import CombatAI
from combat.batch import BatchRunner, BatchConfig, BatchResult
from combat.enums import RangeCategory, StatusEffect, TerrainType
from ui import (
    Theme,
    ThemeManager,
    FontConfig,
    IconProvider,
    ProgressIndicator,
    TextHighlighter,
    TacticalMapWidget,
    TacticalMapWidget,
    CollapsibleSection,
)


# ---------------------------------------------------------------------------
# Batch Results Chart Dialog
# ---------------------------------------------------------------------------

class BatchChartDialog(QDialog):
    """Dialog that displays batch simulation results as bar charts."""

    def __init__(self, result: BatchResult, parent=None, title: str = "Batch Results"):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumSize(700, 520)
        layout = QVBoxLayout(self)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_qimage import FigureCanvasQTAgg  # type: ignore
        except ImportError:
            # Fallback: text-only display
            layout.addWidget(QLabel("Install matplotlib for chart display.\n\n" + result.summary()))
            btn = QDialogButtonBox(QDialogButtonBox.Ok)
            btn.accepted.connect(self.accept)
            layout.addWidget(btn)
            return

        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), tight_layout=True)

        # --- Win Rates bar chart ---
        rates = result.win_rates()
        teams = sorted(rates.keys())
        colors = ["#4e79a7", "#e15759", "#76b7b2", "#f28e2b", "#59a14f", "#af7aa1"]
        ax = axes[0]
        bars = ax.bar(teams, [rates[t] * 100 for t in teams],
                      color=colors[:len(teams)], edgecolor="#333", linewidth=0.5)
        ax.set_ylabel("Win Rate (%)")
        ax.set_title("Win Rates")
        ax.set_ylim(0, 100)
        for bar, t in zip(bars, teams):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    f"{rates[t]*100:.1f}%", ha="center", va="bottom", fontsize=8)

        # --- Average Damage bar chart ---
        avg_dmg = result.avg_damage_by_team()
        ax = axes[1]
        if avg_dmg:
            dmg_teams = sorted(avg_dmg.keys())
            ax.bar(dmg_teams, [avg_dmg[t] for t in dmg_teams],
                   color=colors[:len(dmg_teams)], edgecolor="#333", linewidth=0.5)
        ax.set_ylabel("Avg Damage")
        ax.set_title("Avg Damage / Combat")

        # --- Rounds distribution histogram ---
        rounds_data = [r.rounds for r in result.records]
        ax = axes[2]
        ax.hist(rounds_data, bins=min(20, max(5, len(set(rounds_data)))),
                color="#4e79a7", edgecolor="#333", linewidth=0.5)
        ax.set_xlabel("Rounds")
        ax.set_ylabel("Frequency")
        ax.set_title(f"Rounds Distribution (avg {result.avg_rounds():.1f})")

        # Render to QPixmap via buffer
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        buf.seek(0)
        plt.close(fig)

        from PySide6.QtGui import QPixmap, QImage
        img = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(img)
        chart_label = QLabel()
        chart_label.setPixmap(pixmap)
        chart_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart_label)

        # Summary text
        summary_text = QTextEdit()
        summary_text.setReadOnly(True)
        summary_text.setPlainText(result.summary())
        summary_text.setMaximumHeight(130)
        layout.addWidget(summary_text)

        btn = QDialogButtonBox(QDialogButtonBox.Ok)
        btn.accepted.connect(self.accept)
        layout.addWidget(btn)


# ---------------------------------------------------------------------------
# Loadout Comparison Dialog
# ---------------------------------------------------------------------------

class LoadoutComparisonDialog(QDialog):
    """Dialog showing side-by-side results for two batch runs (A vs B variant)."""

    def __init__(self, result_a: BatchResult, result_b: BatchResult,
                 label_a: str, label_b: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Loadout Comparison")
        self.setMinimumSize(750, 560)
        layout = QVBoxLayout(self)

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
        except ImportError:
            layout.addWidget(QLabel("Install matplotlib for chart display."))
            btn = QDialogButtonBox(QDialogButtonBox.Ok)
            btn.accepted.connect(self.accept)
            layout.addWidget(btn)
            return

        fig, axes = plt.subplots(1, 3, figsize=(10, 3.5), tight_layout=True)

        # Collect win rates for first team across both runs
        rates_a = result_a.win_rates()
        rates_b = result_b.win_rates()
        all_teams = sorted(set(list(rates_a.keys()) + list(rates_b.keys())))

        # --- Grouped Win Rate bar chart ---
        import numpy as np
        x = np.arange(len(all_teams))
        width = 0.35
        ax = axes[0]
        vals_a = [rates_a.get(t, 0) * 100 for t in all_teams]
        vals_b = [rates_b.get(t, 0) * 100 for t in all_teams]
        ax.bar(x - width/2, vals_a, width, label=label_a, color="#4e79a7", edgecolor="#333", linewidth=0.5)
        ax.bar(x + width/2, vals_b, width, label=label_b, color="#e15759", edgecolor="#333", linewidth=0.5)
        ax.set_xticks(x)
        ax.set_xticklabels(all_teams, fontsize=8)
        ax.set_ylabel("Win Rate (%)")
        ax.set_title("Win Rate Comparison")
        ax.set_ylim(0, 100)
        ax.legend(fontsize=7)

        # --- Average Damage comparison ---
        dmg_a = result_a.avg_damage_by_team()
        dmg_b = result_b.avg_damage_by_team()
        dmg_teams = sorted(set(list(dmg_a.keys()) + list(dmg_b.keys())))
        x2 = np.arange(len(dmg_teams))
        ax = axes[1]
        ax.bar(x2 - width/2, [dmg_a.get(t, 0) for t in dmg_teams], width,
               label=label_a, color="#4e79a7", edgecolor="#333", linewidth=0.5)
        ax.bar(x2 + width/2, [dmg_b.get(t, 0) for t in dmg_teams], width,
               label=label_b, color="#e15759", edgecolor="#333", linewidth=0.5)
        ax.set_xticks(x2)
        ax.set_xticklabels(dmg_teams, fontsize=8)
        ax.set_ylabel("Avg Damage")
        ax.set_title("Avg Damage Comparison")
        ax.legend(fontsize=7)

        # --- Rounds distribution overlay ---
        ax = axes[2]
        rounds_a = [r.rounds for r in result_a.records]
        rounds_b = [r.rounds for r in result_b.records]
        ax.hist(rounds_a, bins=15, alpha=0.6, label=label_a, color="#4e79a7", edgecolor="#333", linewidth=0.5)
        ax.hist(rounds_b, bins=15, alpha=0.6, label=label_b, color="#e15759", edgecolor="#333", linewidth=0.5)
        ax.set_xlabel("Rounds")
        ax.set_ylabel("Frequency")
        ax.set_title("Rounds Distribution")
        ax.legend(fontsize=7)

        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=120)
        buf.seek(0)
        plt.close(fig)

        from PySide6.QtGui import QPixmap, QImage
        img = QImage.fromData(buf.getvalue())
        pixmap = QPixmap.fromImage(img)
        chart_label = QLabel()
        chart_label.setPixmap(pixmap)
        chart_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(chart_label)

        # Delta summary
        summary = QTextEdit()
        summary.setReadOnly(True)
        summary.setMaximumHeight(140)
        lines = [f"=== Comparison: {label_a} vs {label_b} ===", ""]
        lines.append(f"{'Team':<12} {'WR (A)':>8} {'WR (B)':>8} {'Delta':>8}")
        lines.append("-" * 40)
        for t in all_teams:
            wa = rates_a.get(t, 0) * 100
            wb = rates_b.get(t, 0) * 100
            delta = wb - wa
            sign = "+" if delta >= 0 else ""
            lines.append(f"{t:<12} {wa:>7.1f}% {wb:>7.1f}% {sign}{delta:>6.1f}%")
        lines.append("")
        lines.append(f"Avg rounds: {result_a.avg_rounds():.1f} (A) vs {result_b.avg_rounds():.1f} (B)")
        summary.setPlainText("\n".join(lines))
        layout.addWidget(summary)

        btn = QDialogButtonBox(QDialogButtonBox.Ok)
        btn.accepted.connect(self.accept)
        layout.addWidget(btn)


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
        stats_box = QGroupBox("Stats (-3 - +3)")
        stats_layout = QGridLayout()
        for idx, stat in enumerate(STATS.keys()):
            spin = self._spin_box(-3, 3, 0)
            self.stat_spins[stat] = spin
            stats_layout.addWidget(QLabel(stat), idx, 0)
            stats_layout.addWidget(spin, idx, 1)
        stats_box.setLayout(stats_layout)

        # Skills
        self.skill_spins: Dict[str, Dict[str, QSpinBox]] = {}
        skills_box = QGroupBox("Skills (-3 - +3)")
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

        # Equipment choices (hands can take a weapon or a shield)
        hand_items = ["(None)"] + list(AVALORE_WEAPONS.keys()) + list(AVALORE_SHIELDS.keys())
        self._two_handed_names = {name for name, w in AVALORE_WEAPONS.items() if getattr(w, "is_two_handed", False)}
        self._weapon_names = set(AVALORE_WEAPONS.keys())
        self._large_shield_name = "Large Shield"
        self.hand1_choice = QComboBox(); self.hand1_choice.addItems(hand_items)
        self.hand1_choice.setCurrentText("Arming Sword")
        self.hand2_choice = QComboBox(); self.hand2_choice.addItems(hand_items)
        self.hand2_choice.setCurrentText("(None)")
        self.hand1_choice.currentTextChanged.connect(lambda _: self._refresh_hand_options())
        self.hand2_choice.currentTextChanged.connect(lambda _: self._refresh_hand_options())

        self.armor_choice = QComboBox()
        self.armor_choice.addItem("None")
        self.armor_choice.addItems(list(AVALORE_ARMOR.keys()))
        self.armor_choice.setCurrentText("Light Armor")

        equip_box = QGroupBox("Equipment")
        equip_layout = QGridLayout()
        equip_layout.addWidget(QLabel("Hand 1"), 0, 0)
        equip_layout.addWidget(self.hand1_choice, 0, 1)
        equip_layout.addWidget(QLabel("Armor"), 1, 0)
        equip_layout.addWidget(self.armor_choice, 1, 1)
        equip_layout.addWidget(QLabel("Hand 2"), 2, 0)
        equip_layout.addWidget(self.hand2_choice, 2, 1)
        equip_box.setLayout(equip_layout)

        self._equip_warning_label = QLabel("")
        self._equip_warning_label.setStyleSheet("color: #d32f2f; font-size: 9pt;")
        self._equip_warning_label.setWordWrap(True)
        self._equip_warning_label.hide()

        self._refresh_hand_options()
        # Connect equipment changes to requirement checks
        self.hand1_choice.currentTextChanged.connect(lambda _: self._check_equipment_requirements())
        self.hand2_choice.currentTextChanged.connect(lambda _: self._check_equipment_requirements())
        self.armor_choice.currentTextChanged.connect(lambda _: self._check_equipment_requirements())

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

        # Team assignment
        self.team_choice = QComboBox()
        self.team_choice.addItems(["Team A", "Team B", "Team C", "Team D", "FFA"])
        self.team_choice.setCurrentText("Team A")
        self.team_choice.setToolTip("Assign combatant to a team (FFA = no team)")

        # Compose layout
        self.layout().addWidget(QLabel("Name"))
        self.layout().addWidget(self.name_input)
        team_row = QHBoxLayout()
        team_row.addWidget(QLabel("Team:"))
        team_row.addWidget(self.team_choice)
        team_row.addStretch()
        self.layout().addLayout(team_row)
        self.layout().addWidget(stats_box)
        self.layout().addWidget(skills_box)
        self.layout().addWidget(equip_box)
        self.layout().addWidget(self._equip_warning_label)

        # Feat picker
        feat_box = QGroupBox("Feats (click ℹ for details)")
        feat_box.setCheckable(True)
        feat_box.setChecked(False)  # collapsed by default
        feat_layout = QGridLayout()
        feat_layout.setSpacing(2)
        self.feat_checks: Dict[str, QCheckBox] = {}
        row = 0
        for feat_name, feat_obj in sorted(AVALORE_FEATS.items()):
            cb = QCheckBox(feat_name)
            # Build a rich tooltip with description + requirements
            req_parts = []
            for req_key, req_val in feat_obj.stat_requirements.items():
                req_parts.append(f"{req_key} ≥ {req_val}")
            req_str = ", ".join(req_parts) if req_parts else "None"
            cb.setToolTip(f"{feat_obj.description}\n\nRequirements: {req_str}")
            feat_layout.addWidget(cb, row, 0)
            self.feat_checks[feat_name] = cb
            row += 1
        feat_scroll = QScrollArea()
        feat_scroll.setWidgetResizable(True)
        feat_inner = QWidget()
        feat_inner.setLayout(feat_layout)
        feat_scroll.setWidget(feat_inner)
        feat_scroll.setMaximumHeight(180)
        feat_box_layout = QVBoxLayout()
        feat_box_layout.addWidget(feat_scroll)
        feat_box.setLayout(feat_box_layout)

        self.layout().addWidget(feat_box)
        self.layout().addWidget(core_box)

        # Connect stat changes to equipment requirement checks
        for spin in self.stat_spins.values():
            spin.valueChanged.connect(lambda _: self._check_equipment_requirements())
        for skills in self.skill_spins.values():
            for spin in skills.values():
                spin.valueChanged.connect(lambda _: self._check_equipment_requirements())

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

        armor_name = self.armor_choice.currentText()
        armor = None if armor_name == "None" else copy.deepcopy(AVALORE_ARMOR[armor_name])

        hand1_sel = self.hand1_choice.currentText()
        hand2_sel = self.hand2_choice.currentText()

        weapon_main = None
        weapon_offhand = None
        shield = None

        def assign_hand(selection: str):
            nonlocal weapon_main, weapon_offhand, shield
            if weapon_main and getattr(weapon_main, "is_two_handed", False):
                return
            if not selection or selection == "(None)":
                return
            if selection in AVALORE_WEAPONS:
                weapon_obj = copy.deepcopy(AVALORE_WEAPONS[selection])
                if weapon_obj.is_two_handed:
                    weapon_main = weapon_obj
                    weapon_offhand = None
                    shield = None
                    return
                if weapon_main is None:
                    weapon_main = weapon_obj
                elif weapon_offhand is None:
                    weapon_offhand = weapon_obj
            elif selection in AVALORE_SHIELDS and shield is None:
                shield = copy.deepcopy(AVALORE_SHIELDS[selection])

        assign_hand(hand1_sel)
        assign_hand(hand2_sel)

        # Collect selected feats
        selected_feats = [
            AVALORE_FEATS[name] for name, cb in self.feat_checks.items() if cb.isChecked()
        ]

        participant = CombatParticipant(
            character=char,
            current_hp=current_hp,
            max_hp=char.get_max_hp(),
            anima=int(self.anima_input.value()),
            max_anima=int(self.max_anima_input.value()),
            weapon_main=weapon_main,
            weapon_offhand=weapon_offhand,
            armor=armor,
            shield=shield,
            feats=selected_feats,
        )
        team_val = self.team_choice.currentText()
        participant.team = "" if team_val == "FFA" else team_val
        return participant

    def to_template(self) -> dict:
        return {
            "name": self.name_input.text(),
            "hp": int(self.hp_input.value()),
            "anima": int(self.anima_input.value()),
            "max_anima": int(self.max_anima_input.value()),
            "stats": {k: int(v.value()) for k, v in self.stat_spins.items()},
            "skills": {stat: {sk: int(sp.value()) for sk, sp in skills.items()} for stat, skills in self.skill_spins.items()},
            "hand1": self.hand1_choice.currentText(),
            "hand2": self.hand2_choice.currentText(),
            "armor": self.armor_choice.currentText(),
            "team": self.team_choice.currentText(),
            "feats": [name for name, cb in self.feat_checks.items() if cb.isChecked()],
        }

    def load_template(self, data: dict) -> None:
        if not data:
            return
        self.name_input.setText(str(data.get("name", "")))
        self.hp_input.setValue(int(data.get("hp", self.hp_input.value())))
        self.anima_input.setValue(int(data.get("anima", self.anima_input.value())))
        self.max_anima_input.setValue(int(data.get("max_anima", self.max_anima_input.value())))
        for stat, val in data.get("stats", {}).items():
            if stat in self.stat_spins:
                self.stat_spins[stat].setValue(int(val))
        for stat, skills in data.get("skills", {}).items():
            if stat in self.skill_spins:
                for sk, val in skills.items():
                    if sk in self.skill_spins[stat]:
                        self.skill_spins[stat][sk].setValue(int(val))
        hand1_val = data.get("hand1") or data.get("weapon")
        hand2_val = data.get("hand2") or data.get("shield")
        if hand1_val and hand1_val in self.hand_choice_model():
            self.hand1_choice.setCurrentText(hand1_val)
        if hand2_val and hand2_val in self.hand_choice_model():
            self.hand2_choice.setCurrentText(hand2_val)
        if data.get("armor") in self.armor_choice_model():
            self.armor_choice.setCurrentText(data.get("armor"))
        if data.get("team"):
            self.team_choice.setCurrentText(str(data["team"]))
        # Restore feat selections
        feat_list = data.get("feats", [])
        for name, cb in self.feat_checks.items():
            cb.setChecked(name in feat_list)
        self._refresh_hand_options()

    def _blank_template(self) -> dict:
        return {
            "name": "",
            "hp": 20,
            "anima": 0,
            "max_anima": 2,
            "stats": {stat: 0 for stat in STATS.keys()},
            "skills": {stat: {sk: 0 for sk in skills} for stat, skills in STATS.items()},
            "hand1": "Arming Sword",
            "hand2": "(None)",
            "armor": "Light Armor",
            "team": "Team A",
        }

    def armor_choice_model(self) -> set[str]:
        return set([self.armor_choice.itemText(i) for i in range(self.armor_choice.count())])

    def hand_choice_model(self) -> set[str]:
        return set([self.hand1_choice.itemText(i) for i in range(self.hand1_choice.count())])

    def _apply_hand_disable(self, combo: QComboBox, disable: set[str]) -> None:
        model = combo.model()
        if not model:
            return
        current = combo.currentText()
        for i in range(model.rowCount()):
            item = model.item(i)
            if not item:
                continue
            text = item.text()
            should_disable = text in disable and text != current
            item.setEnabled(not should_disable)
        if current in disable:
            none_idx = combo.findText("(None)")
            if none_idx >= 0:
                combo.setCurrentIndex(none_idx)

    def _refresh_hand_options(self) -> None:
        hand1 = self.hand1_choice.currentText()
        hand2 = self.hand2_choice.currentText()

        disable_hand1: set[str] = set()
        disable_hand2: set[str] = set()

        if hand2 in self._two_handed_names:
            disable_hand1 |= self._weapon_names
            disable_hand1.add(self._large_shield_name)
        if hand1 in self._two_handed_names:
            disable_hand2 |= self._weapon_names
            disable_hand2.add(self._large_shield_name)

        self._apply_hand_disable(self.hand1_choice, disable_hand1)
        self._apply_hand_disable(self.hand2_choice, disable_hand2)

    def _check_equipment_requirements(self) -> None:
        """Check if current equipment meets stat requirements and show warnings."""
        warnings: list[str] = []

        # Gather current stat/skill values
        stat_vals: dict[str, int] = {}
        for stat, spin in self.stat_spins.items():
            stat_vals[stat] = int(spin.value())
        for stat, skills in self.skill_spins.items():
            for skill, spin in skills.items():
                stat_vals[f"{stat}:{skill}"] = int(spin.value())

        # Check each equipped item
        items_to_check: list[tuple[str, dict]] = []
        hand1_name = self.hand1_choice.currentText()
        hand2_name = self.hand2_choice.currentText()
        armor_name = self.armor_choice.currentText()

        if hand1_name in AVALORE_WEAPONS:
            items_to_check.append((hand1_name, AVALORE_WEAPONS[hand1_name].stat_requirements))
        elif hand1_name in AVALORE_SHIELDS:
            items_to_check.append((hand1_name, AVALORE_SHIELDS[hand1_name].stat_requirements))
        if hand2_name in AVALORE_WEAPONS:
            items_to_check.append((hand2_name, AVALORE_WEAPONS[hand2_name].stat_requirements))
        elif hand2_name in AVALORE_SHIELDS:
            items_to_check.append((hand2_name, AVALORE_SHIELDS[hand2_name].stat_requirements))
        if armor_name != "None" and armor_name in AVALORE_ARMOR:
            items_to_check.append((armor_name, AVALORE_ARMOR[armor_name].stat_requirements))

        for item_name, reqs in items_to_check:
            for req_key, min_val in reqs.items():
                current_val = stat_vals.get(req_key, 0)
                if current_val < min_val:
                    warnings.append(f"⚠ {item_name} requires {req_key} ≥ {min_val} (current: {current_val})")

        if warnings:
            self._equip_warning_label.setText("\n".join(warnings))
            self._equip_warning_label.show()
        else:
            self._equip_warning_label.hide()


class ScenarioEditorDialog(QDialog):
    def __init__(self, scenario: dict, attacker_name: str, defender_name: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Scenario Builder")
        self.setModal(True)
        self.resize(720, 640)

        self.attacker_name = attacker_name or "Attacker"
        self.defender_name = defender_name or "Defender"

        self.width = int(scenario.get("width", 10))
        self.height = int(scenario.get("height", 10))
        self.attacker_pos = tuple(scenario.get("attacker_pos", (0, 0)))
        self.defender_pos = tuple(scenario.get("defender_pos", (3, 0)))
        self.terrain: dict[tuple[int, int], str] = {
            (int(cell["x"]), int(cell["y"])): str(cell["terrain"])
            for cell in scenario.get("terrain", [])
        }

        layout = QVBoxLayout()
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)
        self.setLayout(layout)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Width:"))
        self.width_spin = QSpinBox()
        self.width_spin.setRange(4, 40)
        self.width_spin.setValue(self.width)
        size_row.addWidget(self.width_spin)
        size_row.addSpacing(12)
        size_row.addWidget(QLabel("Height:"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(4, 40)
        self.height_spin.setValue(self.height)
        size_row.addWidget(self.height_spin)
        self.resize_btn = QPushButton("Resize")
        self.resize_btn.clicked.connect(self._apply_resize)
        size_row.addWidget(self.resize_btn)
        size_row.addStretch()
        layout.addLayout(size_row)

        tools_row = QHBoxLayout()
        tools_row.addWidget(QLabel("Edit mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Terrain", "Place Attacker", "Place Defender", "Erase"])
        tools_row.addWidget(self.mode_combo)
        tools_row.addSpacing(12)
        tools_row.addWidget(QLabel("Terrain:"))
        self.terrain_combo = QComboBox()
        self.terrain_combo.addItems(["normal", "forest", "water", "mountain", "road", "wall"])
        tools_row.addWidget(self.terrain_combo)
        self.fill_btn = QPushButton("Fill")
        self.fill_btn.clicked.connect(self._fill_terrain)
        tools_row.addWidget(self.fill_btn)
        self.clear_btn = QPushButton("Clear Terrain")
        self.clear_btn.clicked.connect(self._clear_terrain)
        tools_row.addWidget(self.clear_btn)
        tools_row.addStretch()
        layout.addLayout(tools_row)

        self.map_widget = TacticalMapWidget(self.width, self.height)
        self.map_widget.setMinimumHeight(380)
        self.map_widget.set_interaction_handlers(on_click=self._on_cell_clicked)
        layout.addWidget(self.map_widget)

        help_label = QLabel("Click tiles to paint terrain or place combatants. Use Fill to apply terrain across the grid.")
        help_label.setStyleSheet("color: #777;")
        layout.addWidget(help_label)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._ensure_distinct_positions()
        self._refresh_map()

    def _apply_resize(self) -> None:
        self.width = int(self.width_spin.value())
        self.height = int(self.height_spin.value())
        self.terrain = {(x, y): t for (x, y), t in self.terrain.items() if x < self.width and y < self.height}
        self.attacker_pos = (min(self.attacker_pos[0], self.width - 1), min(self.attacker_pos[1], self.height - 1))
        self.defender_pos = (min(self.defender_pos[0], self.width - 1), min(self.defender_pos[1], self.height - 1))
        self._ensure_distinct_positions()
        self.map_widget.set_grid_dimensions(self.width, self.height)
        self._refresh_map()

    def _ensure_distinct_positions(self) -> None:
        if self.attacker_pos != self.defender_pos:
            return
        ax, ay = self.attacker_pos
        candidates = [
            (min(self.width - 1, ax + 1), ay),
            (max(0, ax - 1), ay),
            (ax, min(self.height - 1, ay + 1)),
            (ax, max(0, ay - 1)),
        ]
        for pos in candidates:
            if pos != self.attacker_pos:
                self.defender_pos = pos
                return

    def _fill_terrain(self) -> None:
        terrain = self.terrain_combo.currentText()
        if terrain == "normal":
            self.terrain.clear()
        else:
            self.terrain = {(x, y): terrain for x in range(self.width) for y in range(self.height)}
        self._refresh_map()

    def _clear_terrain(self) -> None:
        self.terrain.clear()
        self._refresh_map()

    def _on_cell_clicked(self, x: int, y: int) -> None:
        mode = self.mode_combo.currentText()
        if mode == "Place Attacker":
            prev = self.attacker_pos
            self.attacker_pos = (x, y)
            if self.attacker_pos == self.defender_pos:
                self.defender_pos = prev
        elif mode == "Place Defender":
            prev = self.defender_pos
            self.defender_pos = (x, y)
            if self.defender_pos == self.attacker_pos:
                self.attacker_pos = prev
        else:
            if mode == "Erase":
                terrain = "normal"
            else:
                terrain = self.terrain_combo.currentText()
            if terrain == "normal":
                self.terrain.pop((x, y), None)
            else:
                self.terrain[(x, y)] = terrain
        self._ensure_distinct_positions()
        self._refresh_map()

    def _build_snapshot(self) -> dict:
        cells = []
        for y in range(self.height):
            for x in range(self.width):
                terrain = self.terrain.get((x, y), "normal")
                occupant = None
                if (x, y) == self.attacker_pos:
                    occupant = self.attacker_name
                elif (x, y) == self.defender_pos:
                    occupant = self.defender_name
                cells.append({
                    "x": x,
                    "y": y,
                    "terrain": terrain,
                    "occupant": occupant,
                })
        return {
            "label": "Scenario",
            "width": self.width,
            "height": self.height,
            "cells": cells,
            "actor": {"position": self.attacker_pos},
            "target": {"position": self.defender_pos},
        }

    def _refresh_map(self) -> None:
        self.map_widget.draw_snapshot(self._build_snapshot())

    def get_scenario(self) -> dict:
        return {
            "width": self.width,
            "height": self.height,
            "attacker_pos": [int(self.attacker_pos[0]), int(self.attacker_pos[1])],
            "defender_pos": [int(self.defender_pos[0]), int(self.defender_pos[1])],
            "terrain": [
                {"x": int(x), "y": int(y), "terrain": terrain}
                for (x, y), terrain in sorted(self.terrain.items())
            ],
        }


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AvaSim — Qt Combat Sandbox")
        self.resize(1000, 700)
        self.setMinimumSize(1000, 700)

        # Initialize theme manager
        self.theme_manager = ThemeManager(Theme.DARK)
        self._time_of_day = "day"
        appdata = Path(os.environ.get("APPDATA", ""))
        self.settings_path = (appdata / "AvaSim" / "settings.json") if appdata.exists() else (Path.home() / ".avasim_settings.json")
        self.quickstart_setup = {
            "char1": {
                "name": "Captain",
                "hp": 28,
                "anima": 2,
                "max_anima": 4,
                "stats": {"Strength": 2, "Dexterity": 1, "Intelligence": 0, "Vitality": 2},
                "skills": {
                    "Strength": {"Athletics": 2, "Fortitude": 1, "Power": 1},
                    "Dexterity": {"Acrobatics": 1, "Finesse": 1, "Stealth": 0},
                    "Intelligence": {"Lore": 0, "Investigation": 0, "Insight": 0},
                    "Vitality": {"Endurance": 2, "Discipline": 1, "Intimidation": 0},
                },
                "hand1": "Arming Sword",
                "hand2": "Small Shield",
                "armor": "Medium Armor",
            },
            "char2": {
                "name": "Brigand",
                "hp": 24,
                "anima": 0,
                "max_anima": 2,
                "stats": {"Strength": 1, "Dexterity": 2, "Intelligence": 0, "Vitality": 1},
                "skills": {
                    "Strength": {"Athletics": 1, "Fortitude": 0, "Power": 0},
                    "Dexterity": {"Acrobatics": 2, "Finesse": 2, "Stealth": 1},
                    "Intelligence": {"Lore": 0, "Investigation": 0, "Insight": 0},
                    "Vitality": {"Endurance": 1, "Discipline": 0, "Intimidation": 0},
                },
                "hand1": "Spear",
                "hand2": "(None)",
                "armor": "Light Armor",
            },
            "mode": "Player controls both (Default)",
            "theme": "Light",
            "time": "Day",
            "show_math": False,
        }
        self._hover_cell = None
        self.decision_log: list[str] = []
        self._last_action_lines: list[str] = []
        self._move_path_preview: list[tuple[int, int]] = []
        self.scenario_width = 10
        self.scenario_height = 10
        self.scenario_cells: dict[tuple[int, int], str] = {}
        self.scenario_attacker_pos = (0, 0)
        self.scenario_defender_pos = (3, 0)
        self.scenario_positions: list[tuple[int, int]] = [(0, 0), (3, 0)]  # N-combatant positions
        self._scenario_presets = self._build_scenario_presets()
        self._move_path_preview: list[tuple[int, int]] = []
        self._last_engine: AvaCombatEngine | None = None
        self.decision_log: list[str] = []
        self.combat_ai = CombatAI(strategy="balanced", decision_log=self.decision_log)

        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setLayout(root_layout)

        # Menu bar
        self.menu_bar = QMenuBar()
        root_layout.addWidget(self.menu_bar)
        self._build_menus()

        # ── Header bar ──
        header = QWidget()
        header.setObjectName("headerBar")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 0, 16, 0)
        header_layout.setSpacing(12)

        title_label = QLabel("⚔  AvaSim")
        title_label.setObjectName("headerTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.start_button = QPushButton("Start")
        self.start_button.setIcon(IconProvider.get_icon("play"))
        self.start_button.setFixedWidth(100)
        self.start_button.setToolTip("Focus character panel")

        self.quickstart_button = QPushButton("Quick Start")
        self.quickstart_button.setIcon(IconProvider.get_icon("sword"))
        self.quickstart_button.setFixedWidth(120)
        self.quickstart_button.setToolTip("Load sample characters")
        self.quickstart_button.clicked.connect(self._apply_quickstart)

        self.reload_button = QPushButton("Reload")
        self.reload_button.setIcon(IconProvider.get_icon("refresh"))
        self.reload_button.setFixedWidth(100)
        self.reload_button.setToolTip("Reload last saved settings")
        self.reload_button.clicked.connect(self._reload_last_setup)

        self.theme_toggle_btn = QPushButton()
        self.theme_toggle_btn.setIcon(IconProvider.get_icon("moon"))
        self.theme_toggle_btn.setObjectName("themeToggle")
        self.theme_toggle_btn.setToolTip("Toggle dark/light theme")
        self.theme_toggle_btn.clicked.connect(self._toggle_theme)

        for btn in (self.start_button, self.quickstart_button, self.reload_button):
            header_layout.addWidget(btn)
        header_layout.addWidget(self.theme_toggle_btn)
        root_layout.addWidget(header)

        self.toast_label = QLabel("")
        self.toast_label.setVisible(False)
        self.toast_label.setObjectName("toast")
        root_layout.addWidget(self.toast_label)

        # ══════════════════════════════════════════
        #  MAIN CONTENT: Sidebar + Canvas
        # ══════════════════════════════════════════
        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setHandleWidth(2)

        # ─── SIDEBAR ───
        sidebar_scroll = QScrollArea()
        sidebar_scroll.setWidgetResizable(True)
        sidebar_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        sidebar_scroll.setObjectName("sidebarScroll")

        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(8, 8, 8, 8)
        sidebar_layout.setSpacing(6)

        # ── Characters Section ──
        char_section = CollapsibleSection("⚔  Characters")
        char_content = QVBoxLayout()

        self.combatant_editors: list[CombatantEditor] = []
        self.editors_layout = QVBoxLayout()

        self.attacker_editor = CombatantEditor("Character 1")
        self.attacker_editor.team_choice.setCurrentText("Team A")
        self.defender_editor = CombatantEditor("Character 2")
        self.defender_editor.team_choice.setCurrentText("Team B")
        self.combatant_editors = [self.attacker_editor, self.defender_editor]
        self.editors_layout.addWidget(self.attacker_editor)
        self.editors_layout.addWidget(self.defender_editor)
        char_content.addLayout(self.editors_layout)

        self.attacker_editor.name_input.textChanged.connect(self._refresh_scenario_preview)
        self.defender_editor.name_input.textChanged.connect(self._refresh_scenario_preview)
        for combo in (
            self.attacker_editor.hand1_choice,
            self.attacker_editor.hand2_choice,
            self.defender_editor.hand1_choice,
            self.defender_editor.hand2_choice,
        ):
            combo.currentTextChanged.connect(self._update_action_availability)

        combatant_btn_row = QHBoxLayout()
        self.add_combatant_btn = QPushButton("+ Add")
        self.add_combatant_btn.setIcon(IconProvider.get_icon("add"))
        self.add_combatant_btn.clicked.connect(self._add_combatant_editor)
        self.add_combatant_btn.setToolTip("Add combatant (max 8)")
        self.remove_combatant_btn = QPushButton("- Remove")
        self.remove_combatant_btn.clicked.connect(self._remove_combatant_editor)
        self.remove_combatant_btn.setToolTip("Remove last (min 2)")
        self.remove_combatant_btn.setEnabled(False)
        combatant_btn_row.addWidget(self.add_combatant_btn)
        combatant_btn_row.addWidget(self.remove_combatant_btn)
        combatant_btn_row.addStretch()
        char_content.addLayout(combatant_btn_row)

        template_row = QHBoxLayout()
        self.save_c1_btn = QPushButton("Save C1")
        self.save_c1_btn.setIcon(IconProvider.get_icon("save"))
        self.save_c1_btn.clicked.connect(lambda: self._save_template(self.attacker_editor))
        self.load_c1_btn = QPushButton("Load C1")
        self.load_c1_btn.setIcon(IconProvider.get_icon("load"))
        self.load_c1_btn.clicked.connect(lambda: self._load_template(self.attacker_editor))
        self.save_c2_btn = QPushButton("Save C2")
        self.save_c2_btn.setIcon(IconProvider.get_icon("save"))
        self.save_c2_btn.clicked.connect(lambda: self._save_template(self.defender_editor))
        self.load_c2_btn = QPushButton("Load C2")
        self.load_c2_btn.setIcon(IconProvider.get_icon("load"))
        self.load_c2_btn.clicked.connect(lambda: self._load_template(self.defender_editor))
        for btn in (self.save_c1_btn, self.load_c1_btn, self.save_c2_btn, self.load_c2_btn):
            template_row.addWidget(btn)
        char_content.addLayout(template_row)

        char_section.set_content_layout(char_content)
        sidebar_layout.addWidget(char_section)

        # ── Scenario Section ──
        scenario_section = CollapsibleSection("🗺  Scenario", collapsed=True)
        scenario_content = QVBoxLayout()
        scenario_content.setSpacing(8)

        size_row = QHBoxLayout()
        size_row.addWidget(QLabel("Map:"))
        self.map_width_spin = QSpinBox()
        self.map_width_spin.setRange(4, 40)
        self.map_width_spin.setValue(self.scenario_width)
        self.map_width_spin.setMaximumWidth(60)
        size_row.addWidget(QLabel("W"))
        size_row.addWidget(self.map_width_spin)
        self.map_height_spin = QSpinBox()
        self.map_height_spin.setRange(4, 40)
        self.map_height_spin.setValue(self.scenario_height)
        self.map_height_spin.setMaximumWidth(60)
        size_row.addWidget(QLabel("H"))
        size_row.addWidget(self.map_height_spin)
        self.resize_map_button = QPushButton("Resize")
        self.resize_map_button.setIcon(IconProvider.get_icon("refresh"))
        self.resize_map_button.clicked.connect(self._resize_scenario_map)
        size_row.addWidget(self.resize_map_button)
        size_row.addStretch()
        scenario_content.addLayout(size_row)

        tool_row = QHBoxLayout()
        tool_row.addWidget(QLabel("Tool:"))
        self.map_tool_combo = QComboBox()
        self.map_tool_combo.addItems(["Paint Terrain", "Erase Terrain", "Place Character 1", "Place Character 2"])
        self.map_tool_combo.setMinimumWidth(130)
        tool_row.addWidget(self.map_tool_combo)
        tool_row.addStretch()
        scenario_content.addLayout(tool_row)

        terrain_row = QHBoxLayout()
        terrain_row.addWidget(QLabel("Terrain:"))
        self.terrain_combo = QComboBox()
        self.terrain_combo.addItems(["Normal", "Forest", "Water", "Mountain", "Road", "Wall"])
        self.terrain_combo.setMinimumWidth(100)
        terrain_row.addWidget(self.terrain_combo)
        self.clear_terrain_button = QPushButton("Clear")
        self.clear_terrain_button.setIcon(IconProvider.get_icon("delete"))
        self.clear_terrain_button.clicked.connect(self._clear_scenario_terrain)
        terrain_row.addWidget(self.clear_terrain_button)
        terrain_row.addStretch()
        scenario_content.addLayout(terrain_row)

        overlay_row = QHBoxLayout()
        overlay_row.addWidget(QLabel("Show:"))
        self.overlay_source_combo = QComboBox()
        self.overlay_source_combo.addItems(["None", "Character 1", "Character 2"])
        self.overlay_source_combo.setMinimumWidth(100)
        self.overlay_source_combo.setCurrentText("Character 1")
        self.overlay_source_combo.currentIndexChanged.connect(self._refresh_scenario_preview)
        overlay_row.addWidget(self.overlay_source_combo)
        overlay_row.addStretch()
        scenario_content.addLayout(overlay_row)

        overlay_checks_row = QHBoxLayout()
        self.overlay_range_check = QCheckBox("Range")
        self.overlay_range_check.setChecked(True)
        self.overlay_los_check = QCheckBox("LOS")
        self.overlay_path_check = QCheckBox("Path")
        self.overlay_path_check.setChecked(True)
        for chk in (self.overlay_range_check, self.overlay_los_check, self.overlay_path_check):
            chk.stateChanged.connect(self._refresh_scenario_preview)
            overlay_checks_row.addWidget(chk)
        overlay_checks_row.addStretch()
        scenario_content.addLayout(overlay_checks_row)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(["Custom", "Duel", "Skirmish", "Siege", "2v2 Skirmish", "1v3 Ambush", "Free-for-All"])
        self.preset_combo.setMinimumWidth(100)
        preset_row.addWidget(self.preset_combo)
        self.load_preset_button = QPushButton("Load")
        self.load_preset_button.setIcon(IconProvider.get_icon("load"))
        self.load_preset_button.clicked.connect(self._load_preset)
        preset_row.addWidget(self.load_preset_button)
        preset_row.addStretch()
        scenario_content.addLayout(preset_row)

        scenario_io_row = QHBoxLayout()
        self.open_scenario_editor_button = QPushButton("Editor")
        self.open_scenario_editor_button.setIcon(IconProvider.get_icon("edit"))
        self.open_scenario_editor_button.clicked.connect(self._open_scenario_editor)
        self.save_scenario_button = QPushButton("Save")
        self.save_scenario_button.setIcon(IconProvider.get_icon("save"))
        self.save_scenario_button.clicked.connect(self._save_scenario)
        self.load_scenario_button = QPushButton("Load")
        self.load_scenario_button.setIcon(IconProvider.get_icon("load"))
        self.load_scenario_button.clicked.connect(self._load_scenario)
        scenario_io_row.addWidget(self.open_scenario_editor_button)
        scenario_io_row.addWidget(self.save_scenario_button)
        scenario_io_row.addWidget(self.load_scenario_button)
        scenario_io_row.addStretch()
        scenario_content.addLayout(scenario_io_row)

        scenario_section.set_content_layout(scenario_content)
        sidebar_layout.addWidget(scenario_section)

        # ── Settings Section ──
        settings_section = CollapsibleSection("⚙  Settings")
        settings_content = QVBoxLayout()
        settings_content.setSpacing(8)

        env_row = QHBoxLayout()
        env_row.addWidget(QLabel("Theme:"))
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Dark", "Light"])
        self.theme_combo.setMaximumWidth(100)
        self.theme_combo.setToolTip("Switch between dark and light themes")
        self.theme_combo.currentIndexChanged.connect(self._on_theme_changed)
        env_row.addWidget(self.theme_combo)
        env_row.addWidget(QLabel("Time:"))
        self.time_combo = QComboBox()
        self.time_combo.addItems(["Day", "Night"])
        self.time_combo.setMaximumWidth(80)
        self.time_combo.setToolTip("Apply day or night modifiers")
        self.time_combo.currentIndexChanged.connect(self._on_time_changed)
        env_row.addWidget(self.time_combo)
        env_row.addStretch()
        settings_content.addLayout(env_row)

        surprise_row = QHBoxLayout()
        surprise_row.addWidget(QLabel("Surprise:"))
        self.surprise_combo = QComboBox()
        self.surprise_combo.addItems(["None", "Party Surprised", "Party Ambushes"])
        self.surprise_combo.setMaximumWidth(160)
        self.surprise_combo.setToolTip("Apply surprise/ambush modifiers to initiative")
        self.surprise_combo.currentIndexChanged.connect(self._on_surprise_changed)
        surprise_row.addWidget(self.surprise_combo)
        surprise_row.addStretch()
        settings_content.addLayout(surprise_row)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self.mode_combo = QComboBox()
        self.mode_combo.addItems([
            "Player controls both (Default)",
            "Player controls Character 1",
            "Full Auto (both AI)",
            "Full Simulation (Beta)",
            "Single Simulation (Beta)",
        ])
        self.mode_combo.setMinimumWidth(160)
        self.mode_combo.setToolTip("Select player-controlled or beta auto modes")
        self.mode_combo.currentIndexChanged.connect(self._on_mode_changed)
        mode_row.addWidget(self.mode_combo)
        settings_content.addLayout(mode_row)

        self.show_math_check = QCheckBox("Show decision notes")
        self.show_math_check.setToolTip("Include brief decision math/choices in the log")
        settings_content.addWidget(self.show_math_check)

        settings_section.set_content_layout(settings_content)
        sidebar_layout.addWidget(settings_section)

        # ── Combat Controls Section ──
        combat_section = CollapsibleSection("⚔  Combat Controls")
        combat_content = QVBoxLayout()
        combat_content.setSpacing(8)

        self.simulate_button = QPushButton("Run Combat")
        self.simulate_button.setIcon(IconProvider.get_icon("play"))
        self.simulate_button.clicked.connect(self.run_simulation)
        self.simulate_button.setToolTip("Simulate the current setup")
        combat_content.addWidget(self.simulate_button)

        self.batch_button = QPushButton("Batch Sim")
        self.batch_button.setIcon(IconProvider.get_icon("chart"))
        self.batch_button.clicked.connect(self._run_batch_simulation)
        self.batch_button.setToolTip("Run N simulations and show win-rate statistics")
        combat_content.addWidget(self.batch_button)

        self.compare_button = QPushButton("Compare Loadouts")
        self.compare_button.setIcon(IconProvider.get_icon("target"))
        self.compare_button.clicked.connect(self._compare_loadouts)
        self.compare_button.setToolTip(
            "Run batch simulations on current setup, swap a weapon, run again, and compare results"
        )
        combat_content.addWidget(self.compare_button)

        initiative_row = QHBoxLayout()
        initiative_row.addWidget(QLabel("Initiative:"))
        self.initiative_label = QLabel("(run sim)")
        self.initiative_label.setStyleSheet("font-weight: bold;")
        initiative_row.addWidget(self.initiative_label)
        initiative_row.addStretch()
        combat_content.addLayout(initiative_row)

        player_action_row = QHBoxLayout()
        player_action_row.addWidget(QLabel("Actions:"))
        self.player_action1_combo = QComboBox()
        self.player_action2_combo = QComboBox()
        for combo in (self.player_action1_combo, self.player_action2_combo):
            combo.addItems(["Attack", "Evade", "Block", "Skip"])
            combo.setToolTip("Player-selected action when in player-controlled mode")
        player_action_row.addWidget(self.player_action1_combo)
        player_action_row.addWidget(self.player_action2_combo)
        combat_content.addLayout(player_action_row)

        move_row = QHBoxLayout()
        move_row.addWidget(QLabel("Move:"))
        move_row.addWidget(QLabel("x"))
        self.move_x = QSpinBox()
        self.move_x.setRange(0, 99)
        self.move_x.setMaximumWidth(50)
        self.move_x.valueChanged.connect(self._update_move_preview)
        move_row.addWidget(self.move_x)
        move_row.addWidget(QLabel("y"))
        self.move_y = QSpinBox()
        self.move_y.setRange(0, 99)
        self.move_y.setMaximumWidth(50)
        self.move_y.valueChanged.connect(self._update_move_preview)
        move_row.addWidget(self.move_y)
        self.move_button = QPushButton("Go")
        self.move_button.setIcon(IconProvider.get_icon("arrow_right"))
        self.move_button.clicked.connect(self.move_attacker)
        self.move_button.setToolTip("Move Character 1 to the chosen coordinates")
        move_row.addWidget(self.move_button)
        move_row.addStretch()
        combat_content.addLayout(move_row)

        combat_section.set_content_layout(combat_content)
        sidebar_layout.addWidget(combat_section)

        sidebar_layout.addStretch()
        sidebar_scroll.setWidget(sidebar)
        self.main_splitter.addWidget(sidebar_scroll)
        
        self._set_player_controls_enabled(False)
        self.replay_snapshots: list[dict] = []
        self.replay_index = 0
        self.replay_timer = QTimer(self)
        self.replay_timer.setInterval(700)
        self.replay_timer.timeout.connect(self._advance_replay)

        # initialize control state based on default mode
        self._on_mode_changed()

        # ─── MAIN CANVAS ───
        canvas = QWidget()
        canvas.setObjectName("mainCanvas")
        canvas_layout = QVBoxLayout(canvas)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.setSpacing(0)

        self.canvas_splitter = QSplitter(Qt.Vertical)
        self.canvas_splitter.setHandleWidth(3)

        # ── Map Area ──
        map_container = QWidget()
        map_container.setObjectName("mapContainer")
        map_layout = QVBoxLayout(map_container)
        map_layout.setContentsMargins(8, 8, 8, 4)
        map_layout.setSpacing(4)

        self.tactical_map_widget = TacticalMapWidget(10, 10)
        self.tactical_map_widget.setMinimumHeight(300)
        self.tactical_map_widget.setMinimumWidth(400)
        self.tactical_map_widget.set_interaction_handlers(
            on_click=self._on_scenario_cell_clicked,
            on_hover=self._on_scenario_cell_hover,
        )
        map_layout.addWidget(self.tactical_map_widget)

        # Replay bar under map
        replay_row = QHBoxLayout()
        replay_row.setSpacing(6)
        self.replay_prev = QPushButton()
        self.replay_prev.setIcon(IconProvider.get_icon("arrow_left"))
        self.replay_prev.setToolTip("Previous frame")
        self.replay_prev.setFixedWidth(32)
        self.replay_next = QPushButton()
        self.replay_next.setIcon(IconProvider.get_icon("arrow_right"))
        self.replay_next.setToolTip("Next frame")
        self.replay_next.setFixedWidth(32)
        self.replay_play = QPushButton()
        self.replay_play.setIcon(IconProvider.get_icon("play"))
        self.replay_play.setToolTip("Play/Pause replay")
        self.replay_play.setFixedWidth(32)
        self.replay_slider = QSlider(Qt.Horizontal)
        self.replay_slider.setMinimum(0)
        self.replay_slider.setMaximum(0)
        self.replay_slider.setSingleStep(1)
        replay_label = QLabel("Replay")
        replay_label.setStyleSheet("font-weight: bold; font-size: 10pt;")
        replay_row.addWidget(replay_label)
        replay_row.addWidget(self.replay_prev)
        replay_row.addWidget(self.replay_play)
        replay_row.addWidget(self.replay_next)
        replay_row.addWidget(self.replay_slider)
        self.replay_slider.valueChanged.connect(self._on_replay_slider)
        self.replay_prev.clicked.connect(lambda: self._step_replay(-1))
        self.replay_next.clicked.connect(lambda: self._step_replay(1))
        self.replay_play.clicked.connect(self._toggle_replay)
        map_layout.addLayout(replay_row)

        self.canvas_splitter.addWidget(map_container)

        # ── Bottom Panel (tabbed logs, status, grid) ──
        bottom_panel = QWidget()
        bottom_panel.setObjectName("bottomPanel")
        bottom_layout = QVBoxLayout(bottom_panel)
        bottom_layout.setContentsMargins(8, 4, 8, 8)
        bottom_layout.setSpacing(4)

        self.log_tabs = QTabWidget()
        self.log_tabs.setObjectName("logTabs")

        # Action Log tab
        action_log_widget = QWidget()
        action_log_layout = QVBoxLayout(action_log_widget)
        action_log_layout.setContentsMargins(4, 4, 4, 4)
        self.action_view = QTextEdit()
        self.action_view.setReadOnly(True)
        self.action_view.setPlaceholderText("Turn-by-turn actions will appear here.")
        self.action_view.setLineWrapMode(QTextEdit.NoWrap)
        self.collapse_log_check = QCheckBox("Collapse log runs")
        self.collapse_log_check.setToolTip("Combine repeated log lines into a single entry")
        self.collapse_log_check.stateChanged.connect(self._rerender_action_log)
        action_log_layout.addWidget(self.collapse_log_check)
        action_log_layout.addWidget(self.action_view)
        self.log_tabs.addTab(action_log_widget, "⚔ Action Log")

        # Status tab
        status_widget = QWidget()
        status_layout = QVBoxLayout(status_widget)
        status_layout.setContentsMargins(4, 4, 4, 4)
        self.status_view = QTextEdit()
        self.status_view.setReadOnly(True)
        self.status_view.setPlaceholderText("Status badges will appear here.")
        self.status_view.setLineWrapMode(QTextEdit.NoWrap)
        self.status_view.setMaximumHeight(130)
        status_layout.addWidget(self.status_view)

        bars_group = QGroupBox("HP / Armor")
        bars_layout = QGridLayout()
        self.attacker_hp_bar = QProgressBar()
        self.attacker_hp_bar.setRange(0, 100)
        self.attacker_hp_bar.setValue(0)
        self.attacker_hp_bar.setFormat("Character 1 HP: %v/%m")
        self.attacker_armor_bar = QProgressBar()
        self.attacker_armor_bar.setRange(0, 3)
        self.attacker_armor_bar.setValue(0)
        self.attacker_armor_bar.setFormat("Character 1 Armor: %v/3")
        self.defender_hp_bar = QProgressBar()
        self.defender_hp_bar.setRange(0, 100)
        self.defender_hp_bar.setValue(0)
        self.defender_hp_bar.setFormat("Character 2 HP: %v/%m")
        self.defender_armor_bar = QProgressBar()
        self.defender_armor_bar.setRange(0, 3)
        self.defender_armor_bar.setValue(0)
        self.defender_armor_bar.setFormat("Character 2 Armor: %v/3")
        bars_layout.addWidget(self.attacker_hp_bar, 0, 0)
        bars_layout.addWidget(self.attacker_armor_bar, 1, 0)
        bars_layout.addWidget(self.defender_hp_bar, 2, 0)
        bars_layout.addWidget(self.defender_armor_bar, 3, 0)
        bars_group.setLayout(bars_layout)
        self._combat_bars_layout = bars_layout
        self._extra_combat_bars = []
        status_layout.addWidget(bars_group)
        self.log_tabs.addTab(status_widget, "📊 Status")

        # Map Log tab
        self.map_view = QTextEdit()
        self.map_view.setReadOnly(True)
        self.map_view.setPlaceholderText("Post-turn maps will appear here.")
        self.map_view.setLineWrapMode(QTextEdit.NoWrap)
        self.log_tabs.addTab(self.map_view, "🗺 Map Log")

        # Map Grid tab
        self.map_grid = QTableWidget(10, 10)
        self.map_grid.setMinimumWidth(200)
        self.map_grid.horizontalHeader().setVisible(False)
        self.map_grid.verticalHeader().setVisible(False)
        self.map_grid.setEditTriggers(QTableWidget.NoEditTriggers)
        self.map_grid.setSelectionMode(QTableWidget.NoSelection)
        self.map_grid.setShowGrid(True)
        for c in range(10):
            self.map_grid.setColumnWidth(c, 28)
        for r in range(10):
            self.map_grid.setRowHeight(r, 24)
        self.log_tabs.addTab(self.map_grid, "Grid")

        # Decisions tab
        self.decision_view = QTextEdit()
        self.decision_view.setReadOnly(True)
        self.decision_view.setPlaceholderText("Decision math and AI reasoning will appear here.")
        self.decision_view.setLineWrapMode(QTextEdit.NoWrap)
        self.log_tabs.addTab(self.decision_view, "🧠 Decisions")

        bottom_layout.addWidget(self.log_tabs)

        self.canvas_splitter.addWidget(bottom_panel)
        self.canvas_splitter.setStretchFactor(0, 3)
        self.canvas_splitter.setStretchFactor(1, 2)

        canvas_layout.addWidget(self.canvas_splitter)
        self.main_splitter.addWidget(canvas)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([340, 940])

        root_layout.addWidget(self.main_splitter)

        # Decision drawer compat (hidden, kept for method references)
        self.decision_toggle = QCheckBox("Show decision drawer")
        self.decision_toggle.setChecked(False)
        self.decision_toggle.stateChanged.connect(self._toggle_decision_drawer)
        self.decision_group = QGroupBox("Decision Math")
        self.decision_group.setVisible(False)

        self._load_settings()
        self._apply_theme()
        self._update_move_limits()
        self._refresh_scenario_preview()
        if not getattr(self, "_first_launch_shown", False) and not getattr(self, "_settings_loaded", False):
            self._first_launch_shown = True
            self._show_howto()

    def _build_menus(self) -> None:
        file_menu = self.menu_bar.addMenu("File")
        new_action = QAction("New Setup", self)
        new_action.setShortcut("Ctrl+N")
        new_action.triggered.connect(self._new_setup)
        file_menu.addAction(new_action)

        load_action = QAction("Load Setup...", self)
        load_action.setShortcut("Ctrl+O")
        load_action.triggered.connect(self._load_setup_from_file)
        file_menu.addAction(load_action)

        save_action = QAction("Save Setup As...", self)
        save_action.setShortcut("Ctrl+S")
        save_action.triggered.connect(self._save_setup_as)
        file_menu.addAction(save_action)

        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Alt+F4")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        view_menu = self.menu_bar.addMenu("View")
        toggle_theme = QAction("Toggle Theme", self)
        toggle_theme.setShortcut("Ctrl+T")
        toggle_theme.triggered.connect(self._toggle_theme)
        view_menu.addAction(toggle_theme)

        help_menu = self.menu_bar.addMenu("Help")
        about_action = QAction("About AvaSim", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

        howto_action = QAction("How to run a simulation", self)
        howto_action.triggered.connect(self._show_howto)
        help_menu.addAction(howto_action)

        shortcuts_action = QAction("Keyboard shortcuts", self)
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)

        updates_action = QAction("Check for Updates", self)
        updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(updates_action)

        updates_action = QAction("Check for Updates", self)
        updates_action.triggered.connect(self._check_for_updates)
        help_menu.addAction(updates_action)

        export_logs = QAction("Export Logs (Text)...", self)
        export_logs.setShortcut("Ctrl+E")
        export_logs.triggered.connect(self._export_logs)
        file_menu.addAction(export_logs)

        export_html = QAction("Export Logs (HTML)...", self)
        export_html.triggered.connect(self._export_logs_html)
        file_menu.addAction(export_html)

        export_csv = QAction("Export Logs (CSV)...", self)
        export_csv.triggered.connect(self._export_logs_csv)
        file_menu.addAction(export_csv)

    def _toggle_theme(self) -> None:
        next_theme = "Light" if self.theme_combo.currentText() == "Dark" else "Dark"
        self.theme_combo.setCurrentText(next_theme)

    # ------------------------------------------------------------------
    # Dynamic combatant editor management
    # ------------------------------------------------------------------

    def _add_combatant_editor(self) -> None:
        """Add a new CombatantEditor to the character panel (max 8)."""
        if len(self.combatant_editors) >= 8:
            self._show_toast("Maximum of 8 combatants reached.", "warning")
            return
        idx = len(self.combatant_editors) + 1
        team_cycle = ["Team A", "Team B", "Team C", "Team D"]
        default_team = team_cycle[(idx - 1) % len(team_cycle)]
        editor = CombatantEditor(f"Character {idx}")
        editor.team_choice.setCurrentText(default_team)
        self.combatant_editors.append(editor)
        self.editors_layout.addWidget(editor)
        editor.name_input.textChanged.connect(self._refresh_scenario_preview)
        editor.hand1_choice.currentTextChanged.connect(self._update_action_availability)
        editor.hand2_choice.currentTextChanged.connect(self._update_action_availability)
        self.remove_combatant_btn.setEnabled(len(self.combatant_editors) > 2)
        self.add_combatant_btn.setEnabled(len(self.combatant_editors) < 8)
        # Update map tool combo with new placement option
        self._rebuild_map_tool_combo()
        self._refresh_scenario_preview()

    def _remove_combatant_editor(self) -> None:
        """Remove the last CombatantEditor (minimum 2)."""
        if len(self.combatant_editors) <= 2:
            return
        editor = self.combatant_editors.pop()
        self.editors_layout.removeWidget(editor)
        editor.setParent(None)
        editor.deleteLater()
        self.remove_combatant_btn.setEnabled(len(self.combatant_editors) > 2)
        self.add_combatant_btn.setEnabled(len(self.combatant_editors) < 8)
        self._rebuild_map_tool_combo()
        self._refresh_scenario_preview()

    def _rebuild_map_tool_combo(self) -> None:
        """Rebuild the map tool combo to reflect current combatant count."""
        if not hasattr(self, "map_tool_combo"):
            return
        current = self.map_tool_combo.currentText()
        self.map_tool_combo.blockSignals(True)
        self.map_tool_combo.clear()
        tools = ["Paint Terrain", "Erase Terrain"]
        for i, ed in enumerate(self.combatant_editors, 1):
            tools.append(f"Place Character {i}")
        self.map_tool_combo.addItems(tools)
        idx = self.map_tool_combo.findText(current)
        if idx >= 0:
            self.map_tool_combo.setCurrentIndex(idx)
        self.map_tool_combo.blockSignals(False)

    def _default_positions(self, count: int) -> list[tuple[int, int]]:
        """Return default starting positions for N combatants spread across the map."""
        positions = [
            (0, 0), (3, 0), (0, 3), (3, 3),
            (1, 1), (2, 1), (1, 2), (2, 2),
        ]
        # Scale positions to current map size
        w, h = self.scenario_width, self.scenario_height
        scaled: list[tuple[int, int]] = []
        if count <= 2:
            scaled = [(0, 0), (min(3, w - 1), 0)]
        else:
            # Spread combatants along edges / corners
            corners = [
                (0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1),
            ]
            scaled = corners[:count]
        # Deduplicate
        seen: set[tuple[int, int]] = set()
        result: list[tuple[int, int]] = []
        for pos in scaled:
            p = (max(0, min(w - 1, pos[0])), max(0, min(h - 1, pos[1])))
            while p in seen:
                p = ((p[0] + 1) % w, p[1])
            seen.add(p)
            result.append(p)
        return result[:count]

    def _get_scenario_positions(self, count: int) -> list[tuple[int, int]]:
        """Get positions for N combatants.  Uses legacy attacker/defender pos for 2,
        or scenario_positions list, falling back to _default_positions."""
        # Keep legacy positions in sync
        if count <= 2:
            return [self.scenario_attacker_pos, self.scenario_defender_pos][:count]
        # Extend scenario_positions if needed
        while len(self.scenario_positions) < count:
            extras = self._default_positions(count)
            for pos in extras:
                if pos not in self.scenario_positions:
                    self.scenario_positions.append(pos)
                    if len(self.scenario_positions) >= count:
                        break
            else:
                # Fallback: just add next free cell
                w, h = self.scenario_width, self.scenario_height
                for y in range(h):
                    for x in range(w):
                        if (x, y) not in self.scenario_positions:
                            self.scenario_positions.append((x, y))
                            break
                    if len(self.scenario_positions) >= count:
                        break
        return self.scenario_positions[:count]

    # ------------------------------------------------------------------

    def _new_setup(self) -> None:
        resp = QMessageBox.question(self, "Reset setup", "Reset all characters and settings to defaults?", QMessageBox.Yes | QMessageBox.No)
        if resp != QMessageBox.Yes:
            return
        # Remove extra editors back to 2
        while len(self.combatant_editors) > 2:
            self._remove_combatant_editor()
        self.attacker_editor.load_template(self.attacker_editor._blank_template())
        self.attacker_editor.team_choice.setCurrentText("Team A")
        self.defender_editor.load_template(self.defender_editor._blank_template())
        self.defender_editor.team_choice.setCurrentText("Team B")
        self.theme_combo.setCurrentText("Dark")
        self.time_combo.setCurrentText("Day")
        self.mode_combo.setCurrentText("Full Auto (both AI)")
        self.show_math_check.setChecked(False)
        preset = self._scenario_presets.get("Duel")
        if preset:
            self._apply_scenario_dict(preset)
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentText("Duel")
        self._on_mode_changed()
        self._apply_theme()
        self._save_settings()

    def _apply_quickstart(self) -> None:
        data = self.quickstart_setup
        self.attacker_editor.load_template(data.get("char1", {}))
        self.defender_editor.load_template(data.get("char2", {}))
        self._set_combo_text(self.theme_combo, data.get("theme", "Light"))
        self._set_combo_text(self.time_combo, data.get("time", "Day"))
        self._set_combo_text(self.mode_combo, data.get("mode", "Full Auto (both AI)"))
        self.show_math_check.setChecked(data.get("show_math", False))
        preset = self._scenario_presets.get("Duel")
        if preset:
            self._apply_scenario_dict(preset)
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentText("Duel")
        self._on_mode_changed()
        self._apply_theme()
        self._save_settings()

    def _reload_last_setup(self) -> None:
        # Reload persisted settings and reapply theme; stay on current tab unless user prefers simulation
        self._load_settings()
        self._apply_theme()

    def _collect_setup_data(self) -> dict:
        return {
            "theme": self.theme_combo.currentText(),
            "time": self.time_combo.currentText(),
            "mode": self.mode_combo.currentText(),
            "surprise": self.surprise_combo.currentText(),
            # New N-combatant format
            "combatants": [ed.to_template() for ed in self.combatant_editors],
            # Legacy keys for backward compat
            "char1": self.attacker_editor.to_template(),
            "char2": self.defender_editor.to_template(),
            "show_math": self.show_math_check.isChecked(),
            "scenario": self._serialize_scenario(),
        }

    def _apply_setup_data(self, data: dict) -> None:
        if not data:
            return
        # N-combatant format (new)
        combatants = data.get("combatants")
        if combatants and isinstance(combatants, list):
            # Adjust editor count to match saved data
            while len(self.combatant_editors) > len(combatants) and len(self.combatant_editors) > 2:
                self._remove_combatant_editor()
            while len(self.combatant_editors) < len(combatants) and len(self.combatant_editors) < 8:
                self._add_combatant_editor()
            for ed, tmpl in zip(self.combatant_editors, combatants):
                ed.load_template(tmpl)
        else:
            # Legacy 2-combatant format
            self.attacker_editor.load_template(data.get("char1", {}))
            self.defender_editor.load_template(data.get("char2", {}))
        self._set_combo_text(self.theme_combo, data.get("theme", self.theme_combo.currentText()))
        self._set_combo_text(self.time_combo, data.get("time", self.time_combo.currentText()))
        self._set_combo_text(self.mode_combo, data.get("mode", self.mode_combo.currentText()))
        self._set_combo_text(self.surprise_combo, data.get("surprise", self.surprise_combo.currentText()))
        self.show_math_check.setChecked(bool(data.get("show_math", False)))
        if "scenario" in data:
            self._apply_scenario_dict(data.get("scenario", {}), update_preview=False)
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentText("Custom")
        self._on_theme_changed()
        self._on_time_changed()
        self._on_surprise_changed()
        self._on_mode_changed()
        self._refresh_scenario_preview()

    def _build_scenario_presets(self) -> dict[str, dict]:
        duel = {
            "width": 10,
            "height": 10,
            "attacker_pos": [0, 0],
            "defender_pos": [3, 0],
            "terrain": [],
        }

        skirmish_terrain = [{"x": x, "y": 5, "terrain": "road"} for x in range(2, 10)]
        skirmish_terrain += [
            {"x": 2, "y": 2, "terrain": "forest"},
            {"x": 3, "y": 2, "terrain": "forest"},
            {"x": 2, "y": 3, "terrain": "forest"},
            {"x": 8, "y": 8, "terrain": "forest"},
            {"x": 9, "y": 8, "terrain": "forest"},
            {"x": 8, "y": 9, "terrain": "forest"},
        ]
        skirmish = {
            "width": 12,
            "height": 12,
            "attacker_pos": [1, 1],
            "defender_pos": [10, 10],
            "terrain": skirmish_terrain,
        }

        siege_terrain = []
        for y in range(10):
            if y == 5:
                continue
            siege_terrain.append({"x": 7, "y": y, "terrain": "wall"})
        siege_terrain += [{"x": x, "y": 5, "terrain": "road"} for x in range(14)]
        siege = {
            "width": 14,
            "height": 10,
            "attacker_pos": [2, 5],
            "defender_pos": [11, 5],
            "terrain": siege_terrain,
        }
        return {"Duel": duel, "Skirmish": skirmish, "Siege": siege,
                "2v2 Skirmish": self._build_2v2_preset(),
                "1v3 Ambush": self._build_1v3_preset(),
                "Free-for-All": self._build_ffa_preset()}

    def _build_2v2_preset(self) -> dict:
        terrain = [
            {"x": 3, "y": 2, "terrain": "forest"},
            {"x": 3, "y": 3, "terrain": "forest"},
            {"x": 8, "y": 7, "terrain": "forest"},
            {"x": 8, "y": 8, "terrain": "forest"},
            {"x": 5, "y": 5, "terrain": "road"},
            {"x": 6, "y": 5, "terrain": "road"},
        ]
        return {
            "width": 12, "height": 12,
            "attacker_pos": [1, 1], "defender_pos": [10, 10],
            "positions": [[1, 1], [1, 3], [10, 10], [10, 8]],
            "terrain": terrain,
            "combatants": 4,
            "teams": ["Team A", "Team A", "Team B", "Team B"],
        }

    def _build_1v3_preset(self) -> dict:
        terrain = [
            {"x": 6, "y": 4, "terrain": "elevation"},
            {"x": 6, "y": 5, "terrain": "elevation"},
            {"x": 6, "y": 6, "terrain": "elevation"},
        ]
        return {
            "width": 12, "height": 10,
            "attacker_pos": [6, 5], "defender_pos": [2, 2],
            "positions": [[6, 5], [2, 2], [2, 8], [10, 5]],
            "terrain": terrain,
            "combatants": 4,
            "teams": ["Team A", "Team B", "Team B", "Team B"],
        }

    def _build_ffa_preset(self) -> dict:
        terrain = [
            {"x": 4, "y": 4, "terrain": "forest"},
            {"x": 5, "y": 4, "terrain": "forest"},
            {"x": 4, "y": 5, "terrain": "forest"},
            {"x": 5, "y": 5, "terrain": "forest"},
        ]
        return {
            "width": 10, "height": 10,
            "attacker_pos": [0, 0], "defender_pos": [9, 9],
            "positions": [[0, 0], [9, 9], [0, 9]],
            "terrain": terrain,
            "combatants": 3,
            "teams": ["FFA", "FFA", "FFA"],
        }

    def _serialize_scenario(self) -> dict:
        return {
            "width": int(self.scenario_width),
            "height": int(self.scenario_height),
            "attacker_pos": [int(self.scenario_attacker_pos[0]), int(self.scenario_attacker_pos[1])],
            "defender_pos": [int(self.scenario_defender_pos[0]), int(self.scenario_defender_pos[1])],
            "positions": [[int(p[0]), int(p[1])] for p in self.scenario_positions],
            "terrain": [
                {"x": int(x), "y": int(y), "terrain": terrain}
                for (x, y), terrain in sorted(self.scenario_cells.items())
            ],
            "time": self.time_combo.currentText(),
        }

    def _apply_scenario_dict(self, data: dict, update_preview: bool = True) -> None:
        if not data:
            return
        width = int(data.get("width", self.scenario_width))
        height = int(data.get("height", self.scenario_height))
        self.scenario_width = max(4, min(40, width))
        self.scenario_height = max(4, min(40, height))
        if hasattr(self, "map_width_spin"):
            self.map_width_spin.setValue(self.scenario_width)
        if hasattr(self, "map_height_spin"):
            self.map_height_spin.setValue(self.scenario_height)
        if hasattr(self, "tactical_map_widget"):
            self.tactical_map_widget.set_grid_dimensions(self.scenario_width, self.scenario_height)
        attacker_pos = data.get("attacker_pos", self.scenario_attacker_pos)
        defender_pos = data.get("defender_pos", self.scenario_defender_pos)
        self.scenario_attacker_pos = (int(attacker_pos[0]), int(attacker_pos[1]))
        self.scenario_defender_pos = (int(defender_pos[0]), int(defender_pos[1]))
        # Load N positions if present, else rebuild from legacy
        saved_positions = data.get("positions")
        if saved_positions and isinstance(saved_positions, list):
            self.scenario_positions = [(int(p[0]), int(p[1])) for p in saved_positions]
        else:
            self.scenario_positions = [self.scenario_attacker_pos, self.scenario_defender_pos]
        self.scenario_cells = {}
        for cell in data.get("terrain", []):
            x = int(cell.get("x", 0))
            y = int(cell.get("y", 0))
            terrain = str(cell.get("terrain", "normal"))
            if 0 <= x < self.scenario_width and 0 <= y < self.scenario_height and terrain != "normal":
                self.scenario_cells[(x, y)] = terrain
        self._move_path_preview = []
        self._ensure_scenario_positions()
        self._update_move_limits()
        self._update_move_preview()
        if "time" in data:
            self._set_combo_text(self.time_combo, data.get("time"))
        if update_preview:
            self._refresh_scenario_preview()
            self._update_move_button_state()

    def _ensure_scenario_positions(self) -> None:
        ax, ay = self.scenario_attacker_pos
        dx, dy = self.scenario_defender_pos
        ax = max(0, min(self.scenario_width - 1, ax))
        ay = max(0, min(self.scenario_height - 1, ay))
        dx = max(0, min(self.scenario_width - 1, dx))
        dy = max(0, min(self.scenario_height - 1, dy))
        self.scenario_attacker_pos = (ax, ay)
        self.scenario_defender_pos = (dx, dy)
        if self.scenario_attacker_pos == self.scenario_defender_pos:
            new_dx = min(self.scenario_width - 1, ax + 1)
            if new_dx == ax:
                new_dx = max(0, ax - 1)
            self.scenario_defender_pos = (new_dx, dy)

    def _update_move_limits(self) -> None:
        if hasattr(self, "move_x"):
            self.move_x.setMaximum(max(0, self.scenario_width - 1))
        if hasattr(self, "move_y"):
            self.move_y.setMaximum(max(0, self.scenario_height - 1))
        self._update_move_button_state()

    def _update_move_button_state(self) -> None:
        if not hasattr(self, "move_button"):
            return
        target = (int(self.move_x.value()), int(self.move_y.value()))
        preview_map = self._build_scenario_map_only()
        tile = preview_map.get_tile(*target)
        positions = self._get_scenario_positions(len(self.combatant_editors))
        occupied = target in positions[1:]  # Can't move onto another combatant
        valid = tile is not None and tile.passable and not occupied
        self.move_button.setEnabled(valid)

    def _resize_scenario_map(self) -> None:
        self.scenario_width = int(self.map_width_spin.value())
        self.scenario_height = int(self.map_height_spin.value())
        self.scenario_cells = {
            (x, y): t
            for (x, y), t in self.scenario_cells.items()
            if x < self.scenario_width and y < self.scenario_height
        }
        self._ensure_scenario_positions()
        self._update_move_limits()
        if hasattr(self, "tactical_map_widget"):
            self.tactical_map_widget.set_grid_dimensions(self.scenario_width, self.scenario_height)
        self._refresh_scenario_preview()
        if hasattr(self, "preset_combo"):
            self.preset_combo.setCurrentText("Custom")

    def _clear_scenario_terrain(self) -> None:
        self.scenario_cells = {}
        self._refresh_scenario_preview()
        if hasattr(self, "preset_combo"):
            self.preset_combo.setCurrentText("Custom")

    def _load_preset(self) -> None:
        preset_name = self.preset_combo.currentText()
        if preset_name == "Custom":
            return
        preset = self._scenario_presets.get(preset_name)
        if not preset:
            return
        # Adjust number of combatant editors for multi-combatant presets
        needed = preset.get("combatants", 2)
        while len(self.combatant_editors) < needed:
            self._add_combatant_editor()
        while len(self.combatant_editors) > needed and len(self.combatant_editors) > 2:
            self._remove_combatant_editor()
        # Set team assignments if provided
        teams = preset.get("teams")
        if teams:
            for i, team_name in enumerate(teams):
                if i < len(self.combatant_editors):
                    self._set_combo_text(self.combatant_editors[i].team_choice, team_name)
        self._apply_scenario_dict(preset)
        self._refresh_scenario_preview()

    def _on_scenario_cell_clicked(self, x: int, y: int) -> None:
        tool = self.map_tool_combo.currentText()
        if tool == "Paint Terrain":
            terrain = self.terrain_combo.currentText().lower()
            if terrain == "normal":
                self.scenario_cells.pop((x, y), None)
            else:
                self.scenario_cells[(x, y)] = terrain
        elif tool == "Erase Terrain":
            self.scenario_cells.pop((x, y), None)
        elif tool.startswith("Place Character "):
            try:
                idx = int(tool.split()[-1]) - 1
            except (ValueError, IndexError):
                idx = 0
            # Extend positions list if needed
            while len(self.scenario_positions) <= idx:
                self.scenario_positions.append((0, 0))
            self.scenario_positions[idx] = (x, y)
            # Keep legacy attacker/defender in sync
            if idx == 0:
                self.scenario_attacker_pos = (x, y)
            elif idx == 1:
                self.scenario_defender_pos = (x, y)
        self._refresh_scenario_preview()
        if hasattr(self, "preset_combo"):
            self.preset_combo.setCurrentText("Custom")

    def _on_scenario_cell_hover(self, x: int, y: int) -> None:
        self._hover_cell = (x, y)
        if self.overlay_path_check.isChecked():
            self._refresh_scenario_preview()

    def _range_bounds_for_weapon(self, weapon) -> tuple[int, int]:
        if weapon.range_category == RangeCategory.MELEE:
            return (0, 1)
        if weapon.range_category == RangeCategory.SKIRMISHING:
            return (2, 8)
        if weapon.range_category == RangeCategory.RANGED:
            return (6, 30)
        return (0, 1)

    def _is_distance_in_range(self, weapon, distance: int) -> bool:
        min_r, max_r = self._range_bounds_for_weapon(weapon)
        return min_r <= distance <= max_r

    def _update_action_availability(self) -> None:
        if not hasattr(self, "player_action1_combo"):
            return
        dist = abs(self.scenario_attacker_pos[0] - self.scenario_defender_pos[0]) + abs(
            self.scenario_attacker_pos[1] - self.scenario_defender_pos[1]
        )
        attacker = self.attacker_editor.to_participant()
        weapon = attacker.weapon_main or AVALORE_WEAPONS["Unarmed"]
        attack_ok = self._is_distance_in_range(weapon, dist)
        has_shield = attacker.shield is not None
        for combo in (self.player_action1_combo, self.player_action2_combo):
            # Disable Attack when out of range
            idx_attack = combo.findText("Attack")
            if idx_attack >= 0:
                item = combo.model().item(idx_attack)
                if item:
                    item.setEnabled(attack_ok)
                if not attack_ok and combo.currentText() == "Attack":
                    combo.setCurrentText("Skip")
            # Disable Block when no shield equipped
            idx_block = combo.findText("Block")
            if idx_block >= 0:
                item = combo.model().item(idx_block)
                if item:
                    item.setEnabled(has_shield)
                if not has_shield and combo.currentText() == "Block":
                    combo.setCurrentText("Skip")

    def _build_overlay_data(self) -> tuple[dict, list]:
        overlays: dict[str, list[tuple[int, int]]] = {}
        path: list[tuple[int, int]] = []
        if not hasattr(self, "overlay_source_combo"):
            return overlays, path
        source = self.overlay_source_combo.currentText()
        if source == "None":
            return overlays, path
        actor_pos = self.scenario_attacker_pos if source == "Character 1" else self.scenario_defender_pos
        participant = self.attacker_editor.to_participant() if source == "Character 1" else self.defender_editor.to_participant()
        weapon = participant.weapon_main or AVALORE_WEAPONS["Unarmed"]
        preview_map = self._build_scenario_map_only()
        if self.overlay_range_check.isChecked():
            min_r, max_r = self._range_bounds_for_weapon(weapon)
            overlays["range"] = preview_map.get_tiles_in_range(actor_pos[0], actor_pos[1], min_r, max_r)
        if self.overlay_los_check.isChecked():
            los_cells = []
            blocked_cells = []
            for y in range(self.scenario_height):
                for x in range(self.scenario_width):
                    if preview_map.has_line_of_sight(actor_pos, (x, y)):
                        los_cells.append((x, y))
                    else:
                        blocked_cells.append((x, y))
            overlays["los"] = los_cells
            overlays["blocked"] = blocked_cells
        if self.overlay_path_check.isChecked():
            if getattr(self, "_move_path_preview", None):
                path = self._move_path_preview
            elif self._hover_cell:
                path = preview_map.find_path(actor_pos[0], actor_pos[1], self._hover_cell[0], self._hover_cell[1]) or []
        return overlays, path

    def _scenario_snapshot(self) -> dict:
        positions = self._get_scenario_positions(len(self.combatant_editors))
        pos_to_name: dict[tuple[int, int], str] = {}
        for i, ed in enumerate(self.combatant_editors):
            if i < len(positions):
                name = ed.name_input.text() or f"Character {i + 1}"
                pos_to_name[positions[i]] = name
        cells = []
        for y in range(self.scenario_height):
            for x in range(self.scenario_width):
                terrain = self.scenario_cells.get((x, y), "normal")
                occupant = pos_to_name.get((x, y))
                cells.append({
                    "x": x,
                    "y": y,
                    "terrain": terrain,
                    "occupant": occupant,
                })
        overlays, path = self._build_overlay_data()
        actor_pos = positions[0] if positions else self.scenario_attacker_pos
        target_pos = positions[1] if len(positions) > 1 else self.scenario_defender_pos
        return {
            "label": "Scenario",
            "width": self.scenario_width,
            "height": self.scenario_height,
            "cells": cells,
            "actor": {"position": actor_pos},
            "target": {"position": target_pos},
            "overlays": overlays,
            "path": path,
        }

    def _refresh_scenario_preview(self) -> None:
        if hasattr(self, "tactical_map_widget"):
            self.tactical_map_widget.draw_snapshot(self._scenario_snapshot())
        self._update_action_availability()
        self._update_move_button_state()

    def _build_tactical_map(self, participants: list[CombatParticipant]) -> TacticalMap:
        tactical_map = TacticalMap(self.scenario_width, self.scenario_height)
        terrain_costs = {
            "forest": 2,
            "water": 2,
            "mountain": 3,
            "road": 1,
            "wall": 999,
        }
        for (x, y), terrain in self.scenario_cells.items():
            tile = tactical_map.get_tile(x, y)
            if not tile:
                continue
            terrain_enum = TerrainType(terrain) if terrain in TerrainType._value2member_map_ else TerrainType.NORMAL
            tile.terrain_type = terrain_enum
            if terrain == "wall":
                tile.passable = False
            if terrain in terrain_costs and terrain != "wall":
                tile.move_cost = terrain_costs[terrain]
        # Assign positions to all participants
        positions = self._get_scenario_positions(len(participants))
        for p, pos in zip(participants, positions):
            p.position = pos
            tactical_map.set_occupant(*pos, p)
        return tactical_map

    def _build_scenario_map_only(self) -> TacticalMap:
        tactical_map = TacticalMap(self.scenario_width, self.scenario_height)
        terrain_costs = {
            "forest": 2,
            "water": 2,
            "mountain": 3,
            "road": 1,
            "wall": 999,
        }
        for (x, y), terrain in self.scenario_cells.items():
            tile = tactical_map.get_tile(x, y)
            if not tile:
                continue
            terrain_enum = TerrainType(terrain) if terrain in TerrainType._value2member_map_ else TerrainType.NORMAL
            tile.terrain_type = terrain_enum
            if terrain == "wall":
                tile.passable = False
            if terrain in terrain_costs and terrain != "wall":
                tile.move_cost = terrain_costs[terrain]
        return tactical_map

    def _decorate_snapshot(self, snapshot: dict, include_path: bool = False, engine: AvaCombatEngine | None = None) -> dict:
        decorated = copy.deepcopy(snapshot)
        decorated["overlays"] = self._build_overlays_for_snapshot(decorated, engine)
        if include_path and getattr(self, "_move_path_preview", None):
            decorated["path"] = self._move_path_preview
        return decorated

    def _build_overlays_for_snapshot(self, snapshot: dict, engine: AvaCombatEngine | None = None) -> dict:
        overlays: dict[str, list[tuple[int, int]]] = {}
        actor_pos = snapshot.get("actor", {}).get("position")
        target_pos = snapshot.get("target", {}).get("position")
        if actor_pos:
            min_range = 0
            max_range = 8
            if engine:
                actor_name = snapshot.get("actor", {}).get("name")
                actor = next((p for p in engine.participants if getattr(p.character, "name", None) == actor_name), None)
                if actor:
                    weapon = actor.weapon_main or AVALORE_WEAPONS["Unarmed"]
                    if weapon.range_category == RangeCategory.MELEE:
                        min_range, max_range = 0, 1
                    elif weapon.range_category == RangeCategory.SKIRMISHING:
                        min_range, max_range = 2, 8
                    else:
                        min_range, max_range = 6, 30
            ax, ay = actor_pos
            cells = []
            for y in range(snapshot.get("height", 0)):
                for x in range(snapshot.get("width", 0)):
                    dist = abs(x - ax) + abs(y - ay)
                    if min_range <= dist <= max_range:
                        cells.append((x, y))
            overlays["range"] = cells
        if actor_pos and target_pos:
            line_cells = self._line_cells(actor_pos, target_pos)
            visible = self._has_line_of_sight(snapshot, actor_pos, target_pos, engine)
            overlays["los" if visible else "blocked"] = line_cells
        return overlays

    def _line_cells(self, a: tuple[int, int], b: tuple[int, int]) -> list[tuple[int, int]]:
        ax, ay = a
        bx, by = b
        dx = abs(bx - ax)
        dy = -abs(by - ay)
        sx = 1 if ax < bx else -1
        sy = 1 if ay < by else -1
        err = dx + dy
        x, y = ax, ay
        cells = []
        while True:
            cells.append((x, y))
            if (x, y) == (bx, by):
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x += sx
            if e2 <= dx:
                err += dx
                y += sy
        return cells

    def _has_line_of_sight(self, snapshot: dict, a: tuple[int, int], b: tuple[int, int], engine: AvaCombatEngine | None) -> bool:
        if engine and engine.tactical_map:
            return engine.tactical_map.has_line_of_sight(a, b)
        terrain_map = {(cell["x"], cell["y"]): cell.get("terrain", "normal") for cell in snapshot.get("cells", [])}
        for x, y in self._line_cells(a, b):
            if (x, y) not in (a, b) and terrain_map.get((x, y)) == "wall":
                return False
        return True

    def _update_move_preview(self) -> None:
        if not hasattr(self, "move_x") or not hasattr(self, "move_y"):
            return
        try:
            tactical_map = self._build_scenario_map_only()
            start = self.scenario_attacker_pos
            goal = (int(self.move_x.value()), int(self.move_y.value()))
            if start == goal:
                self._move_path_preview = []
            else:
                path = tactical_map.find_path(start[0], start[1], goal[0], goal[1])
                self._move_path_preview = path or []
            self._refresh_scenario_preview()
        except Exception:
            # Avoid blocking input if preview fails
            self._move_path_preview = []

    def _open_scenario_editor(self) -> None:
        dialog = ScenarioEditorDialog(
            self._serialize_scenario(),
            self.attacker_editor.name_input.text(),
            self.defender_editor.name_input.text(),
            self,
        )
        if dialog.exec() == QDialog.Accepted:
            self._apply_scenario_dict(dialog.get_scenario())
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentText("Custom")
            self._save_settings()

    def _save_scenario(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Scenario", "avasim_scenario.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self._serialize_scenario(), f, indent=2)
            QMessageBox.information(self, "Scenario saved", "Scenario saved successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", f"Could not save scenario:\n{exc}")

    def _load_scenario(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Scenario", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_scenario_dict(data)
            if hasattr(self, "preset_combo"):
                self.preset_combo.setCurrentText("Custom")
            self._save_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", f"Could not load scenario:\n{exc}")

    def _save_setup_as(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Setup", "avasim_setup.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            self._write_setup(Path(path), self._collect_setup_data())
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", f"Could not save setup:\n{exc}")

    def _load_setup_from_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Setup", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_setup_data(data)
            self._apply_theme()
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", f"Could not load setup:\n{exc}")

    def _write_setup(self, path: Path, data: dict) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _save_settings(self) -> None:
        try:
            self._write_setup(self.settings_path, self._collect_setup_data())
        except Exception:
            # avoid blocking close on save failure
            pass

    def _load_settings(self) -> None:
        if not self.settings_path.exists():
            return
        try:
            with open(self.settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._apply_setup_data(data)
            self._settings_loaded = True
        except Exception:
            pass

    def _set_combo_text(self, combo: QComboBox, text: str) -> None:
        if text is None:
            return
        idx = combo.findText(text)
        if idx >= 0:
            combo.setCurrentIndex(idx)

    def _show_about(self) -> None:
        QMessageBox.information(self, "About AvaSim", "AvaSim Combat Sandbox\nWindows-friendly PySide6 desktop app for Avalore-inspired encounters.")

    def _render_action_log(self, lines: list[str]) -> str:
        """Render action log with syntax highlighting."""
        return TextHighlighter.highlight_html(lines)

    def _collapse_log_runs(self, lines: list[str]) -> list[str]:
        if not lines:
            return []
        collapsed = []
        prev = lines[0]
        count = 1
        for line in lines[1:]:
            if line == prev:
                count += 1
                continue
            if count > 1:
                collapsed.append(f"{prev} (x{count})")
            else:
                collapsed.append(prev)
            prev = line
            count = 1
        if count > 1:
            collapsed.append(f"{prev} (x{count})")
        else:
            collapsed.append(prev)
        return collapsed

    def _set_action_log(self, lines: list[str]) -> None:
        self._last_action_lines = list(lines)
        self._rerender_action_log()

    def _rerender_action_log(self) -> None:
        if not hasattr(self, "action_view"):
            return
        lines = self._last_action_lines or []
        if self.collapse_log_check.isChecked():
            lines = self._collapse_log_runs(lines)
        self.action_view.setHtml(self._render_action_log(lines))

    def _toggle_decision_drawer(self) -> None:
        # In the new layout, decisions are always in a tab. Toggle switches to that tab.
        if hasattr(self, "log_tabs") and self.decision_toggle.isChecked():
            for i in range(self.log_tabs.count()):
                if "Decision" in self.log_tabs.tabText(i):
                    self.log_tabs.setCurrentIndex(i)
                    break

    def _log_decision(self, engine: AvaCombatEngine, message: str) -> None:
        if not self.show_math_check.isChecked():
            return
        self.decision_log.append(message)
        engine.combat_log.append(message)

    def _set_decision_log(self) -> None:
        if not hasattr(self, "decision_view"):
            return
        if not self.decision_log:
            self.decision_view.setPlainText("No decision data recorded.")
        else:
            self.decision_view.setPlainText("\n".join(self.decision_log))

    def _show_toast(self, message: str, kind: str = "info") -> None:
        color_map = {"info": "#222", "warning": "#805b00", "error": "#7a1f1f", "success": "#1f5f2a"}
        bg = color_map.get(kind, "#222")
        self.toast_label.setStyleSheet(
            f"background:{bg};color:#fff;padding:6px 12px;border-radius:6px;font-size:10pt;"
        )
        self.toast_label.setText(message)
        self.toast_label.setVisible(True)
        QTimer.singleShot(2500, lambda: self.toast_label.setVisible(False))

    def _render_map_grid(self, tactical_map: TacticalMap | None) -> None:
        if tactical_map is None:
            return
        rows = tactical_map.height
        cols = tactical_map.width
        self.map_grid.setRowCount(rows)
        self.map_grid.setColumnCount(cols)
        for c in range(cols):
            self.map_grid.setColumnWidth(c, 28)
        for r in range(rows):
            self.map_grid.setRowHeight(r, 24)
        for y in range(rows):
            for x in range(cols):
                occupant = tactical_map.get_occupant(x, y)
                txt = occupant.character.name[:2] if occupant else ""
                item = QTableWidgetItem(txt)
                if occupant:
                    item.setBackground(QColor("#ffe8c2"))
                else:
                    item.setBackground(QColor("#f4f4f4"))
                item.setTextAlignment(Qt.AlignCenter)
                self.map_grid.setItem(y, x, item)
        self.map_grid.resizeColumnsToContents()
        self.map_grid.resizeRowsToContents()

    def _render_visual_map(self, snapshot: dict | None) -> None:
        """Render visual tactical map using enhanced widget."""
        if hasattr(self, 'tactical_map_widget'):
            if snapshot:
                # Build occupant detail dict for rich tooltips
                occupant_details: dict[tuple[int, int], dict] = {}
                engine = getattr(self, "_last_engine", None)
                if engine:
                    for p in engine.participants:
                        if p.position:
                            statuses = []
                            if p.is_blocking:
                                statuses.append("Blocking")
                            if p.is_evading:
                                statuses.append("Evading")
                            if p.bastion_active:
                                statuses.append("Bastion")
                            if p.flowing_stance:
                                statuses.append("Flowing Stance")
                            if p.is_critical:
                                statuses.append("Critical")
                            if p.inspired_scene:
                                statuses.append("Inspired")
                            for se in getattr(p, "status_effects", set()):
                                statuses.append(se.name.title())
                            occupant_details[tuple(p.position)] = {
                                "hp": p.current_hp,
                                "max_hp": p.max_hp,
                                "weapon": p.weapon_main.name if p.weapon_main else "Unarmed",
                                "armor": p.armor.name if p.armor else "None",
                                "statuses": statuses,
                            }
                self.tactical_map_widget.set_occupant_details(occupant_details)
                decorated = self._decorate_snapshot(snapshot, engine=self._last_engine)
                self.tactical_map_widget.draw_snapshot(decorated)
            else:
                self.tactical_map_widget.set_occupant_details({})
                self.tactical_map_widget.draw_snapshot(None)

    def _show_howto(self) -> None:
        QMessageBox.information(
            self,
            "How to run a simulation",
            "AvaSim supports three simulation modes:\n\n"
            "🤖 AI vs AI (Full Combat)\n"
            "  Both characters are controlled by the AI engine.\n"
            "  Select a strategy (aggressive, defensive, balanced, random)\n"
            "  and click 'Run full combat' to watch the entire fight play out.\n\n"
            "🎮 Player controls Character 1\n"
            "  You choose actions for Character 1 each turn using the\n"
            "  Action 1 / Action 2 dropdowns. The AI controls opponents.\n"
            "  After selecting actions, click 'Execute Turn'.\n\n"
            "🎮 Player controls both\n"
            "  You control both characters' actions each turn.\n\n"
            "📊 Batch Simulation\n"
            "  Run 100-10,000 combats with the same setup to get\n"
            "  win rates and average stats. Click 'Batch Sim' to start.\n\n"
            "🔀 Compare Loadouts\n"
            "  Swap Character 1's weapon and run two batch simulations\n"
            "  side-by-side to see how loadout changes affect win rates.\n\n"
            "Quick start: Use the Preset dropdown to load a pre-built\n"
            "scenario, then click 'Run full combat'.",
        )

    def _show_shortcuts(self) -> None:
        QMessageBox.information(
            self,
            "Keyboard shortcuts",
            "Ctrl+N: New setup\nCtrl+O: Load setup\nCtrl+S: Save setup as\nCtrl+E: Export logs\nCtrl+T: Toggle theme\nAlt+F4: Exit",
        )

    def _check_for_updates(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/Von-Van/avasim"))

    def _check_for_updates(self) -> None:
        QDesktopServices.openUrl(QUrl("https://github.com/Von-Van/avasim"))

    def _export_logs(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Logs",
            "avasim_logs.txt",
            "Text Files (*.txt);;HTML Files (*.html);;CSV Files (*.csv)",
        )
        if not path:
            return
        try:
            suffix = Path(path).suffix.lower()
            action_lines = self._last_action_lines or self.action_view.toPlainText().splitlines()
            map_lines = self.map_view.toPlainText().splitlines()
            if suffix == ".html":
                action_html = self._render_action_log(action_lines)
                map_html = "<br>".join(html.escape(line) for line in map_lines)
                html_doc = (
                    "<html><head><meta charset='utf-8'><title>AvaSim Logs</title></head><body>"
                    "<h2>Action Log</h2>"
                    f"{action_html}"
                    "<h2>Map Log</h2>"
                    f"<div style='font-family:monospace;white-space:pre-wrap;'>{map_html}</div>"
                    "</body></html>"
                )
                with open(path, "w", encoding="utf-8") as f:
                    f.write(html_doc)
            elif suffix == ".csv":
                with open(path, "w", encoding="utf-8", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["section", "line"])
                    for line in action_lines:
                        writer.writerow(["action", line])
                    for line in map_lines:
                        writer.writerow(["map", line])
            else:
                with open(path, "w", encoding="utf-8") as f:
                    f.write("Action Log\n" + "\n".join(action_lines) + "\n\n")
                    f.write("Map Log\n" + "\n".join(map_lines))
            QMessageBox.information(self, "Export complete", "Logs exported successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not export logs:\n{exc}")

    def _export_logs_html(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs (HTML)", "avasim_logs.html", "HTML Files (*.html)")
        if not path:
            return
        try:
            action_lines = self._last_action_lines or self.action_view.toPlainText().splitlines()
            map_lines = self.map_view.toPlainText().splitlines()
            action_html = self._render_action_log(action_lines)
            map_html = "<br>".join(html.escape(line) for line in map_lines)
            html_doc = (
                "<html><head><meta charset='utf-8'><title>AvaSim Logs</title></head><body>"
                "<h2>Action Log</h2>"
                f"{action_html}"
                "<h2>Map Log</h2>"
                f"<div style='font-family:monospace;white-space:pre-wrap;'>{map_html}</div>"
                "</body></html>"
            )
            with open(path, "w", encoding="utf-8") as f:
                f.write(html_doc)
            QMessageBox.information(self, "Export complete", "HTML log exported successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not export HTML logs:\n{exc}")

    def _export_logs_csv(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Logs (CSV)", "avasim_logs.csv", "CSV Files (*.csv)")
        if not path:
            return
        try:
            action_lines = self._last_action_lines or self.action_view.toPlainText().splitlines()
            map_lines = self.map_view.toPlainText().splitlines()
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["section", "line"])
                for line in action_lines:
                    writer.writerow(["action", line])
                for line in map_lines:
                    writer.writerow(["map", line])
            QMessageBox.information(self, "Export complete", "CSV log exported successfully.")
        except Exception as exc:
            QMessageBox.critical(self, "Export failed", f"Could not export CSV logs:\n{exc}")

    def closeEvent(self, event) -> None:  # type: ignore
        self._save_settings()
        return super().closeEvent(event)

    def run_simulation(self):
        try:
            self.decision_log = []
            participants = [ed.to_participant() for ed in self.combatant_editors]
            tactical_map = self._build_tactical_map(participants)

            engine = AvaCombatEngine(participants, tactical_map=tactical_map)
            self._last_engine = engine
            engine.set_time_of_day(self._time_of_day)
            engine.party_surprised = (self.surprise_combo.currentText() == "Party Surprised")
            engine.party_initiated = (self.surprise_combo.currentText() == "Party Ambushes")

            # Override logger to keep output in-app (no stdout noise)
            def ui_log(message: str):
                engine.combat_log.append(message)

            engine.log = ui_log  # type: ignore

            engine.roll_initiative()

            # Determine simulation length: full or single-turn beta
            mode_text = self.mode_combo.currentText()
            turn_limit = 1 if "Single Simulation" in mode_text else 200
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

                mode_text = self.mode_combo.currentText()
                player_controls_both = "Player controls" in mode_text and "both" in mode_text.lower()
                player_controls_c1 = "Player controls Character 1" in mode_text and current is participants[0]
                if player_controls_both or player_controls_c1:
                    self._execute_player_turn(engine, current, target)
                else:
                    self.combat_ai.decision_log = self.decision_log
                    self.combat_ai.show_decisions = self.show_math_check.isChecked()
                    self.combat_ai.decide_turn(engine, current)

                engine._log_map_state(f"End turn: {current.character.name}")

                engine.advance_turn()
                turns += 1

            engine.combat_log.append(engine.get_combat_summary())

            action_lines = ["Combat finished", f"Turns executed: {turns}", "", "Combat Log:"] + engine.combat_log
            self._set_action_log(action_lines)
            self.map_view.setPlainText("\n".join(engine.map_log))
            self.status_view.setHtml(self._format_status_badges(participants))
            self._update_combat_bars(participants)
            self._render_map_grid(engine.tactical_map)
            self._render_initiative(engine)
            self._set_replay_data(engine.map_snapshots)
            self._set_decision_log()
            self._save_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Simulation failed", f"An error occurred while simulating:\n{exc}")

    def _run_batch_simulation(self) -> None:
        """Run N batch simulations and display win-rate statistics."""
        # Ask the user how many combats to run
        from PySide6.QtWidgets import QInputDialog
        num, ok = QInputDialog.getInt(self, "Batch Simulation", "Number of combats:", 100, 1, 10000, 50)
        if not ok:
            return

        try:
            # Capture editor templates so the factory creates fresh participants each time
            templates = [ed.to_template() for ed in self.combatant_editors]
            team_assignments = [ed.team_choice.currentText() for ed in self.combatant_editors]

            def make_participants() -> list:
                parts = []
                for i, tmpl in enumerate(templates):
                    ed = CombatantEditor(f"Character {i + 1}")
                    ed.load_template(tmpl)
                    p = ed.to_participant()
                    team_text = team_assignments[i]
                    p.team = "" if team_text == "FFA" else team_text
                    parts.append(p)
                    ed.deleteLater()
                return parts

            def make_map(participants):
                return self._build_tactical_map(participants)

            config = BatchConfig(
                participants_factory=make_participants,
                map_factory=make_map,
                num_combats=num,
                turn_limit=200,
                strategy="balanced",
                time_of_day=self._time_of_day,
                surprise="none",
            )
            surprise_text = self.surprise_combo.currentText()
            if surprise_text == "Party Surprised":
                config.surprise = "surprised"
            elif surprise_text == "Party Ambushes":
                config.surprise = "ambush"

            self.simulate_button.setEnabled(False)
            self.batch_button.setEnabled(False)
            self.batch_button.setText("Running...")
            QApplication.processEvents()

            result = BatchRunner.run(config, progress_callback=lambda i, n: None)

            # Display results
            summary_lines = result.summary().split("\n")
            action_lines = ["Batch Simulation Complete", ""] + summary_lines
            self._set_action_log(action_lines)
            self.map_view.setPlainText(result.summary())
            self._show_toast(f"Batch done: {num} combats in {result.elapsed_seconds:.1f}s", "info")

            # Show chart dialog
            dlg = BatchChartDialog(result, parent=self)
            dlg.exec()
        except Exception as exc:
            QMessageBox.critical(self, "Batch failed", f"An error occurred during batch simulation:\n{exc}")
        finally:
            self.simulate_button.setEnabled(True)
            self.batch_button.setEnabled(True)
            self.batch_button.setText("Run Batch Simulation")

    def _compare_loadouts(self) -> None:
        """Run two batch simulations side-by-side: current setup (A) vs a variant (B).

        The user picks which combatant to modify and selects an alternate
        weapon.  Both batches run with the same number of combats and the
        results are shown in a comparison dialog with grouped bar charts.
        """
        from PySide6.QtWidgets import QInputDialog

        # Ask for number of combats
        num, ok = QInputDialog.getInt(
            self, "Compare Loadouts", "Number of combats per loadout:", 100, 10, 10000, 50)
        if not ok:
            return

        # Ask which combatant to modify
        names = [ed.name_input.text() or f"Character {i+1}" for i, ed in enumerate(self.combatant_editors)]
        char_name, ok = QInputDialog.getItem(
            self, "Compare Loadouts", "Modify which combatant?", names, 0, False)
        if not ok:
            return
        char_idx = names.index(char_name)

        # Ask for the alternate weapon
        weapon_names = sorted(AVALORE_WEAPONS.keys())
        current_weapon = self.combatant_editors[char_idx].hand1_combo.currentText()
        alt_weapon, ok = QInputDialog.getItem(
            self, "Compare Loadouts",
            f"Alternate weapon for {char_name}\n(current: {current_weapon}):",
            weapon_names, weapon_names.index(current_weapon) if current_weapon in weapon_names else 0, False)
        if not ok or alt_weapon == current_weapon:
            self._show_toast("Same weapon selected — nothing to compare.", "warning")
            return

        try:
            templates = [ed.to_template() for ed in self.combatant_editors]
            team_assignments = [ed.team_choice.currentText() for ed in self.combatant_editors]

            def _make_factory(tmpl_list):
                def factory():
                    parts = []
                    for i, tmpl in enumerate(tmpl_list):
                        ed = CombatantEditor(f"Character {i + 1}")
                        ed.load_template(tmpl)
                        p = ed.to_participant()
                        team_text = team_assignments[i]
                        p.team = "" if team_text == "FFA" else team_text
                        parts.append(p)
                        ed.deleteLater()
                    return parts
                return factory

            def make_map(participants):
                return self._build_tactical_map(participants)

            surprise_text = self.surprise_combo.currentText()
            surprise_val = "none"
            if surprise_text == "Party Surprised":
                surprise_val = "surprised"
            elif surprise_text == "Party Ambushes":
                surprise_val = "ambush"

            # --- Run A (current setup) ---
            config_a = BatchConfig(
                participants_factory=_make_factory(templates),
                map_factory=make_map,
                num_combats=num,
                turn_limit=200,
                strategy="balanced",
                time_of_day=self._time_of_day,
                surprise=surprise_val,
            )
            self.simulate_button.setEnabled(False)
            self.batch_button.setEnabled(False)
            self.compare_button.setEnabled(False)
            self.compare_button.setText("Running A...")
            QApplication.processEvents()
            result_a = BatchRunner.run(config_a)

            # --- Build variant B templates ---
            templates_b = [copy.deepcopy(t) for t in templates]
            templates_b[char_idx]["hand1"] = alt_weapon

            config_b = BatchConfig(
                participants_factory=_make_factory(templates_b),
                map_factory=make_map,
                num_combats=num,
                turn_limit=200,
                strategy="balanced",
                time_of_day=self._time_of_day,
                surprise=surprise_val,
            )
            self.compare_button.setText("Running B...")
            QApplication.processEvents()
            result_b = BatchRunner.run(config_b)

            label_a = f"{char_name} w/ {current_weapon}"
            label_b = f"{char_name} w/ {alt_weapon}"

            dlg = LoadoutComparisonDialog(result_a, result_b, label_a, label_b, parent=self)
            dlg.exec()

            self._show_toast(
                f"Comparison: {num} combats × 2 loadouts in "
                f"{result_a.elapsed_seconds + result_b.elapsed_seconds:.1f}s", "info")
        except Exception as exc:
            QMessageBox.critical(self, "Compare failed",
                                 f"An error occurred during comparison:\n{exc}")
        finally:
            self.simulate_button.setEnabled(True)
            self.batch_button.setEnabled(True)
            self.compare_button.setEnabled(True)
            self.compare_button.setText("Compare Loadouts")

    def move_attacker(self):
        try:
            participants = [ed.to_participant() for ed in self.combatant_editors]
            tactical_map = self._build_tactical_map(participants)
            engine = AvaCombatEngine(participants, tactical_map=tactical_map)
            self._last_engine = engine
            engine.log = lambda msg: engine.combat_log.append(msg)  # type: ignore
            attacker = participants[0]
            success = engine.action_move(attacker, int(self.move_x.value()), int(self.move_y.value()))
            if not success:
                engine.combat_log.append("Move failed.")
                self._show_toast("Move failed.", "warning")
            engine._log_map_state("After move")
            engine.combat_log.append(engine.get_combat_summary())
            self._set_action_log(engine.combat_log)
            self.map_view.setPlainText("\n".join(engine.map_log))
            self.status_view.setHtml(self._format_status_badges(participants))
            self._update_combat_bars(participants)
            self._render_map_grid(engine.tactical_map)
            self._set_decision_log()
            self._save_settings()
        except Exception as exc:
            QMessageBox.critical(self, "Move failed", f"An error occurred while moving:\n{exc}")

    def cast_spell(self):
        # Spell casting disabled in this UI for now.
        self.action_view.setPlainText("Spell casting is currently disabled.")

    def _on_mode_changed(self):
        # Enable controls for any player-controlled mode
        player_mode = "Player controls" in self.mode_combo.currentText()
        self._set_player_controls_enabled(player_mode)

    def _on_theme_changed(self):
        theme_str = self.theme_combo.currentText().lower()
        theme = Theme.DARK if theme_str == "dark" else Theme.LIGHT
        self.theme_manager.set_theme(theme)
        self._apply_theme()

    def _on_time_changed(self):
        self._time_of_day = self.time_combo.currentText().lower()

    def _on_surprise_changed(self):
        # Map selection to engine flags later during simulation run
        pass

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

    def _apply_theme(self):
        """Apply the current theme's stylesheet to the entire window."""
        stylesheet = self.theme_manager.generate_stylesheet()
        self.setStyleSheet(stylesheet)
        
        # Apply monospace fonts to text displays
        mono_font = FontConfig.get_font("monospace", 11)
        map_font = FontConfig.get_font("monospace", 12)
        
        self.action_view.setFont(mono_font)
        self.status_view.setFont(mono_font)
        self.map_view.setFont(map_font)
        if hasattr(self, "decision_view"):
            self.decision_view.setFont(mono_font)

        # Update tactical map colors to match theme
        if hasattr(self, "tactical_map_widget"):
            is_dark = self.theme_manager.current_theme == Theme.DARK
            if is_dark:
                self.tactical_map_widget.set_theme_colors("#2d2d2d", "#555555")
            else:
                self.tactical_map_widget.set_theme_colors("#f0ede6", "#999999")

        # Update theme toggle button icon
        if hasattr(self, "theme_toggle_btn"):
            is_dark = self.theme_manager.current_theme == Theme.DARK
            icon_name = "moon" if is_dark else "sun"
            self.theme_toggle_btn.setIcon(IconProvider.get_icon(icon_name))

    def _render_initiative(self, engine: AvaCombatEngine) -> None:
        if not engine.turn_order:
            self.initiative_label.setText("(no initiative)")
            return
        names = [p.character.name for p in engine.turn_order]
        round_info = f"Round {engine.round}" if engine.round else ""
        self.initiative_label.setText(f"{round_info} | Order: " + " → ".join(names))

    def _set_replay_data(self, snapshots: list[dict]) -> None:
        self.replay_snapshots = snapshots or []
        count = len(self.replay_snapshots)
        self.replay_slider.blockSignals(True)
        self.replay_slider.setMaximum(max(0, count - 1))
        self.replay_slider.setValue(max(0, count - 1))
        self.replay_slider.blockSignals(False)
        self.replay_index = max(0, count - 1)
        self.replay_play.setText("Play")
        if count:
            self._render_visual_map(self.replay_snapshots[self.replay_index])
        else:
            self._render_visual_map(None)

    def _on_replay_slider(self, value: int) -> None:
        if 0 <= value < len(self.replay_snapshots):
            self.replay_index = value
            self._render_visual_map(self.replay_snapshots[self.replay_index])

    def _step_replay(self, delta: int) -> None:
        if not self.replay_snapshots:
            return
        new_idx = min(len(self.replay_snapshots) - 1, max(0, self.replay_index + delta))
        self.replay_slider.setValue(new_idx)

    def _toggle_replay(self) -> None:
        if not self.replay_snapshots:
            return
        if self.replay_timer.isActive():
            self.replay_timer.stop()
            self.replay_play.setText("Play")
        else:
            self.replay_play.setText("Pause")
            self.replay_timer.start()

    def _advance_replay(self) -> None:
        if not self.replay_snapshots:
            self.replay_timer.stop()
            self.replay_play.setText("Play")
            return
        next_idx = self.replay_index + 1
        if next_idx >= len(self.replay_snapshots):
            self.replay_timer.stop()
            self.replay_play.setText("Play")
            return
        self.replay_slider.setValue(next_idx)

    def _save_template(self, editor: CombatantEditor) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Save Character Template", "character.json", "JSON Files (*.json)")
        if not path:
            return
        try:
            data = editor.to_template()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as exc:
            QMessageBox.critical(self, "Save failed", f"Could not save template:\n{exc}")

    def _load_template(self, editor: CombatantEditor) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Load Character Template", "", "JSON Files (*.json)")
        if not path:
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            editor.load_template(data)
        except Exception as exc:
            QMessageBox.critical(self, "Load failed", f"Could not load template:\n{exc}")

    def _format_status_badges(self, participants: list[CombatParticipant]) -> str:
        chips: list[str] = []
        status_icons = {
            "Prone": "PRN",
            "Slowed": "SLO",
            "Disarmed": "DIS",
            "Marked": "MRK",
            "Vulnerable": "VUL",
            "Hidden": "HID",
        }
        for p in participants:
            if not p:
                continue
            name = html.escape(p.character.name or "?")
            arch = ", ".join(sorted(getattr(p.character, "archetypes", []))) if hasattr(p, "character") else ""
            hp = f"HP {p.current_hp}/{p.max_hp}"
            hp_pct = int((p.current_hp / max(1, p.max_hp)) * 100)
            armor_label = p.armor.name if p.armor else "No Armor"
            armor_rating = 0
            if p.armor:
                if p.armor.category.name == "LIGHT":
                    armor_rating = 1
                elif p.armor.category.name == "MEDIUM":
                    armor_rating = 2
                elif p.armor.category.name == "HEAVY":
                    armor_rating = 3
            armor_pct = int((armor_rating / 3) * 100) if armor_rating else 0

            # -- Weapon and shield labels --
            weapon_label = p.weapon_main.name if p.weapon_main else "Unarmed"
            offhand_label = ""
            if p.weapon_offhand:
                offhand_label = f" / {p.weapon_offhand.name}"
            elif p.shield:
                offhand_label = f" / {p.shield.name}"

            # -- Anima bar --
            anima_pct = int((p.anima / max(1, p.max_anima)) * 100) if p.max_anima else 0
            anima_label = f"Anima {p.anima}/{p.max_anima}" if p.max_anima else ""

            # -- Status chips --
            statuses = []
            if p.is_blocking:
                statuses.append(("🛡 Blocking", "#264653"))
            if p.is_evading:
                statuses.append(("⚡ Evading", "#2a9d8f"))
            if p.bastion_active:
                statuses.append(("🏰 Bastion", "#1d3557"))
            if p.flowing_stance:
                statuses.append(("🌊 Flowing", "#457b9d"))
            if p.inspired_scene:
                statuses.append(("✨ Inspired", "#e9c46a"))
            if p.is_critical:
                statuses.append(("💀 Critical", "#9d0208"))
            if getattr(p, "death_save_failures", 0) > 0:
                skulls = "💀" * p.death_save_failures
                statuses.append((f"{skulls} Death Saves: {p.death_save_failures}", "#6a040f"))
            for status in getattr(p, "status_effects", set()):
                label = status.name.title()
                icon = status_icons.get(label, "STS")
                statuses.append((f"{icon} {label}", "#e76f51"))
            if not statuses:
                statuses.append(("✓ Stable", "#6c757d"))

            status_html = " ".join([f"<span style='background:{color};color:white;padding:2px 6px;border-radius:8px;font-size:9pt;'>{label}</span>" for label, color in statuses])
            hp_bar = (
                f"<div style='height:6px;background:#eee;border-radius:4px;overflow:hidden;margin-top:4px;'>"
                f"<div style='width:{hp_pct}%;height:6px;background:#e63946;'></div></div>"
            )
            armor_bar = (
                f"<div style='height:6px;background:#eee;border-radius:4px;overflow:hidden;margin-top:3px;'>"
                f"<div style='width:{armor_pct}%;height:6px;background:#457b9d;'></div></div>"
            )
            anima_bar_html = ""
            if p.max_anima:
                anima_bar_html = (
                    f"<div style='color:#666;font-size:9pt;margin-top:2px;'>{anima_label}</div>"
                    f"<div style='height:6px;background:#eee;border-radius:4px;overflow:hidden;margin-top:2px;'>"
                    f"<div style='width:{anima_pct}%;height:6px;background:#7b2cbf;'></div></div>"
                )
            equip_html = (
                f"<div style='color:#555;font-size:9pt;margin-top:2px;'>⚔ {html.escape(weapon_label)}{html.escape(offhand_label)}"
                f" &nbsp;|&nbsp; 🛡 {html.escape(armor_label)}</div>"
            )
            chips.append(
                f"<div style='margin-bottom:10px;'><b>{name}</b> <span style='color:#888;'>[{arch}]</span> — "
                f"<span style='color:#555;'>{hp}</span><br/>"
                f"{status_html}"
                f"{equip_html}"
                f"{hp_bar}{armor_bar}{anima_bar_html}</div>"
            )
        return "".join(chips)

    def _update_combat_bars(self, participants: list[CombatParticipant]) -> None:
        if not hasattr(self, "attacker_hp_bar"):
            return
        from combat.enums import ArmorCategory

        def armor_score(p: CombatParticipant) -> int:
            if not p.armor:
                return 0
            if p.armor.category == ArmorCategory.LIGHT:
                return 1
            if p.armor.category == ArmorCategory.MEDIUM:
                return 2
            if p.armor.category == ArmorCategory.HEAVY:
                return 3
            return 0

        # Update first two bars (always present)
        if len(participants) >= 1:
            self.attacker_hp_bar.setMaximum(max(1, participants[0].max_hp))
            self.attacker_hp_bar.setValue(max(0, participants[0].current_hp))
            self.attacker_hp_bar.setFormat(f"{participants[0].character.name} HP: %v/%m")
            self.attacker_armor_bar.setValue(armor_score(participants[0]))
        if len(participants) >= 2:
            self.defender_hp_bar.setMaximum(max(1, participants[1].max_hp))
            self.defender_hp_bar.setValue(max(0, participants[1].current_hp))
            self.defender_hp_bar.setFormat(f"{participants[1].character.name} HP: %v/%m")
            self.defender_armor_bar.setValue(armor_score(participants[1]))

        # Update extra combatant bars (3+)
        extra_bars = getattr(self, "_extra_combat_bars", [])
        for bar_pair in extra_bars:
            bar_pair["hp"].setVisible(False)
            bar_pair["armor"].setVisible(False)
        for i in range(2, len(participants)):
            p = participants[i]
            if i - 2 < len(extra_bars):
                hp_bar = extra_bars[i - 2]["hp"]
                armor_bar = extra_bars[i - 2]["armor"]
            else:
                hp_bar = QProgressBar()
                hp_bar.setTextVisible(True)
                armor_bar = QProgressBar()
                armor_bar.setMaximum(3)
                armor_bar.setTextVisible(True)
                armor_bar.setFormat("Armor: %v/3")
                if hasattr(self, "_combat_bars_layout"):
                    self._combat_bars_layout.addWidget(hp_bar)
                    self._combat_bars_layout.addWidget(armor_bar)
                extra_bars.append({"hp": hp_bar, "armor": armor_bar})
            hp_bar.setMaximum(max(1, p.max_hp))
            hp_bar.setValue(max(0, p.current_hp))
            hp_bar.setFormat(f"{p.character.name} HP: %v/%m")
            hp_bar.setVisible(True)
            armor_bar.setValue(armor_score(p))
            armor_bar.setVisible(True)
        self._extra_combat_bars = extra_bars

    def _execute_player_turn(self, engine: AvaCombatEngine, current: CombatParticipant, target: CombatParticipant) -> None:
        actions = self._selected_player_actions()
        for action in actions:
            if current.current_hp <= 0 or current.actions_remaining <= 0 or target.current_hp <= 0:
                break
            dist = engine.tactical_map.manhattan_distance(*current.position, *target.position) if engine.tactical_map else "?"
            self._log_decision(engine, f"Decision: Player chose {action} (dist {dist})")
            if action == "Attack":
                weapon = current.weapon_main or AVALORE_WEAPONS["Unarmed"]
                if not engine.is_in_range(current, target, weapon):
                    engine.combat_log.append("Player attack out of range; action wasted.")
                    self._show_toast("Attack out of range.", "warning")
                    current.spend_actions(weapon.actions_required)
                    continue
                engine.perform_attack(current, target, weapon=weapon)
            elif action == "Evade":
                engine.action_evade(current)
            elif action == "Block":
                engine.action_block(current)


def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
