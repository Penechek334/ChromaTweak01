#!/usr/bin/env python3
"""Автозапуск ChromaTweak вместе с Windows.

Реализация через реестр HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\
CurrentVersion\\Run, параметр "ChromaTweak". Все публичные функции —
безопасные: при недоступном реестре печатают предупреждение в stderr
и возвращают False, наружу исключения не пробрасываются.

Используется в app/main_window.py:
    is_available() -> bool   — можно ли вообще управлять автозапуском
    is_enabled()   -> bool   — есть ли запись и указывает ли она на наш main.py
    enable()       -> bool   — прописать в реестр (True = успех)
    disable()      -> bool   — удалить из реестра (True = успех / уже не было)
"""
from __future__ import annotations

import os
import shutil
import sys

APP_NAME = "ChromaTweak"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


# ---------------------------------------------------------------- helpers --

def _winreg():
    """Вернуть модуль winreg или None, если мы не на Windows."""
    try:
        import winreg
        return winreg
    except ImportError:
        return None


def _pythonw() -> str:
    """Путь к pythonw.exe — без него при автозапуске мелькает консоль."""
    exe = sys.executable or ""
    if exe.lower().endswith("python.exe"):
        candidate = exe[: -len("python.exe")] + "pythonw.exe"
        if os.path.isfile(candidate):
            return candidate
    w = shutil.which("pythonw")
    return w or exe  # fallback — python.exe, лучше чем ничего


def _main_py() -> str:
    """Абсолютный путь к main.py (лежит на уровень выше пакета app/)."""
    here = os.path.dirname(os.path.abspath(__file__))  # .../app
    root = os.path.dirname(here)                        # .../ChromaTweak
    return os.path.join(root, "main.py")


def _launch_command() -> str:
    """Команда для реестра. Кавычки — из-за пробелов/кириллицы в пути."""
    return f'"{_pythonw()}" "{_main_py()}" --hidden'


# ------------------------------------------------------------------- API ---

def is_available() -> bool:
    """Доступен ли механизм автозапуска на этой системе."""
    return _winreg() is not None


def enable() -> bool:
    """Прописать ChromaTweak в HKCU\\...\\Run. True — успех."""
    w = _winreg()
    if w is None:
        print("autostart: winreg недоступен (не Windows?)", file=sys.stderr)
        return False
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, RUN_KEY, 0, w.KEY_SET_VALUE) as k:
            w.SetValueEx(k, APP_NAME, 0, w.REG_SZ, _launch_command())
        return True
    except (PermissionError, OSError) as e:
        print(f"autostart: не удалось включить — {e}", file=sys.stderr)
        return False


def disable() -> bool:
    """Удалить параметр ChromaTweak. True — успех (или уже не было)."""
    w = _winreg()
    if w is None:
        return False
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, RUN_KEY, 0, w.KEY_SET_VALUE) as k:
            w.DeleteValue(k, APP_NAME)
        return True
    except FileNotFoundError:
        # записи и так не было — считаем успехом
        return True
    except (PermissionError, OSError) as e:
        print(f"autostart: не удалось выключить — {e}", file=sys.stderr)
        return False


def is_enabled() -> bool:
    """Запись есть и указывает именно на наш main.py (а не на мусор)."""
    w = _winreg()
    if w is None:
        return False
    try:
        with w.OpenKey(w.HKEY_CURRENT_USER, RUN_KEY, 0, w.KEY_READ) as k:
            value, _ = w.QueryValueEx(k, APP_NAME)
        return _main_py().lower() in str(value).lower()
    except FileNotFoundError:
        return False
    except (PermissionError, OSError) as e:
        print(f"autostart: не удалось прочитать реестр — {e}", file=sys.stderr)
        return False