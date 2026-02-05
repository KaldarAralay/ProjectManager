"""Multi-theme stylesheet system for the application."""


_QSS_TEMPLATE = """
    /* Main window and general backgrounds */
    QMainWindow, QWidget {{
        background-color: {background};
        color: {text_primary};
    }}

    /* Sidebar styling */
    QWidget#sidebar {{
        background-color: {sidebar};
        border-right: 1px solid {border};
    }}

    /* Cards and panels */
    QFrame#projectCard {{
        background-color: {card};
        border: 1px solid {border};
        border-radius: 8px;
    }}

    QFrame#projectCard:hover {{
        border: 1px solid {accent};
        background-color: {card_hover};
    }}

    /* Labels */
    QLabel {{
        color: {text_primary};
    }}

    QLabel#secondaryText {{
        color: {text_secondary};
    }}

    QLabel#sectionHeader {{
        color: {text_secondary};
        font-size: 11px;
        font-weight: bold;
        padding: 8px 12px 4px 12px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {button};
        color: {text_primary};
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
    }}

    QPushButton:hover {{
        background-color: {button_hover};
    }}

    QPushButton:pressed {{
        background-color: {accent};
    }}

    QPushButton#primaryButton {{
        background-color: {accent};
    }}

    QPushButton#primaryButton:hover {{
        background-color: {accent_hover};
    }}

    QPushButton#iconButton {{
        background-color: transparent;
        padding: 4px;
        border-radius: 4px;
    }}

    QPushButton#iconButton:hover {{
        background-color: {button};
    }}

    /* Sidebar buttons */
    QPushButton#sidebarItem {{
        background-color: transparent;
        color: {text_primary};
        text-align: left;
        padding: 8px 12px;
        border-radius: 4px;
        border: none;
    }}

    QPushButton#sidebarItem:hover {{
        background-color: {button};
    }}

    QPushButton#sidebarItem:checked {{
        background-color: {accent};
    }}

    /* Line edits and search */
    QLineEdit {{
        background-color: {input};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 6px 10px;
    }}

    QLineEdit:focus {{
        border: 1px solid {accent};
    }}

    QLineEdit::placeholder {{
        color: {text_secondary};
    }}

    /* Text edits */
    QTextEdit, QPlainTextEdit {{
        background-color: {card};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 4px;
    }}

    QTextEdit:focus, QPlainTextEdit:focus {{
        border: 1px solid {accent};
    }}

    /* Combo boxes */
    QComboBox {{
        background-color: {input};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 6px 10px;
    }}

    QComboBox:hover {{
        border: 1px solid {button_hover};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}

    QComboBox::down-arrow {{
        width: 12px;
        height: 12px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {card};
        color: {text_primary};
        border: 1px solid {border};
        selection-background-color: {accent};
    }}

    /* Scroll areas */
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}

    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background-color: {background};
        width: 12px;
        border: none;
    }}

    QScrollBar::handle:vertical {{
        background-color: {button};
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background-color: {button_hover};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}

    QScrollBar:horizontal {{
        background-color: {background};
        height: 12px;
        border: none;
    }}

    QScrollBar::handle:horizontal {{
        background-color: {button};
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background-color: {button_hover};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0px;
    }}

    /* List widgets */
    QListWidget {{
        background-color: {background};
        border: none;
        outline: none;
    }}

    QListWidget::item {{
        background-color: {card};
        border: 1px solid {border};
        border-radius: 4px;
        margin: 2px 4px;
        padding: 8px;
    }}

    QListWidget::item:hover {{
        background-color: {card_hover};
        border: 1px solid {accent};
    }}

    QListWidget::item:selected {{
        background-color: {accent};
    }}

    /* Table widgets */
    QTableWidget, QTableView {{
        background-color: {background};
        alternate-background-color: {sidebar};
        border: none;
        gridline-color: {border};
    }}

    QTableWidget::item, QTableView::item {{
        padding: 8px;
    }}

    QTableWidget::item:selected, QTableView::item:selected {{
        background-color: {accent};
    }}

    QHeaderView::section {{
        background-color: {sidebar};
        color: {text_secondary};
        border: none;
        border-bottom: 1px solid {border};
        padding: 8px;
        font-weight: bold;
    }}

    /* Dialogs */
    QDialog {{
        background-color: {background};
    }}

    /* Group boxes */
    QGroupBox {{
        border: 1px solid {border};
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 8px;
    }}

    QGroupBox::title {{
        color: {text_secondary};
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
    }}

    /* Splitters */
    QSplitter::handle {{
        background-color: {border};
    }}

    QSplitter::handle:horizontal {{
        width: 1px;
    }}

    QSplitter::handle:vertical {{
        height: 1px;
    }}

    /* Menu */
    QMenu {{
        background-color: {card};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 4px;
    }}

    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
    }}

    QMenu::item:selected {{
        background-color: {accent};
    }}

    QMenu::separator {{
        height: 1px;
        background-color: {border};
        margin: 4px 8px;
    }}

    /* Toolbar */
    QToolBar {{
        background-color: {sidebar};
        border: none;
        border-bottom: 1px solid {border};
        spacing: 8px;
        padding: 4px 8px;
    }}

    /* Status badges */
    QLabel#statusActive {{
        background-color: {status_active};
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }}

    QLabel#statusHold {{
        background-color: {status_hold};
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }}

    QLabel#statusArchived {{
        background-color: {status_archived};
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {card};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 4px;
        padding: 4px 8px;
    }}
"""

