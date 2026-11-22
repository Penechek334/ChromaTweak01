"""Кастомный слайдер в стиле скриншота: тонкий трек, цветная заливка,
круглая ручка с обводкой. Поддержка отрицательных значений (заливка от нуля)
или от левого края — зависит от параметра ``fill_from_center``.
"""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QSize, QRectF
from PyQt6.QtGui import QColor, QPainter, QMouseEvent
from PyQt6.QtWidgets import QAbstractSlider


class ColorSlider(QAbstractSlider):
    valueChangedFloat = pyqtSignal(float)

    def __init__(self, color: str, min_v: float, max_v: float,
                 default: float, step: float = 1.0,
                 fill_from_center: bool = True, parent=None):
        super().__init__(parent)
        self._color = QColor(color)
        self._track_color = QColor("#2a2a3e")
        self._min = min_v
        self._max = max_v
        self._step = step
        self._fill_center = fill_from_center
        # внутренняя координатная шкала int (для плавности — 100 дробных знаков)
        self._scale = 100.0
        self.setRange(int(min_v * self._scale), int(max_v * self._scale))
        self.setValue(int(default * self._scale))
        self.setOrientation(Qt.Orientation.Horizontal)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(22)
        self.valueChanged.connect(
            lambda v: self.valueChangedFloat.emit(v / self._scale))

    # ------------------------------------------------------------------ API --
    def value_f(self) -> float:
        return self.value() / self._scale

    def set_value_f(self, v: float):
        self.setValue(int(round(v * self._scale)))

    def sizeHint(self) -> QSize:
        return QSize(240, 22)

    # ------------------------------------------------------------- мышь --
    def mousePressEvent(self, e: QMouseEvent):
        if e.button() == Qt.MouseButton.LeftButton:
            self._move_to(e.position().x())
            self.setSliderDown(True)
            e.accept()

    def mouseMoveEvent(self, e: QMouseEvent):
        if self.isSliderDown():
            self._move_to(e.position().x())
            e.accept()

    def mouseReleaseEvent(self, e: QMouseEvent):
        if self.isSliderDown():
            self.setSliderDown(False)
            e.accept()

    def wheelEvent(self, e):
        dirn = 1 if e.angleDelta().y() > 0 else -1
        self.triggerAction(QAbstractSlider.SliderAction.SliderSingleStepAdd
                          if dirn > 0 else
                          QAbstractSlider.SliderAction.SliderSingleStepSub)
        e.accept()

    def _move_to(self, x: float):
        w = self.width()
        groove_w = w - self._handle_r() * 2
        t = max(0.0, min(1.0, (x - self._handle_r()) / max(groove_w, 1)))
        span = self.maximum() - self.minimum()
        self.setValue(self.minimum() + int(round(t * span)))

    # ------------------------------------------------------------ отрисовка --
    def _handle_r(self) -> float:
        return 7.5

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        r = self._handle_r()
        cy = h / 2.0
        x0, x1 = r, w - r
        track_h = 4.0

        # базовый трек
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._track_color)
        p.drawRoundedRect(QRectF(x0, cy - track_h / 2, x1 - x0, track_h),
                          track_h / 2, track_h / 2)

        # положение ручки
        span = self.maximum() - self.minimum() or 1
        t = (self.value() - self.minimum()) / span
        hx = x0 + t * (x1 - x0)

        # заливка
        if self._fill_center and self._min < 0 < self._max:
            zero_t = (0.0 - self._min) / (self._max - self._min)
            zx = x0 + zero_t * (x1 - x0)
            left, right = min(zx, hx), max(zx, hx)
        else:
            left, right = x0, hx
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self._color)
        p.drawRoundedRect(QRectF(left, cy - track_h / 2,
                                 max(right - left, track_h), track_h),
                          track_h / 2, track_h / 2)

        # ручка: тёмный круг + цветная обводка
        pen = p.pen()
        pen.setColor(self._color.lighter(115))
        pen.setWidthF(2.0)
        p.setPen(pen)
        p.setBrush(QColor("#12121a"))
        p.drawEllipse(QRectF(hx - r, cy - r, 2 * r, 2 * r))
        p.end()
