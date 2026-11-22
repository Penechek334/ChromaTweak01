"""Хранилище настроек и пресетов (JSON в каталоге пользователя).

Каталог:
    Windows : %APPDATA%/MonitorColorTuner
    Linux   : ~/.config/monitor_color_tuner
    macOS   : ~/Library/Application Support/MonitorColorTuner
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path


def app_dir() -> Path:
    if sys.platform == "win32":
        base = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
        d = base / "MonitorColorTuner"
    elif sys.platform == "darwin":
        d = Path.home() / "Library" / "Application Support" / "MonitorColorTuner"
    else:
        base = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
        d = base / "monitor_color_tuner"
    d.mkdir(parents=True, exist_ok=True)
    return d


SETTINGS_FILE = app_dir() / "settings.json"
PRESETS_FILE = app_dir() / "presets.json"


def _load_json(path: Path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return default


def _save_json(path: Path, data) -> None:
    tmp = path.with_suffix(".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    tmp.replace(path)


# ---------------------------------------------------------------- settings --
def load_settings(defaults: dict) -> dict:
    """Объединяет сохранённые значения с значениями по умолчанию."""
    data = _load_json(SETTINGS_FILE, {})
    merged = dict(defaults)
    if isinstance(data, dict):
        for key in defaults:
            if key in data:
                try:
                    merged[key] = float(data[key])
                except (TypeError, ValueError):
                    pass
    return merged


def save_settings(values: dict) -> None:
    _save_json(SETTINGS_FILE, values)


# ----------------------------------------------------------------- presets --
def load_presets() -> dict:
    data = _load_json(PRESETS_FILE, {})
    return data if isinstance(data, dict) else {}


def save_preset(name: str, values: dict) -> None:
    presets = load_presets()
    presets[name] = dict(values)
    _save_json(PRESETS_FILE, presets)


def delete_preset(name: str) -> None:
    presets = load_presets()
    presets.pop(name, None)
    _save_json(PRESETS_FILE, presets)