THEMES = {
    "dark": {
        "name": "Dark",
        "colors": {
            "background": "#1e1e1e",
            "sidebar": "#252526",
            "card": "#2d2d2d",
            "card_hover": "#333333",
            "border": "#3c3c3c",
            "text_primary": "#ffffff",
            "text_secondary": "#808080",
            "accent": "#0078d4",
            "accent_hover": "#1084d8",
            "button": "#3c3c3c",
            "button_hover": "#4c4c4c",
            "input": "#3c3c3c",
            "status_active": "#4caf50",
            "status_hold": "#ff9800",
            "status_archived": "#9e9e9e",
        },
    },
    "light": {
        "name": "Light",
        "colors": {
            "background": "#f5f5f5",
            "sidebar": "#e8e8e8",
            "card": "#ffffff",
            "card_hover": "#f0f0f0",
            "border": "#d0d0d0",
            "text_primary": "#1a1a1a",
            "text_secondary": "#666666",
            "accent": "#0078d4",
            "accent_hover": "#1084d8",
            "button": "#e0e0e0",
            "button_hover": "#d0d0d0",
            "input": "#ffffff",
            "status_active": "#4caf50",
            "status_hold": "#ff9800",
            "status_archived": "#9e9e9e",
        },
    },
    "nord": {
        "name": "Nord",
        "colors": {
            "background": "#2e3440",
            "sidebar": "#3b4252",
            "card": "#434c5e",
            "card_hover": "#4c566a",
            "border": "#4c566a",
            "text_primary": "#eceff4",
            "text_secondary": "#d8dee9",
            "accent": "#88c0d0",
            "accent_hover": "#8fbcbb",
            "button": "#4c566a",
            "button_hover": "#5e6779",
            "input": "#3b4252",
            "status_active": "#a3be8c",
            "status_hold": "#ebcb8b",
            "status_archived": "#d8dee9",
        },
    },
}


def get_available_themes() -> list[tuple[str, str]]:
    """Return list of (theme_id, display_name) for all available themes."""
    return [(tid, t["name"]) for tid, t in THEMES.items()]


def get_theme_stylesheet(theme_id: str) -> str:
    """Generate a QSS stylesheet for the given theme.

    Args:
        theme_id: Theme identifier (e.g. 'dark', 'light', 'nord').

    Returns:
        Complete QSS stylesheet string.
    """
    colors = THEMES.get(theme_id, THEMES["dark"])["colors"]
    return _QSS_TEMPLATE.format(**colors)


def get_theme_colors(theme_id: str) -> dict:
    """Return the color dict for the given theme.

    Args:
        theme_id: Theme identifier.

    Returns:
        Dict mapping color names to hex values.
    """
    return dict(THEMES.get(theme_id, THEMES["dark"])["colors"])


# Backward compatibility
COLORS = THEMES["dark"]["colors"]


def get_dark_theme() -> str:
    """Return the dark theme stylesheet (backward compat wrapper)."""
    return get_theme_stylesheet("dark")
