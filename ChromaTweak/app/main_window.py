"""Главное окно приложения «Monitor Color Tuner»."""
from __future__ import annotations

import sys

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (QApplication, QCheckBox, QDialog, QInputDialog,
                             QLabel, QLineEdit, QMainWindow, QMessageBox,
                             QPushButton, QVBoxLayout, QHBoxLayout, QWidget)

from . import autostart, settings as st
from .gamma_backend import create_backend, is_neutral
from .overlay import ScreenOverlay
from .theme import (GREEN, ORANGE, PURPLE, PINK, TEXT_DIM, app_icon, svg_icon)
from .tray import Tray
from .widgets.section import SectionCard
from .widgets.slider import ColorSlider

# ------------------------------------------------------------- параметры --
# key, название, иконка, цвет слайдера, min, max, default, формат значения
PARAMS = [
    # секция «ОСНОВНЫЕ»
    dict(section="basic", key="brightness",  name="Яркость",
         icon="brightness", color=GREEN,  min=-100, max=100, default=0.0,
         fmt=lambda v: f"{v:.2f}", center=True),
    dict(section="basic", key="contrast",   name="Контрастность",
         icon="contrast",   color=GREEN,  min=-100, max=100, default=0.0,
         fmt=lambda v: f"{v:.2f}", center=True),
    dict(section="basic", key="exposure",   name="Экспозиция",
         icon="exposure",   color=GREEN,  min=-100, max=100, default=0.0,
         fmt=lambda v: f"{v:.2f}", center=True),
    dict(section="basic", key="gamma",      name="Гамма",
         icon="gamma",      color=GREEN,  min=0.1, max=3.0, default=1.0,
         fmt=lambda v: f"{v:.2f}", center=False),
    dict(section="basic", key="hue_shift",  name="Сдвиг оттенка",
         icon="hue",        color=ORANGE, min=-180, max=180, default=0.0,
         fmt=lambda v: f"{v:.0f}\u00b0", center=True),
    # секция «ЦВЕТ»
    dict(section="color", key="saturation", name="Насыщенность",
         icon="saturation", color=PURPLE, min=-100, max=100, default=0.0,
         fmt=lambda v: f"{v:.2f}", center=True),
    dict(section="color", key="vibrance",   name="Сочность (Vibrance)",
         icon="vibrance",   color=PINK,   min=-100, max=100, default=0.0,
         fmt=lambda v: f"{v:.2f}", center=True),
]

