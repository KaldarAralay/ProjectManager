"""Navigation sidebar with filters."""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QScrollArea, QFrame
)
from PyQt6.QtCore import pyqtSignal, Qt


class Sidebar(QWidget):
    """Navigation sidebar with status and language filters."""

    status_filter_changed = pyqtSignal(object)  # str or None
    language_filter_changed = pyqtSignal(object)  # str or None

    def __init__(self, parent=None):
        """Initialize the sidebar."""
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(200)

        self._status_buttons: dict[str, QPushButton] = {}
        self._language_buttons: dict[str, QPushButton] = {}
        self._current_status = None
        self._current_language = None

        self._setup_ui()

    def _setup_ui(self):
        """Set up the sidebar UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(0)

        # Status section
        status_header = QLabel("STATUS")
        status_header.setObjectName("sectionHeader")
        layout.addWidget(status_header)

        # Status filter buttons
        status_filters = [
            ('all', 'All Projects'),
            ('active', 'Active'),
            ('hold', 'On Hold'),
            ('archived', 'Archived'),
        ]

        for status_id, label in status_filters:
            btn = QPushButton(label)
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            if status_id == 'all':
                btn.setChecked(True)
            btn.clicked.connect(lambda checked, s=status_id: self._on_status_clicked(s))
            layout.addWidget(btn)
            self._status_buttons[status_id] = btn

        # Separator
        layout.addSpacing(16)

        # Languages section header
        lang_header = QLabel("LANGUAGES")
        lang_header.setObjectName("sectionHeader")
        layout.addWidget(lang_header)

        # Scroll area for languages
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._languages_container = QWidget()
        self._languages_layout = QVBoxLayout(self._languages_container)
        self._languages_layout.setContentsMargins(0, 0, 0, 0)
        self._languages_layout.setSpacing(0)
        self._languages_layout.addStretch()

        scroll.setWidget(self._languages_container)
        layout.addWidget(scroll, 1)

    def _on_status_clicked(self, status_id: str):
        """Handle status filter button click.

        Args:
            status_id: Status identifier.
        """
        # Uncheck other status buttons
        for sid, btn in self._status_buttons.items():
            btn.setChecked(sid == status_id)

        # Emit filter change
        self._current_status = None if status_id == 'all' else status_id
        self.status_filter_changed.emit(self._current_status)

    def _on_language_clicked(self, language: str, checked: bool):
        """Handle language filter button click.

        Args:
            language: Language name.
            checked: Whether the button is now checked.
        """
        if checked:
            # Uncheck previous language button
            if self._current_language and self._current_language in self._language_buttons:
                self._language_buttons[self._current_language].setChecked(False)
            self._current_language = language
        else:
            # Unchecking current language clears filter
            self._current_language = None

        self.language_filter_changed.emit(self._current_language)

    def update_languages(self, languages: list[str]):
        """Update the language filter list.

        Args:
            languages: List of language names.
        """
        # Clear existing language buttons
        for btn in self._language_buttons.values():
            btn.deleteLater()
        self._language_buttons.clear()

        # Remove stretch item
        while self._languages_layout.count() > 0:
            item = self._languages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new language buttons
        for language in languages:
            btn = QPushButton(language)
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(lambda checked, lang=language: self._on_language_clicked(lang, checked))
            self._languages_layout.addWidget(btn)
            self._language_buttons[language] = btn

        # Re-add stretch
        self._languages_layout.addStretch()

        # Restore selection if still valid
        if self._current_language and self._current_language in self._language_buttons:
            self._language_buttons[self._current_language].setChecked(True)
        elif self._current_language:
            self._current_language = None
            self.language_filter_changed.emit(None)

    def clear_filters(self):
        """Clear all filters."""
        # Reset status
        self._on_status_clicked('all')

        # Reset language
        if self._current_language and self._current_language in self._language_buttons:
            self._language_buttons[self._current_language].setChecked(False)
        self._current_language = None
        self.language_filter_changed.emit(None)
