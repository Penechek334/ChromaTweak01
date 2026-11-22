"""Тёмная тема приложения: палитра, QSS и генерация SVG-иконок."""
from __future__ import annotations

from PyQt6.QtGui import QColor, QIcon, QPainter, QPixmap
from PyQt6.QtSvg import QSvgRenderer  # входит в PyQt6 (Qt6 Svg)

# ------------------------------------------------------------------- палитра --
BG          = "#16161e"   # фон окна
CARD        = "#1d1d2b"   # карточки секций
CARD_BORDER = "#262637"
TRACK       = "#2a2a3e"   # трек ползунка
HANDLE_BG   = "#12121a"
TEXT        = "#d8d8e4"
TEXT_DIM    = "#8a8aa0"
GREEN       = "#a8d86e"   # ОСНОВНЫЕ + иконки
ORANGE      = "#f0a050"   # сдвиг оттенка
PURPLE      = "#b070e0"   # насыщенность
PINK        = "#f050a0"   # сочность
ACCENT      = GREEN

FONT_STACK = '"Segoe UI", "Inter", "Roboto", "Helvetica Neue", Arial, sans-serif'


def qss() -> str:
    return f"""
    QWidget {{
        background-color: {BG};
        color: {TEXT};
        font-family: {FONT_STACK};
        font-size: 13px;
    }}
    QMainWindow, QDialog {{ background-color: {BG}; }}

    /* ---------- карточки секций ---------- */
    QFrame#Card {{
        background-color: {CARD};
        border: 1px solid {CARD_BORDER};
        border-radius: 14px;
    }}
    QLabel#SectionTitle {{
        color: {TEXT};
        font-size: 13px;
        font-weight: 700;
        letter-spacing: 2px;
    }}
    QLabel#ParamName {{ color: {TEXT}; font-size: 13px; }}
    QLabel#ParamValue {{
        color: {TEXT}; font-size: 13px; font-weight: 600;
        font-variant-numeric: tabular-nums;
    }}

    /* ---------- круглые кнопки-иконки (сброс / свернуть) ---------- */
    QPushButton#IconBtn {{
        background-color: transparent;
        border: 1px solid {CARD_BORDER};
        border-radius: 11px;
        padding: 2px;
    }}
    QPushButton#IconBtn:hover {{ background-color: #26263a; }}
    QPushButton#IconBtn:pressed {{ background-color: #2e2e46; }}

    /* ---------- нижние кнопки ---------- */
    QPushButton#BottomBtn {{
        background-color: {CARD};
        color: {TEXT};
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 9px 14px;
        font-weight: 600;
    }}
    QPushButton#BottomBtn:hover {{ background-color: #26263a; }}
    QPushButton#BottomBtn:pressed {{ background-color: #2c2c44; }}
    QPushButton#AccentBtn {{
        background-color: {GREEN};
        color: #16330a;
        border: none;
        border-radius: 10px;
        padding: 9px 16px;
        font-weight: 700;
    }}
    QPushButton#AccentBtn:hover {{ background-color: #b8e482; }}
    QPushButton#AccentBtn:pressed {{ background-color: #99cc5e; }}

    /* ---------- чекбокс ---------- */
    QCheckBox {{ color: {TEXT_DIM}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 16px; height: 16px; border-radius: 5px;
        border: 1px solid {CARD_BORDER}; background: {HANDLE_BG};
    }}
    QCheckBox::indicator:checked {{
        background: {GREEN}; border-color: {GREEN};
    }}

    /* ---------- меню / диалоги ---------- */
    QMenu {{
        background-color: {CARD};
        border: 1px solid {CARD_BORDER};
        border-radius: 10px;
        padding: 6px;
    }}
    QMenu::item {{
        padding: 6px 22px 6px 14px;
        border-radius: 7px;
        color: {TEXT};
    }}
    QMenu::item:selected {{ background-color: #2b2b42; }}
    QMenu::separator {{ height: 1px; background: {CARD_BORDER}; margin: 5px 8px; }}

    QLineEdit {{
        background-color: {HANDLE_BG};
        border: 1px solid {CARD_BORDER};
        border-radius: 8px;
        padding: 7px 10px;
        color: {TEXT};
        selection-background-color: {GREEN};
        selection-color: #16330a;
    }}
    QMessageBox, QDialog {{ background-color: {BG}; }}
    QToolTip {{
        background-color: {CARD}; color: {TEXT};
        border: 1px solid {CARD_BORDER}; border-radius: 6px;
    }}
    """


# -------------------------------------------------------------------- иконки --
_SVG_TMPL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" '
             'width="24" height="24">{body}</svg>')

