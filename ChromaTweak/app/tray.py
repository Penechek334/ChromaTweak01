"""Системный трей: иконка, контекстное меню, скрытие окна в трей."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon


class Tray(QSystemTrayIcon):
    def __init__(self, window, on_show, on_quit, icon: QIcon | None = None):
        super().__init__(icon or window.windowIcon(), window)
        self._window = window
        self._on_show = on_show
        self._on_quit = on_quit

        menu = QMenu()
        act_show = QAction("Показать окно", menu)
        act_show.triggered.connect(self._show)
        menu.addAction(act_show)

        act_reset = QAction("Сбросить все настройки", menu)
        act_reset.triggered.connect(lambda: getattr(window, "reset_all")())
        menu.addAction(act_reset)
        menu.addSeparator()

        act_quit = QAction("Выход", menu)
        act_quit.triggered.connect(self._quit)
        menu.addAction(act_quit)

        self.setContextMenu(menu)
        self.activated.connect(self._activated)
        self.messageClicked.connect(self._show)

    def _activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # одинарный клик — показать/скрыть
            if self._window.isVisible():
                self._window.hide()
            else:
                self._show()

    def _show(self):
        self._on_show()

    def _quit(self):
        self._on_quit()