DEFAULTS = {p["key"]: p["default"] for p in PARAMS}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Monitor Color Tuner")
        self.setWindowIcon(app_icon())
        self.setMinimumWidth(420)
        self.resize(430, 640)

        self.backend = create_backend()
        # на не-Windows используем экран-фильтр как основной метод
        self.use_overlay = not self.backend.is_supported()
        self.overlay = ScreenOverlay() if self.use_overlay else None

        self._quitting = False
        self._sliders: dict[str, ColorSlider] = {}
        self._rows = {}

        values = st.load_settings(DEFAULTS)
        self._build_ui(values)

        # debounce для плавного применения при быстром перетаскивании
        self._apply_timer = QTimer(self)
        self._apply_timer.setSingleShot(True)
        self._apply_timer.setInterval(16)  # ~60 fps
        self._apply_timer.timeout.connect(self._apply_now)

        self._setup_tray()

        # стартовое применение сохранённых значений
        self._schedule_apply()

        status = ("Режим: " + self.backend.name) if not self.use_overlay \
            else "Режим: экран-фильтр (оверлей)"
        self.status = QLabel(status)
        self.status.setStyleSheet(f"color:{TEXT_DIM}; font-size:11px;")
        self.bottom_layout.addWidget(self.status)

    # ------------------------------------------------------------------- UI --
    def _build_ui(self, values: dict):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 14)
        root.setSpacing(14)

        # заголовок окна
        head = QHBoxLayout()
        title = QLabel("НАСТРОЙКА ЦВЕТА МОНИТОРА")
        title.setStyleSheet("font-weight:700; letter-spacing:2px; font-size:12px;"
                            f"color:{TEXT_DIM};")
        head.addWidget(title)
        head.addStretch(1)
        root.addLayout(head)

        # --- секции ---
        self.sec_basic = SectionCard("Основные", "gear")
        self.sec_color = SectionCard("Цвет", "palette")
        for p in PARAMS:
            slider = ColorSlider(p["color"], p["min"], p["max"],
                                 values.get(p["key"], p["default"]),
                                 fill_from_center=p["center"])
            slider.set_value_f(values.get(p["key"], p["default"]))
            self._sliders[p["key"]] = slider
            card = self.sec_basic if p["section"] == "basic" else self.sec_color
            row = card.add_param(p["icon"], p["color"], p["name"],
                                 slider, p["fmt"])
            self._rows[p["key"]] = row
            slider.valueChangedFloat.connect(lambda _v: self._schedule_apply())

        self.sec_basic.resetClicked.connect(
            lambda: self._reset_section("basic"))
        self.sec_color.resetClicked.connect(
            lambda: self._reset_section("color"))

        root.addWidget(self.sec_basic)
        root.addWidget(self.sec_color)

        # --- нижняя панель управления ---
        self.bottom_layout = QVBoxLayout()
        self.bottom_layout.setSpacing(8)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        b_reset = QPushButton("Сбросить")
        b_reset.setObjectName("AccentBtn")
        b_reset.clicked.connect(self.reset_all)
        b_save = QPushButton("Сохранить пресет")
        b_save.setObjectName("BottomBtn")
        b_save.clicked.connect(self.save_preset_dialog)
        b_load = QPushButton("Пресеты")
        b_load.setObjectName("BottomBtn")
        b_load.clicked.connect(self.show_presets_menu)
        btns.addWidget(b_reset)
        btns.addWidget(b_save)
        btns.addWidget(b_load)
        self.bottom_layout.addLayout(btns)

        row2 = QHBoxLayout()
        self.chk_autostart = QCheckBox("Запускать вместе с Windows")
        self.chk_autostart.setEnabled(autostart.is_available())
        self.chk_autostart.setChecked(autostart.is_enabled())
        self.chk_autostart.toggled.connect(self._toggle_autostart)
        row2.addWidget(self.chk_autostart)
        row2.addStretch(1)
        b_hide = QPushButton("В трей")
        b_hide.setObjectName("BottomBtn")
        b_hide.clicked.connect(self.hide_to_tray)
        row2.addWidget(b_hide)
        self.bottom_layout.addLayout(row2)

        root.addLayout(self.bottom_layout)
        root.addStretch(1)

    # ------------------------------------------------------------ логика --
    def current_values(self) -> dict:
        return {k: s.value_f() for k, s in self._sliders.items()}

    def _schedule_apply(self):
        self._apply_timer.start()

    def _apply_now(self):
        vals = self.current_values()
        if self.overlay is not None:
            self.overlay.apply(vals)
        else:
            self.backend.apply(vals)
        st.save_settings(vals)

    def _set_values(self, values: dict):
        for key, slider in self._sliders.items():
            if key in values:
                slider.set_value_f(float(values[key]))
                self._rows[key].refresh()
        self._schedule_apply()

    def _reset_section(self, section: str):
        vals = self.current_values()
        for p in PARAMS:
            if p["section"] == section:
                vals[p["key"]] = p["default"]
        self._set_values(vals)

    def reset_all(self):
        self._set_values(dict(DEFAULTS))

    # ------------------------------------------------------------ пресеты --
    def save_preset_dialog(self):
        name, ok = QInputDialog.getText(
            self, "Сохранить пресет", "Название пресета:",
            QLineEdit.EchoMode.Normal)
        if ok and name.strip():
            st.save_preset(name.strip(), self.current_values())
            self.status.setText(f"Пресет «{name.strip()}» сохранён")

    def show_presets_menu(self):
        from PyQt6.QtWidgets import QMenu
        presets = st.load_presets()
        menu = QMenu(self)
        if not presets:
            act = menu.addAction("Нет сохранённых пресетов")
            act.setEnabled(False)
        else:
            for name in sorted(presets):
                act = menu.addAction(name)
                act.triggered.connect(
                    lambda _c=False, n=name: self._load_preset(n))
            menu.addSeparator()
            act_del = menu.addAction("Удалить пресет…")
            act_del.triggered.connect(self._delete_preset_dialog)
        menu.exec(self._menu_pos())

    def _menu_pos(self):
        from PyQt6.QtGui import QCursor
        return QCursor.pos()

    def _load_preset(self, name: str):
        presets = st.load_presets()
        if name in presets:
            self._set_values(presets[name])
            self.status.setText(f"Загружен пресет «{name}»")

    def _delete_preset_dialog(self):
        presets = sorted(st.load_presets())
        if not presets:
            return
        name, ok = QInputDialog.getItem(self, "Удалить пресет",
                                        "Пресет:", presets, 0, False)
        if ok and name:
            st.delete_preset(name)

    # ------------------------------------------------------- автозапуск --
    def _toggle_autostart(self, checked: bool):
        if checked:
            if not autostart.enable():
                QMessageBox.warning(self, "Автозагрузка",
                                    "Не удалось добавить запись в реестр.")
                self.chk_autostart.blockSignals(True)
                self.chk_autostart.setChecked(False)
                self.chk_autostart.blockSignals(False)
        else:
            autostart.disable()

    # -------------------------------------------------------------- трей --
    def _setup_tray(self):
        self.tray = Tray(self, on_show=self.show_from_tray,
                         on_quit=self.quit_app, icon=app_icon())
        if Tray.isSystemTrayAvailable():
            self.tray.show()
        else:
            self.tray = None

    def hide_to_tray(self):
        if self.tray is not None:
            self.hide()
            self.tray.showMessage("Monitor Color Tuner",
                                  "Приложение свёрнуто в трей.\n"
                                  "Коррекция цвета продолжает работать.",
                                  self.tray.icon(), 3000)
        else:
            self.hide()

    def show_from_tray(self):
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def closeEvent(self, event):
        if self._quitting:
            event.accept()
            return
        # крестик — сворачиваем в трей вместо закрытия
        event.ignore()
        self.hide_to_tray()

    def quit_app(self):
        self._quitting = True
        try:
            self.backend.reset()
        except Exception:
            pass
        if self.overlay is not None:
            self.overlay.reset()
        st.save_settings(self.current_values())
        if self.tray is not None:
            self.tray.hide()
        QApplication.instance().quit()
