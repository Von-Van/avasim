#!/usr/bin/env python3
"""Render the AvaSim desktop app offscreen and capture README screenshots.

Drives the real PySide UI (no display needed) with a mage-vs-knight duel so
the spellbook, casting log, and tactical grid all show real content.

Usage::

    python scripts/capture_screenshots.py          # writes docs/screenshots/*.png
"""

from __future__ import annotations

import os
import sys
import threading
from pathlib import Path

# Hard watchdog: a headless Qt hang should kill the process, not the shell.
_watchdog = threading.Timer(120, lambda: (print("watchdog: timed out", file=sys.stderr), os._exit(2)))
_watchdog.daemon = True
_watchdog.start()

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

# Headless run: modal dialogs would block forever, so report and continue.
def _report_dialog(kind):
    def handler(parent, title, text, *args, **kwargs):
        print(f"[dialog suppressed] {kind}: {title}: {text}", file=sys.stderr)
        return QMessageBox.StandardButton.Ok
    return handler

QMessageBox.critical = staticmethod(_report_dialog("critical"))
QMessageBox.warning = staticmethod(_report_dialog("warning"))
QMessageBox.information = staticmethod(_report_dialog("information"))

import pyside_app  # noqa: E402

OUT_DIR = ROOT / "docs" / "screenshots"

MAGE = {
    "name": "Maelis the Ashbound",
    "hp": 20,
    "anima": 14,
    "max_anima": 14,
    "stats": {"Strength": 0, "Dexterity": 1, "Intelligence": 1, "Harmony": 2},
    "skills": {
        "Strength": {"Athletics": 0, "Fortitude": 1, "Forging": 1},
        "Dexterity": {"Acrobatics": 1, "Finesse": 1, "Stealth": 0},
        "Intelligence": {"Healing": 1, "Perception": 1, "Research": 0},
        "Harmony": {"Arcana": 2, "Nature": 0, "Belief": 1},
    },
    "hand1": "Arcane Wand",
    "hand2": "(None)",
    "armor": "Light Armor",
    "team": "Team A",
    "feats": ["Always Ready"],
    "spells": ["Pyrebolt", "Geokinesis", "Atmokinesis", "Barbs", "Seize"],
    "primary_discipline": "Tellurgy",
}

KNIGHT = {
    "name": "Ser Brandt",
    "hp": 20,
    "anima": 0,
    "max_anima": 0,
    "stats": {"Strength": 2, "Dexterity": 1, "Intelligence": 0, "Harmony": 0},
    "skills": {
        "Strength": {"Athletics": 2, "Fortitude": 2, "Forging": 0},
        "Dexterity": {"Acrobatics": 1, "Finesse": 1, "Stealth": 0},
        "Intelligence": {"Healing": 0, "Perception": 1, "Research": 0},
        "Harmony": {"Arcana": 0, "Nature": 0, "Belief": 1},
    },
    "hand1": "Arming Sword",
    "hand2": "Small Shield",
    "armor": "Medium Armor",
    "team": "Team B",
    "feats": ["Shield Bash", "Shieldmaster", "Second Wind"],
}


def settle(app: QApplication, rounds: int = 4) -> None:
    for _ in range(rounds):
        app.processEvents()


def grab(window, app: QApplication, name: str) -> None:
    settle(app)
    path = OUT_DIR / name
    window.grab().save(str(path))
    print(f"wrote {path.relative_to(ROOT)}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication(sys.argv)
    pyside_app.load_fantasy_fonts()
    print("building window...", flush=True)
    window = pyside_app.MainWindow()
    window.resize(1440, 920)
    window.show()
    settle(app)

    print("loading builds...", flush=True)
    window.attacker_editor.load_template(MAGE)
    window.defender_editor.load_template(KNIGHT)
    settle(app)

    # 1) Character setup with the feat picker and spellbook visible.
    window.main_tabs.setCurrentIndex(0)
    grab(window, app, "character-setup.png")

    # 2) Full AI-vs-AI run: action log with attacks, casts, and decision math.
    print("running simulation...", flush=True)
    window.mode_combo.setCurrentText("Full Auto (both AI)")
    window.show_math_check.setChecked(True)
    window.main_tabs.setCurrentIndex(1)
    settle(app)
    window.run_simulation()
    settle(app)
    print("simulation done", flush=True)
    window.log_tabs.setCurrentIndex(0)  # Action Log
    grab(window, app, "combat-log.png")

    # 3) Status tab: HP/anima bars and condition badges after the fight.
    window.log_tabs.setCurrentIndex(1)
    grab(window, app, "status-panel.png")


if __name__ == "__main__":
    main()
