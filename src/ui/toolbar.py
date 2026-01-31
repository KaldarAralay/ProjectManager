"""Top toolbar with search, view toggle, and settings."""

from PyQt6.QtWidgets import (
    QWidget, QHBoxLayout, QLineEdit, QPushButton, QButtonGroup, QSizePolicy
)
from PyQt6.QtCore import pyqtSignal, Qt


class Toolbar(QWidget):
    """Top toolbar widget."""

    search_changed = pyqtSignal(str)
    view_changed = pyqtSignal(str)  # 'grid' or 'list'
    settings_clicked = pyqtSignal()
    refresh_clicked = pyqtSignal()
    new_project_clicked = pyqtSignal()
    select_mode_changed = pyqtSignal(bool)
    batch_status_changed = pyqtSignal(str)  # 'active', 'hold', 'archived'

    def __init__(self, parent=None):
        """Initialize the toolbar."""
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the toolbar UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(12)

        # Search field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search projects...")
        self.search_input.setMinimumWidth(200)
        self.search_input.setMaximumWidth(400)
        self.search_input.textChanged.connect(self.search_changed.emit)
        layout.addWidget(self.search_input)

        # Spacer
        layout.addStretch()

        # View toggle buttons
        self.view_group = QButtonGroup(self)
        self.view_group.setExclusive(True)

        self.grid_btn = QPushButton("Grid")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.setObjectName("iconButton")
        self.grid_btn.setToolTip("Grid View")
        self.view_group.addButton(self.grid_btn)
        layout.addWidget(self.grid_btn)

        self.list_btn = QPushButton("List")
        self.list_btn.setCheckable(True)
        self.list_btn.setObjectName("iconButton")
        self.list_btn.setToolTip("List View")
        self.view_group.addButton(self.list_btn)
        layout.addWidget(self.list_btn)

        # Connect view toggle
        self.grid_btn.clicked.connect(lambda: self.view_changed.emit('grid'))
        self.list_btn.clicked.connect(lambda: self.view_changed.emit('list'))

        # Separator
        layout.addSpacing(8)

        # New Project button
        self.new_btn = QPushButton("+ New")
        self.new_btn.setObjectName("primaryButton")
        self.new_btn.setToolTip("Create New Project Folder")
        self.new_btn.clicked.connect(self.new_project_clicked.emit)
        layout.addWidget(self.new_btn)

        # Refresh button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.setObjectName("iconButton")
        self.refresh_btn.setToolTip("Refresh Projects")
        self.refresh_btn.clicked.connect(self.refresh_clicked.emit)
        layout.addWidget(self.refresh_btn)

        # Settings button
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("iconButton")
        self.settings_btn.setToolTip("Settings")
        self.settings_btn.clicked.connect(self.settings_clicked.emit)
        layout.addWidget(self.settings_btn)

        # Separator
        layout.addSpacing(12)

        # Select mode toggle
        self.select_btn = QPushButton("Select")
        self.select_btn.setCheckable(True)
        self.select_btn.setObjectName("iconButton")
        self.select_btn.setToolTip("Toggle selection mode")
        self.select_btn.clicked.connect(self._on_select_toggled)
        layout.addWidget(self.select_btn)

        # Batch status buttons (hidden by default)
        self.batch_container = QWidget()
        batch_layout = QHBoxLayout(self.batch_container)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setSpacing(4)

        self.active_btn = QPushButton("Active")
        self.active_btn.setStyleSheet("background-color: #4caf50;")
        self.active_btn.clicked.connect(lambda: self.batch_status_changed.emit('active'))
        batch_layout.addWidget(self.active_btn)

        self.hold_btn = QPushButton("On Hold")
        self.hold_btn.setStyleSheet("background-color: #ff9800;")
        self.hold_btn.clicked.connect(lambda: self.batch_status_changed.emit('hold'))
        batch_layout.addWidget(self.hold_btn)

        self.archive_btn = QPushButton("Archive")
        self.archive_btn.setStyleSheet("background-color: #9e9e9e;")
        self.archive_btn.clicked.connect(lambda: self.batch_status_changed.emit('archived'))
        batch_layout.addWidget(self.archive_btn)

        self.batch_container.setVisible(False)
        layout.addWidget(self.batch_container)

    def _on_select_toggled(self, checked: bool):
        """Handle select mode toggle."""
        self.batch_container.setVisible(checked)
        self.select_mode_changed.emit(checked)

    def set_view(self, view: str):
        """Set the current view mode.

        Args:
            view: 'grid' or 'list'
        """
        if view == 'grid':
            self.grid_btn.setChecked(True)
        else:
            self.list_btn.setChecked(True)

    def clear_search(self):
        """Clear the search input."""
        self.search_input.clear()
