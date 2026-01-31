"""Project list widget for list view."""

from PyQt6.QtWidgets import (
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QWidget, QHBoxLayout, QLabel, QPushButton, QMenu
)
from PyQt6.QtCore import pyqtSignal, Qt

from ..models.project import Project
from ..utils.theme import COLORS


class ProjectListWidget(QTableWidget):
    """Table widget displaying projects in list view."""

    open_clicked = pyqtSignal(Project)
    details_clicked = pyqtSignal(Project)
    open_folder_clicked = pyqtSignal(Project)
    open_terminal_clicked = pyqtSignal(Project)
    open_claude_clicked = pyqtSignal(Project)
    run_command_clicked = pyqtSignal(Project, dict)  # project, command dict

    def __init__(self, parent=None):
        """Initialize the list widget."""
        super().__init__(parent)
        self._projects: list[Project] = []

        self._setup_ui()

    def _setup_ui(self):
        """Set up the table UI."""
        # Set up columns
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(['Name', 'Languages', 'Status', 'Modified', 'Actions'])

        # Configure header
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(4, 120)

        # Configure table
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setShowGrid(False)
        self.setAlternatingRowColors(True)
        self.verticalHeader().setVisible(False)
        self.setSortingEnabled(True)

        # Connect double-click
        self.cellDoubleClicked.connect(self._on_double_click)

    def set_projects(self, projects: list[Project]):
        """Set the projects to display.

        Args:
            projects: List of projects.
        """
        self._projects = projects
        self._populate_table()

    def _populate_table(self):
        """Populate the table with project data."""
        self.setSortingEnabled(False)
        self.setRowCount(len(self._projects))

        for row, project in enumerate(self._projects):
            # Name (with star if favorite)
            name_text = f"★ {project.name}" if project.favorite else project.name
            name_item = QTableWidgetItem(name_text)
            name_item.setData(Qt.ItemDataRole.UserRole, row)
            if project.favorite:
                name_item.setForeground(Qt.GlobalColor.yellow)
            self.setItem(row, 0, name_item)

            # Languages
            languages_text = ', '.join(project.languages[:3])
            if len(project.languages) > 3:
                languages_text += f' +{len(project.languages) - 3}'
            lang_item = QTableWidgetItem(languages_text)
            self.setItem(row, 1, lang_item)

            # Status
            status_item = QTableWidgetItem(project.status_display)
            status_colors = {
                'active': COLORS['status_active'],
                'hold': COLORS['status_hold'],
                'archived': COLORS['status_archived'],
            }
            status_item.setForeground(
                Qt.GlobalColor.white if project.status in status_colors else Qt.GlobalColor.gray
            )
            self.setItem(row, 2, status_item)

            # Modified
            modified_item = QTableWidgetItem(project.last_modified_display)
            self.setItem(row, 3, modified_item)

            # Actions
            actions_widget = self._create_actions_widget(project)
            self.setCellWidget(row, 4, actions_widget)

            # Set row height
            self.setRowHeight(row, 44)

        self.setSortingEnabled(True)

    def _create_actions_widget(self, project: Project) -> QWidget:
        """Create the actions widget for a row.

        Args:
            project: Project for the row.

        Returns:
            Widget containing action buttons.
        """
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        open_btn = QPushButton("Open")
        open_btn.setObjectName("primaryButton")
        open_btn.setFixedWidth(50)
        open_btn.clicked.connect(lambda: self.open_clicked.emit(project))
        layout.addWidget(open_btn)

        details_btn = QPushButton("...")
        details_btn.setToolTip("More actions")
        details_btn.setFixedWidth(30)
        details_btn.clicked.connect(lambda: self._show_context_menu(project))
        layout.addWidget(details_btn)

        layout.addStretch()
        return widget

    def _show_context_menu(self, project: Project):
        """Show context menu for a project.

        Args:
            project: Project to show menu for.
        """
        menu = QMenu(self)

        open_action = menu.addAction("Open Folder")
        open_action.triggered.connect(lambda: self.open_clicked.emit(project))

        terminal_action = menu.addAction("Open Terminal")
        terminal_action.triggered.connect(lambda: self.open_terminal_clicked.emit(project))

        claude_action = menu.addAction("Open in Claude Code")
        claude_action.triggered.connect(lambda: self.open_claude_clicked.emit(project))

        menu.addSeparator()

        details_action = menu.addAction("Edit Details")
        details_action.triggered.connect(lambda: self.details_clicked.emit(project))

        # Custom Commands submenu
        if project.commands:
            menu.addSeparator()
            commands_menu = menu.addMenu("Custom Commands")
            for cmd in project.commands:
                action = commands_menu.addAction(cmd['name'])
                action.triggered.connect(
                    lambda checked, p=project, c=cmd: self.run_command_clicked.emit(p, c)
                )

        menu.exec(self.cursor().pos())

    def _on_double_click(self, row: int, column: int):
        """Handle double-click on a row.

        Args:
            row: Row index.
            column: Column index.
        """
        if 0 <= row < len(self._projects):
            self.open_clicked.emit(self._projects[row])

    def contextMenuEvent(self, event):
        """Show context menu on right-click."""
        row = self.rowAt(event.pos().y())
        if 0 <= row < len(self._projects):
            self._show_context_menu(self._projects[row])

    def get_selected_project(self) -> Project | None:
        """Get the currently selected project.

        Returns:
            Selected project or None.
        """
        rows = self.selectionModel().selectedRows()
        if rows:
            row = rows[0].row()
            if 0 <= row < len(self._projects):
                return self._projects[row]
        return None
