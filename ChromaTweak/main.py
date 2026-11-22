#!/usr/bin/env python3
"""Точка входа Monitor Color Tuner.

Запуск:
    python main.py            — обычный запуск
    python main.py --hidden   — старт, свёрнутым в трей (для автозагрузки)
"""
from __future__ import annotations

import sys


def main() -> int:
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtCore import Qt

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)

    app = QApplication(sys.argv)
    app.setApplicationName("Monitor Color Tuner")
    app.setOrganizationName("MCT")
    app.setQuitOnLastWindowClosed(False)  # трей живёт после закрытия окна

    from app.theme import qss, app_icon
    app.setStyleSheet(qss())
    app.setWindowIcon(app_icon())

    from app.main_window import MainWindow
    win = MainWindow()

    hidden = "--hidden" in sys.argv
    if hidden and win.tray is not None:
        # старт свёрнутым в трей — окно не показываем вовсе
        pass
    elif hidden:
        # трей недоступен — показываем окно, иначе приложение «исчезнет»
        win.show()
    else:
        win.show()

    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