_PATHS = {
    # шестерёнка (fill)
    "gear": ('<path fill="{c}" d="M19.14 12.94a7.07 7.07 0 0 0 .05-1.88l2.03-1.58a.5.5 0 0 0'
             ' .12-.64l-1.92-3.32a.5.5 0 0 0-.61-.22l-2.39.96a7.03 7.03 0 0 0-1.62-.94l-.36-2.54'
             '.5a.5.5 0 0 0-.42-.42L10.5 1.08a.5.5 0 0 0-.6.36l-.36 2.54c-.56.24-1.09.55-1.58.92'
             'l-2.33-1.0a.5.5 0 0 0-.62.21L2.73 7.4a.5.5 0 0 0 .15.63l1.9 1.55a7.1 7.1 0 0 0 0 '
             '1.85l-1.9 1.55a.5.5 0 0 0-.15.63l2.28 3.32a.5.5 0 0 0 .62.21l2.33-1c.49.37 1.02.68 '
             '1.58.92l.36 2.54a.5.5 0 0 0 .6.36l3.52-1.29a.5.5 0 0 0 .42-.42l.36-2.54c.57-.24 '
             '1.12-.56 1.62-.94l2.39.96a.5.5 0 0 0 .61-.22l1.92-3.32a.5.5 0 0 0-.12-.64zM12 '
             '15.5A3.5 3.5 0 1 1 12 8.5a3.5 3.5 0 0 1 0 7z"/>'),
    # палитра художника
    "palette": ('<path fill="{c}" d="M12 3a9 9 0 0 0 0 18c1.1 0 2-.9 2-2 0-.5-.2-1-.5-1.3-.3-.4-.5-.8'
                '-.5-1.2 0-1.1.9-2 2-2h2.4A4.6 4.6 0 0 0 21 9c0-3.3-4-6-9-6zm-5.5 9a1.5 1.5 0 1 1 '
                '0-3 1.5 1.5 0 0 1 0 3zm3-4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3zm5 0a1.5 1.5 0 1 1 '
                '0-3 1.5 1.5 0 0 1 0 3zm3 4a1.5 1.5 0 1 1 0-3 1.5 1.5 0 0 1 0 3z"/>'),
    # солнце — яркость
    "brightness": ('<circle cx="12" cy="12" r="4" fill="{c}"/>'
                   '<g stroke="{c}" stroke-width="1.8" stroke-linecap="round">'
                   '<line x1="12" y1="2.5" x2="12" y2="5"/><line x1="12" y1="19" x2="12" y2="21.5"/>'
                   '<line x1="2.5" y1="12" x2="5" y2="12"/><line x1="19" y1="12" x2="21.5" y2="12"/>'
                   '<line x1="5.3" y1="5.3" x2="7" y2="7"/><line x1="17" y1="17" x2="18.7" y2="18.7"/>'
                   '<line x1="5.3" y1="18.7" x2="7" y2="17"/><line x1="17" y1="7" x2="18.7" y2="5.3"/></g>'),
    # контраст — полукруг
    "contrast": ('<circle cx="12" cy="12" r="9" fill="none" stroke="{c}" stroke-width="1.8"/>'
                 '<path fill="{c}" d="M12 3a9 9 0 0 1 0 18z"/>'),
    # экспозиция — «E» в круге / шкала
    "exposure": ('<rect x="3" y="3" width="18" height="18" rx="4" fill="none" stroke="{c}" stroke-width="1.8"/>'
                 '<text x="12" y="16.2" font-size="10.5" font-family="Arial" font-weight="bold" '
                 'fill="{c}" text-anchor="middle">±</text>'),
    # гамма — кривая
    "gamma": ('<path d="M4 19 C 10 19, 10 5, 20 5" fill="none" stroke="{c}" '
              'stroke-width="2" stroke-linecap="round"/>'
              '<circle cx="4" cy="19" r="1.6" fill="{c}"/><circle cx="20" cy="5" r="1.6" fill="{c}"/>'),
    # оттенок — круговая радужная стрелка
    "hue": ('<path d="M12 4a8 8 0 1 1-7.6 5.5" fill="none" stroke="{c}" stroke-width="2" '
            'stroke-linecap="round"/><path d="M2 5.5 L4.4 9.9 L8.6 8.3 Z" fill="{c}"/>'),
    # насыщенность — капля
    "saturation": ('<path fill="{c}" d="M12 3s6 6.3 6 10.2A6 6 0 0 1 6 13.2C6 9.3 12 3 12 3z"/>'),
    # сочность — искра
    "vibrance": ('<path fill="{c}" d="M12 2l1.9 6.1L20 10l-6.1 1.9L12 18l-1.9-6.1L4 10l6.1-1.9z"/>'
                 '<circle cx="18.5" cy="17.5" r="1.8" fill="{c}"/>'),
    # сброс ↻
    "reset": ('<path d="M12 5a7 7 0 1 1-6.3 4" fill="none" stroke="{c}" stroke-width="2" '
              'stroke-linecap="round"/><path d="M3.5 3.5 L5.7 9 L11 6.8 Z" fill="{c}"/>'),
    # шеврон ^
    "chevron": ('<path d="M6 14l6-6 6 6" fill="none" stroke="{c}" stroke-width="2.2" '
                'stroke-linecap="round" stroke-linejoin="round"/>'),
}


def svg_icon(name: str, color: str = TEXT, size: int = 18) -> QIcon:
    body = _PATHS[name].format(c=color)
    renderer = QSvgRenderer(_SVG_TMPL.format(body=body).encode("utf-8"))
    pm = QPixmap(size, size)
    pm.fill(QColor(0, 0, 0, 0))
    painter = QPainter(pm)
    renderer.render(painter)
    painter.end()
    return QIcon(pm)


def app_icon() -> QIcon:
    """Иконка приложения: зелёный кружок с настройками."""
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect x="4" y="4" width="56" height="56" rx="16" fill="#1d1d2b" '
           'stroke="#2a2a3e" stroke-width="2"/>'
           '<circle cx="32" cy="32" r="14" fill="none" stroke="%s" stroke-width="4"/>'
           '<circle cx="32" cy="32" r="4" fill="%s"/></svg>' % (GREEN, GREEN))
    renderer = QSvgRenderer(svg.encode("utf-8"))
    pm = QPixmap(64, 64)
    pm.fill(QColor(0, 0, 0, 0))
    p = QPainter(pm)
    renderer.render(p)
    p.end()
    return QIcon(pm)
