"""Project card widget for grid view."""

from PyQt6.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QWidget, QCheckBox
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..models.project import Project
from ..utils.theme import COLORS


class ProjectCard(QFrame):
    """Card widget displaying a project in grid view."""

    open_clicked = pyqtSignal(Project)
    details_clicked = pyqtSignal(Project)
    open_folder_clicked = pyqtSignal(Project)
    open_terminal_clicked = pyqtSignal(Project)
    open_claude_clicked = pyqtSignal(Project)
    selection_changed = pyqtSignal(Project, bool)
    run_command_clicked = pyqtSignal(Project, dict)  # project, command dict

    def __init__(self, project: Project, is_open: bool = False, parent=None):
        """Initialize the project card.

        Args:
            project: Project to display.
            is_open: Whether the project is currently open in a terminal/editor.
        """
        super().__init__(parent)
        self.project = project
        self._is_open = is_open
        self._select_mode = False
        self.setObjectName("projectCard")
        self.setFixedSize(220, 160)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Top row with checkbox, name, and indicators
        top_row = QHBoxLayout()
        top_row.setSpacing(4)

        # Selection checkbox (hidden by default)
        self.checkbox = QCheckBox()
        self.checkbox.setVisible(False)
        self.checkbox.stateChanged.connect(self._on_checkbox_changed)
        top_row.addWidget(self.checkbox)

        # Project name
        self.name_label = QLabel(self.project.name)
        self.name_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        self.name_label.setWordWrap(True)
        self.name_label.setMaximumHeight(40)
        top_row.addWidget(self.name_label, 1)

        # Favorite star
        self.fav_label = QLabel("★")
        self.fav_label.setStyleSheet("color: #ffc107; font-size: 16px;")
        self.fav_label.setVisible(self.project.favorite)
        top_row.addWidget(self.fav_label)

        # Open indicator (green dot)
        self.open_indicator = QLabel("●")
        self.open_indicator.setStyleSheet("color: #4caf50; font-size: 12px;")
        self.open_indicator.setToolTip("Currently open")
        self.open_indicator.setVisible(self._is_open)
        top_row.addWidget(self.open_indicator)

        layout.addLayout(top_row)

        # Languages
        lang_layout = QHBoxLayout()
        lang_layout.setSpacing(4)

        for i, lang in enumerate(self.project.languages[:3]):
            lang_label = QLabel(lang)
            lang_label.setStyleSheet(f"""
                background-color: #3c3c3c;
                color: {COLORS['text_secondary']};
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 11px;
            """)
            lang_layout.addWidget(lang_label)

        if len(self.project.languages) > 3:
            more_label = QLabel(f"+{len(self.project.languages) - 3}")
            more_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
            lang_layout.addWidget(more_label)

        lang_layout.addStretch()
        layout.addLayout(lang_layout)

        # Status badge
        status_layout = QHBoxLayout()

        status_colors = {
            'active': COLORS['status_active'],
            'hold': COLORS['status_hold'],
            'archived': COLORS['status_archived'],
        }
        status_color = status_colors.get(self.project.status, COLORS['text_secondary'])

        status_label = QLabel(self.project.status_display)
        status_label.setStyleSheet(f"""
            background-color: {status_color};
            color: white;
            border-radius: 4px;
            padding: 2px 8px;
            font-size: 11px;
        """)
        status_layout.addWidget(status_label)
        status_layout.addStretch()
        layout.addLayout(status_layout)

        # Last modified
        self.modified_label = QLabel(self.project.last_modified_display)
        self.modified_label.setObjectName("secondaryText")
        self.modified_label.setStyleSheet(f"color: {COLORS['text_secondary']}; font-size: 11px;")
        layout.addWidget(self.modified_label)

        layout.addStretch()

        # Action buttons (hidden by default, shown on hover)
        self.button_container = QWidget()
        self.button_container.setVisible(False)
        btn_layout = QHBoxLayout(self.button_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(4)

        open_btn = QPushButton("Open")
        open_btn.setObjectName("primaryButton")
        open_btn.clicked.connect(lambda: self.open_clicked.emit(self.project))
        btn_layout.addWidget(open_btn)

        details_btn = QPushButton("Details")
        details_btn.clicked.connect(lambda: self.details_clicked.emit(self.project))
        btn_layout.addWidget(details_btn)

        layout.addWidget(self.button_container)

    def enterEvent(self, event):
        """Show action buttons on hover."""
        self.button_container.setVisible(True)
        super().enterEvent(event)

    def leaveEvent(self, event):
        """Hide action buttons when not hovering."""
        self.button_container.setVisible(False)
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Open project on double-click."""
        self.open_clicked.emit(self.project)
        super().mouseDoubleClickEvent(event)

    def contextMenuEvent(self, event):
        """Show context menu."""
        from PyQt6.QtWidgets import QMenu

        menu = QMenu(self)

        open_action = menu.addAction("Open Folder")
        open_action.triggered.connect(lambda: self.open_clicked.emit(self.project))

        terminal_action = menu.addAction("Open Terminal")
        terminal_action.triggered.connect(lambda: self.open_terminal_clicked.emit(self.project))

        claude_action = menu.addAction("Open in Claude Code")
        claude_action.triggered.connect(lambda: self.open_claude_clicked.emit(self.project))

        menu.addSeparator()

        details_action = menu.addAction("Edit Details")
        details_action.triggered.connect(lambda: self.details_clicked.emit(self.project))

        # Custom Commands submenu
        if self.project.commands:
            menu.addSeparator()
            commands_menu = menu.addMenu("Custom Commands")
            for cmd in self.project.commands:
                action = commands_menu.addAction(cmd['name'])
                action.triggered.connect(
                    lambda checked, c=cmd: self.run_command_clicked.emit(self.project, c)
                )

        menu.exec(event.globalPos())

    def update_project(self, project: Project):
        """Update the displayed project data.

        Args:
            project: Updated project.
        """
        self.project = project
        self.name_label.setText(project.name)
        self.modified_label.setText(project.last_modified_display)
        self.fav_label.setVisible(project.favorite)

    def set_open_status(self, is_open: bool):
        """Set whether the project is currently open.

        Args:
            is_open: Whether the project is open.
        """
        self._is_open = is_open
        self.open_indicator.setVisible(is_open)

    def set_select_mode(self, enabled: bool):
        """Enable or disable selection mode.

        Args:
            enabled: Whether selection mode is enabled.
        """
        self._select_mode = enabled
        self.checkbox.setVisible(enabled)
        if not enabled:
            self.checkbox.setChecked(False)

    def is_selected(self) -> bool:
        """Check if this card is selected.

        Returns:
            True if selected.
        """
        return self.checkbox.isChecked()

    def set_selected(self, selected: bool):
        """Set the selection state.

        Args:
            selected: Whether to select this card.
        """
        self.checkbox.setChecked(selected)

    def _on_checkbox_changed(self, state: int):
        """Handle checkbox state change."""
        self.selection_changed.emit(self.project, state == 2)  # 2 = Qt.Checked
