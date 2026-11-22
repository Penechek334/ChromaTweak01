"""Карточка-секция (ОСНОВНЫЕ / ЦВЕТ): заголовок с иконкой, кнопками
сброса (↻) и сворачивания (^), список параметров с ползунками."""
from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal, QPropertyAnimation, QEasingCurve
from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton,
                             QVBoxLayout, QWidget, QGraphicsDropShadowEffect)

from ..theme import GREEN, TEXT, svg_icon


class ParamRow(QWidget):
    """Строка параметра: иконка + название слева, значение справа, слайдер снизу."""

    def __init__(self, icon_name: str, icon_color: str, label: str,
                 slider, fmt, parent=None):
        super().__init__(parent)
        self.slider = slider
        self.fmt = fmt

        root = QVBoxLayout(self)
        root.setContentsMargins(0, 4, 0, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.setSpacing(8)
        ic = QLabel()
        ic.setFixedSize(20, 20)
        ic.setPixmap(svg_icon(icon_name, icon_color, 18).pixmap(18, 18))
        name = QLabel(label)
        name.setObjectName("ParamName")
        self.value_label = QLabel(fmt(slider.value_f()))
        self.value_label.setObjectName("ParamValue")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignRight
                                      | Qt.AlignmentFlag.AlignVCenter)
        self.value_label.setMinimumWidth(64)
        top.addWidget(ic)
        top.addWidget(name)
        top.addStretch(1)
        top.addWidget(self.value_label)
        root.addLayout(top)
        root.addWidget(slider)

        slider.valueChangedFloat.connect(self._update_value)

    def _update_value(self, v: float):
        self.value_label.setText(self.fmt(v))

    def refresh(self):
        self._update_value(self.slider.value_f())


class SectionCard(QFrame):
    """Закруглённая карточка секции со сворачиваемым содержимым."""

    resetClicked = pyqtSignal()
    changed = pyqtSignal()

    def __init__(self, title: str, icon_name: str, parent=None):
        super().__init__(parent)
        self.setObjectName("Card")
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 110))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 14, 18, 12)
        outer.setSpacing(0)

        # ---- заголовок ----
        header = QWidget()
        hl = QHBoxLayout(header)
        hl.setContentsMargins(0, 0, 0, 0)
        hl.setSpacing(9)

        hicon = QLabel()
        hicon.setFixedSize(22, 22)
        hicon.setPixmap(svg_icon(icon_name, GREEN, 19).pixmap(19, 19))

        title_lbl = QLabel(title.upper())
        title_lbl.setObjectName("SectionTitle")

        self.btn_reset = QPushButton()
        self.btn_reset.setObjectName("IconBtn")
        self.btn_reset.setFixedSize(24, 24)
        self.btn_reset.setIcon(svg_icon("reset", TEXT, 14))
        self.btn_reset.setIconSize(self.btn_reset.icon().pixmap(14, 14).size())
        self.btn_reset.setToolTip("Сбросить параметры секции")
        self.btn_reset.clicked.connect(self.resetClicked.emit)

        self.btn_collapse = QPushButton()
        self.btn_collapse.setObjectName("IconBtn")
        self.btn_collapse.setFixedSize(24, 24)
        self._collapsed = False
        self.btn_collapse.clicked.connect(self.toggle_collapsed)

        hl.addWidget(hicon)
        hl.addWidget(title_lbl)
        hl.addStretch(1)
        hl.addWidget(self.btn_reset)
        hl.addWidget(self.btn_collapse)
        outer.addWidget(header)
        outer.addSpacing(8)

        # ---- содержимое (анимированная высота) ----
        self.body = QWidget()
        self.body_layout = QVBoxLayout(self.body)
        self.body_layout.setContentsMargins(0, 0, 0, 0)
        self.body_layout.setSpacing(2)
        outer.addWidget(self.body)

        self._anim = QPropertyAnimation(self.body, b"maximumHeight", self)
        self._anim.setDuration(180)
        self._anim.setEasingCurve(QEasingCurve.Type.InOutCubic)
        self._set_collapse_icon()

    # ------------------------------------------------------------------ API --
    def add_param(self, icon: str, color: str, label: str,
                  slider, fmt) -> ParamRow:
        row = ParamRow(icon, color, label, slider, fmt, self.body)
        self.body_layout.addWidget(row)
        slider.valueChangedFloat.connect(lambda _v: self.changed.emit())
        return row

    def toggle_collapsed(self):
        self._collapsed = not self._collapsed
        self._set_collapse_icon()
        if self._collapsed:
            self._anim.stop()
            self._anim.setStartValue(self.body.height())
            self._anim.setEndValue(0)
        else:
            self._anim.stop()
            self._anim.setStartValue(self.body.maximumHeight())
            self._anim.setEndValue(self._preferred_height())
        self._anim.start()

    def _preferred_height(self) -> int:
        return max(self.body.sizeHint().height(), 1)

    def _set_collapse_icon(self):
        # ^ когда развёрнуто, v когда свёрнуто
        rot = 180 if self._collapsed else 0
        renderer = QSvgRenderer(
            ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">'
             '<g transform="rotate(%d 12 12)">%s</g></svg>'
             % (rot, _CHEVRON_BODY)).encode("utf-8"))
        pm = QPixmap(14, 14)
        pm.fill(QColor(0, 0, 0, 0))
        p = QPainter(pm)
        renderer.render(p)
        p.end()
        self.btn_collapse.setIcon(QIcon(pm))
        self.btn_collapse.setIconSize(pm.size())
        self.btn_collapse.setToolTip(
            "Развернуть секцию" if self._collapsed else "Свернуть секцию")

    # после анимации разворота фиксируем максимальную высоту
    def showEvent(self, e):
        super().showEvent(e)
        self.body.setMaximumHeight(self._preferred_height())


_CHEVRON_BODY = ('<path d="M6 14l6-6 6 6" fill="none" stroke="#d8d8e4" '
                 'stroke-width="2.2" stroke-linecap="round" '
                 'stroke-linejoin="round"/>')
