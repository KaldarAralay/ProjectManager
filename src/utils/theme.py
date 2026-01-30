"""Dark theme stylesheet for the application."""


def get_dark_theme() -> str:
    """Return the dark theme stylesheet."""
    return """
    /* Main window and general backgrounds */
    QMainWindow, QWidget {
        background-color: #1e1e1e;
        color: #ffffff;
    }

    /* Sidebar styling */
    QWidget#sidebar {
        background-color: #252526;
        border-right: 1px solid #3c3c3c;
    }

    /* Cards and panels */
    QFrame#projectCard {
        background-color: #2d2d2d;
        border: 1px solid #3c3c3c;
        border-radius: 8px;
    }

    QFrame#projectCard:hover {
        border: 1px solid #0078d4;
        background-color: #333333;
    }

    /* Labels */
    QLabel {
        color: #ffffff;
    }

    QLabel#secondaryText {
        color: #808080;
    }

    QLabel#sectionHeader {
        color: #808080;
        font-size: 11px;
        font-weight: bold;
        padding: 8px 12px 4px 12px;
    }

    /* Buttons */
    QPushButton {
        background-color: #3c3c3c;
        color: #ffffff;
        border: none;
        padding: 6px 12px;
        border-radius: 4px;
    }

    QPushButton:hover {
        background-color: #4c4c4c;
    }

    QPushButton:pressed {
        background-color: #0078d4;
    }

    QPushButton#primaryButton {
        background-color: #0078d4;
    }

    QPushButton#primaryButton:hover {
        background-color: #1084d8;
    }

    QPushButton#iconButton {
        background-color: transparent;
        padding: 4px;
        border-radius: 4px;
    }

    QPushButton#iconButton:hover {
        background-color: #3c3c3c;
    }

    /* Sidebar buttons */
    QPushButton#sidebarItem {
        background-color: transparent;
        color: #ffffff;
        text-align: left;
        padding: 8px 12px;
        border-radius: 4px;
        border: none;
    }

    QPushButton#sidebarItem:hover {
        background-color: #3c3c3c;
    }

    QPushButton#sidebarItem:checked {
        background-color: #0078d4;
    }

    /* Line edits and search */
    QLineEdit {
        background-color: #3c3c3c;
        color: #ffffff;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 6px 10px;
    }

    QLineEdit:focus {
        border: 1px solid #0078d4;
    }

    QLineEdit::placeholder {
        color: #808080;
    }

    /* Text edits */
    QTextEdit, QPlainTextEdit {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
    }

    QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #0078d4;
    }

    /* Combo boxes */
    QComboBox {
        background-color: #3c3c3c;
        color: #ffffff;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 6px 10px;
    }

    QComboBox:hover {
        border: 1px solid #4c4c4c;
    }

    QComboBox::drop-down {
        border: none;
        width: 20px;
    }

    QComboBox::down-arrow {
        width: 12px;
        height: 12px;
    }

    QComboBox QAbstractItemView {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3c3c3c;
        selection-background-color: #0078d4;
    }

    /* Scroll areas */
    QScrollArea {
        border: none;
        background-color: transparent;
    }

    QScrollArea > QWidget > QWidget {
        background-color: transparent;
    }

    /* Scrollbars */
    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
        border: none;
    }

    QScrollBar::handle:vertical {
        background-color: #3c3c3c;
        min-height: 30px;
        border-radius: 6px;
        margin: 2px;
    }

    QScrollBar::handle:vertical:hover {
        background-color: #4c4c4c;
    }

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        height: 0px;
    }

    QScrollBar:horizontal {
        background-color: #1e1e1e;
        height: 12px;
        border: none;
    }

    QScrollBar::handle:horizontal {
        background-color: #3c3c3c;
        min-width: 30px;
        border-radius: 6px;
        margin: 2px;
    }

    QScrollBar::handle:horizontal:hover {
        background-color: #4c4c4c;
    }

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
        width: 0px;
    }

    /* List widgets */
    QListWidget {
        background-color: #1e1e1e;
        border: none;
        outline: none;
    }

    QListWidget::item {
        background-color: #2d2d2d;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        margin: 2px 4px;
        padding: 8px;
    }

    QListWidget::item:hover {
        background-color: #333333;
        border: 1px solid #0078d4;
    }

    QListWidget::item:selected {
        background-color: #0078d4;
    }

    /* Table widgets */
    QTableWidget, QTableView {
        background-color: #1e1e1e;
        alternate-background-color: #252526;
        border: none;
        gridline-color: #3c3c3c;
    }

    QTableWidget::item, QTableView::item {
        padding: 8px;
    }

    QTableWidget::item:selected, QTableView::item:selected {
        background-color: #0078d4;
    }

    QHeaderView::section {
        background-color: #252526;
        color: #808080;
        border: none;
        border-bottom: 1px solid #3c3c3c;
        padding: 8px;
        font-weight: bold;
    }

    /* Dialogs */
    QDialog {
        background-color: #1e1e1e;
    }

    /* Group boxes */
    QGroupBox {
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        margin-top: 12px;
        padding-top: 8px;
    }

    QGroupBox::title {
        color: #808080;
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 4px;
    }

    /* Splitters */
    QSplitter::handle {
        background-color: #3c3c3c;
    }

    QSplitter::handle:horizontal {
        width: 1px;
    }

    QSplitter::handle:vertical {
        height: 1px;
    }

    /* Menu */
    QMenu {
        background-color: #2d2d2d;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 4px;
    }

    QMenu::item {
        padding: 6px 24px;
        border-radius: 4px;
    }

    QMenu::item:selected {
        background-color: #0078d4;
    }

    QMenu::separator {
        height: 1px;
        background-color: #3c3c3c;
        margin: 4px 8px;
    }

    /* Toolbar */
    QToolBar {
        background-color: #252526;
        border: none;
        border-bottom: 1px solid #3c3c3c;
        spacing: 8px;
        padding: 4px 8px;
    }

    /* Status badges */
    QLabel#statusActive {
        background-color: #4caf50;
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }

    QLabel#statusHold {
        background-color: #ff9800;
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }

    QLabel#statusArchived {
        background-color: #9e9e9e;
        color: #ffffff;
        border-radius: 4px;
        padding: 2px 8px;
        font-size: 11px;
    }

    /* Tooltips */
    QToolTip {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 1px solid #3c3c3c;
        border-radius: 4px;
        padding: 4px 8px;
    }
    """


# Color constants for programmatic use
COLORS = {
    'background': '#1e1e1e',
    'sidebar': '#252526',
    'card': '#2d2d2d',
    'border': '#3c3c3c',
    'text_primary': '#ffffff',
    'text_secondary': '#808080',
    'accent': '#0078d4',
    'status_active': '#4caf50',
    'status_hold': '#ff9800',
    'status_archived': '#9e9e9e',
}
