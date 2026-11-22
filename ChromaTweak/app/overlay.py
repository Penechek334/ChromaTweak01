"""Экранный фильтр-оверлей — fallback для Linux/macOS.

Полноэкранное кликс--through, неактивируемое окно:
 - чёрная/белая полупрозрачная подложка эмулирует яркость и экспозицию;
 - цветные слои с альфой аппроксимируют сдвиг оттенка;
 - контраст/гамма моделируются затемнением краёв кривой (приближённо).

На Windows этот модуль не используется (там SetDeviceGammaRamp).
"""
from __future__ import annotations

import math

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import QWidget


class ScreenOverlay(QWidget):
    def __init__(self):
        super().__init__(None, Qt.WindowType.FramelessWindowHint
                         | Qt.WindowType.Tool
                         | Qt.WindowType.WindowStaysOnTopHint
                         | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._params = {}
        self.hide()

    # ------------------------------------------------------------------ API --
    def apply(self, params: dict):
        """Показывает/обновляет оверлей под текущие параметры."""
        self._params = dict(params)
        if self._is_neutral(params):
            self.hide()
            return
        from PyQt6.QtWidgets import QApplication
        geo = QApplication.primaryScreen().virtualGeometry()
        self.setGeometry(geo)
        self.show()
        self.update()

    def reset(self):
        self.hide()

    @staticmethod
    def _is_neutral(p: dict) -> bool:
        keys = ("brightness", "contrast", "exposure", "hue_shift",
                "saturation", "vibrance")
        if abs(p.get("gamma", 1.0) - 1.0) < 1e-9 and all(
                abs(p.get(k, 0.0)) < 1e-9 for k in keys):
            return True
        return False

    # -------------------------------------------------------------- отрисовка --
    def paintEvent(self, event):
        p = self._params
        brightness = p.get("brightness", 0.0) / 100.0
        exposure = p.get("exposure", 0.0) / 100.0
        contrast = p.get("contrast", 0.0) / 100.0
        hue = p.get("hue_shift", 0.0)
        saturation = p.get("saturation", 0.0) / 100.0

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        rect = self.rect()

        # яркость/экспозиция: затемнение (-) или осветление (+) через белую вуаль
        lift = max(0.0, brightness + exposure * 0.5)
        shade = max(0.0, -(brightness + exposure * 0.5))
        # контраст: дополнительно приглушаем середину тёмным слоем
        if contrast < 0:
            shade += -contrast * 0.25

        if shade > 0:
            painter.fillRect(rect, QColor(0, 0, 0, int(min(shade, 1.0) * 180)))
        if lift > 0:
            painter.fillRect(rect, QColor(255, 255, 255, int(min(lift, 1.0) * 140)))

        # сдвиг оттенка: два цветных слоя с альфой (аддитивно-переходный)
        if abs(hue) > 0.5:
            hcol = QColor.fromHsvF((hue % 360) / 360.0, 0.75, 1.0)
            alpha = int(min(abs(hue) / 180.0, 1.0) * 60)
            painter.fillRect(rect, QColor(hcol.red(), hcol.green(),
                                          hcol.blue(), alpha))

        # насыщенность -: серый вуалирующий слой
        if saturation < -0.01:
            gray_alpha = int(min(-saturation, 1.0) * 120)
            painter.fillRect(rect, QColor(128, 128, 128, gray_alpha))

        painter.end()
