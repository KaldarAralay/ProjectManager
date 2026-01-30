"""Main application window."""

import subprocess
import platform
import os
from pathlib import Path
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QScrollArea, QFrame, QLabel, QMessageBox, QGridLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer

from .toolbar import Toolbar
from .sidebar import Sidebar
from .project_card import ProjectCard
from .project_list import ProjectListWidget
from .dialogs.settings import SettingsDialog
from .dialogs.project_details import ProjectDetailsDialog
from .dialogs.new_project import NewProjectDialog
from ..models.project import Project
from ..utils.process_checker import get_open_projects_by_window_titles

if TYPE_CHECKING:
    from ..app import ProjectManagerApp


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, app: 'ProjectManagerApp'):
        """Initialize the main window.

        Args:
            app: Application controller.
        """
        super().__init__()
        self.app = app
        self._current_view = 'grid'
        self._project_cards: list[ProjectCard] = []

        self._setup_ui()
        self.setWindowTitle("Project Manager")
        self.resize(1200, 800)

        # Timer to refresh open project status every 3 seconds
        self._open_status_timer = QTimer(self)
        self._open_status_timer.timeout.connect(self._refresh_open_status)
        self._open_status_timer.start(3000)

    def _setup_ui(self):
        """Set up the window UI."""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Toolbar
        self.toolbar = Toolbar()
        self.toolbar.search_changed.connect(self.app.search_projects)
        self.toolbar.view_changed.connect(self._on_view_changed)
        self.toolbar.settings_clicked.connect(self._show_settings)
        self.toolbar.refresh_clicked.connect(self.app.refresh_projects)
        self.toolbar.new_project_clicked.connect(self._show_new_project)
        main_layout.addWidget(self.toolbar)

        # Main content area with splitter
        self.splitter = QSplitter(Qt.Orientation.Horizontal)

        # Sidebar
        self.sidebar = Sidebar()
        self.sidebar.status_filter_changed.connect(self.app.filter_by_status)
        self.sidebar.language_filter_changed.connect(self.app.filter_by_language)
        self.splitter.addWidget(self.sidebar)

        # Content area
        self.content_widget = QWidget()
        content_layout = QVBoxLayout(self.content_widget)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Grid view (scroll area with grid of cards)
        self.grid_scroll = QScrollArea()
        self.grid_scroll.setWidgetResizable(True)
        self.grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_scroll.setFrameShape(QFrame.Shape.NoFrame)

        self.grid_container = QWidget()
        self.grid_layout = QVBoxLayout(self.grid_container)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.grid_scroll.setWidget(self.grid_container)
        content_layout.addWidget(self.grid_scroll)

        # List view
        self.list_view = ProjectListWidget()
        self.list_view.open_clicked.connect(self._open_project)
        self.list_view.details_clicked.connect(self._show_project_details)
        self.list_view.open_folder_clicked.connect(self._open_folder)
        self.list_view.open_terminal_clicked.connect(self._open_terminal)
        self.list_view.open_claude_clicked.connect(self._open_claude)
        self.list_view.setVisible(False)
        content_layout.addWidget(self.list_view)

        # Empty state message
        self.empty_label = QLabel("No projects found.\nAdd scan directories in Settings and click Refresh.")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_label.setStyleSheet("color: #808080; font-size: 14px;")
        self.empty_label.setVisible(False)
        content_layout.addWidget(self.empty_label)

        self.splitter.addWidget(self.content_widget)
        self.splitter.setSizes([200, 1000])

        main_layout.addWidget(self.splitter)

    def _on_view_changed(self, view: str):
        """Handle view toggle.

        Args:
            view: 'grid' or 'list'
        """
        self._current_view = view

        if view == 'grid':
            self.grid_scroll.setVisible(True)
            self.list_view.setVisible(False)
        else:
            self.grid_scroll.setVisible(False)
            self.list_view.setVisible(True)

    def update_projects(self, projects: list[Project]):
        """Update the displayed projects.

        Args:
            projects: List of projects to display.
        """
        # Clear existing cards
        for card in self._project_cards:
            card.deleteLater()
        self._project_cards.clear()

        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item:
                if item.widget():
                    item.widget().deleteLater()
                elif item.layout():
                    # Clear nested layouts
                    while item.layout().count():
                        nested = item.layout().takeAt(0)
                        if nested and nested.widget():
                            nested.widget().deleteLater()

        # Show/hide empty state
        self.empty_label.setVisible(len(projects) == 0)
        self.grid_scroll.setVisible(len(projects) > 0 and self._current_view == 'grid')
        self.list_view.setVisible(len(projects) > 0 and self._current_view == 'list')

        if not projects:
            return

        # Get currently open projects
        open_names = get_open_projects_by_window_titles()

        # Calculate cards per row based on available width
        available_width = self.grid_scroll.viewport().width() - 32  # Account for margins
        card_width = 220
        spacing = 16
        cards_per_row = max(1, (available_width + spacing) // (card_width + spacing))

        # Create cards in rows
        current_row = None
        for i, project in enumerate(projects):
            if i % cards_per_row == 0:
                # Start a new row
                current_row = QHBoxLayout()
                current_row.setSpacing(16)
                current_row.setAlignment(Qt.AlignmentFlag.AlignLeft)
                self.grid_layout.addLayout(current_row)

            # Check if project is open
            is_open = project.name.lower() in open_names

            card = ProjectCard(project, is_open=is_open)
            card.open_clicked.connect(self._open_project)
            card.details_clicked.connect(self._show_project_details)
            card.open_folder_clicked.connect(self._open_folder)
            card.open_terminal_clicked.connect(self._open_terminal)
            card.open_claude_clicked.connect(self._open_claude)

            current_row.addWidget(card)
            self._project_cards.append(card)

        # Add stretch at the bottom to push cards to top
        self.grid_layout.addStretch()

        # Update list view
        self.list_view.set_projects(projects)

    def update_language_filters(self, languages: list[str]):
        """Update the language filter list.

        Args:
            languages: List of language names.
        """
        self.sidebar.update_languages(languages)

    def _open_project(self, project: Project):
        """Open a project folder in the file explorer.

        Args:
            project: Project to open.
        """
        self._open_folder(project)

    def _open_folder(self, project: Project):
        """Open project folder in file explorer.

        Args:
            project: Project to open.
        """
        try:
            if platform.system() == 'Windows':
                os.startfile(str(project.path))
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(project.path)])
            else:
                subprocess.Popen(['xdg-open', str(project.path)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open folder: {e}")

    def _open_terminal(self, project: Project):
        """Open terminal at project path.

        Args:
            project: Project to open terminal for.
        """
        try:
            if platform.system() == 'Windows':
                subprocess.Popen(['cmd', '/c', 'start', 'cmd'], cwd=str(project.path), shell=True)
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', '-a', 'Terminal', str(project.path)])
            else:
                # Try common Linux terminals
                for term in ['gnome-terminal', 'konsole', 'xterm']:
                    try:
                        subprocess.Popen([term], cwd=str(project.path))
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open terminal: {e}")

    def _open_claude(self, project: Project):
        """Open Claude Code for the project.

        Args:
            project: Project to open in Claude Code.
        """
        try:
            if platform.system() == 'Windows':
                # Open a new terminal and run claude command
                subprocess.Popen(
                    ['cmd', '/c', 'start', 'cmd', '/k', 'claude'],
                    cwd=str(project.path),
                    shell=True
                )
            elif platform.system() == 'Darwin':
                # macOS - open Terminal and run claude
                subprocess.Popen(
                    ['osascript', '-e',
                     f'tell application "Terminal" to do script "cd {project.path} && claude"']
                )
            else:
                # Linux - try to open terminal with claude
                for term in ['gnome-terminal', 'konsole', 'xterm']:
                    try:
                        subprocess.Popen([term, '--', 'claude'], cwd=str(project.path))
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open Claude Code: {e}")

    def _show_project_details(self, project: Project):
        """Show project details dialog.

        Args:
            project: Project to edit.
        """
        dialog = ProjectDetailsDialog(project, self)
        if dialog.exec():
            updated = dialog.get_project()
            self.app.update_project(updated)

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(
            self.app.get_scan_directories(),
            self.app.get_editor_command(),
            self
        )
        if dialog.exec():
            self.app.set_scan_directories(dialog.get_directories())
            self.app.set_editor_command(dialog.get_editor_command())

    def _show_new_project(self):
        """Show new project dialog."""
        dialog = NewProjectDialog(
            self.app.get_scan_directories(),
            self
        )
        if dialog.exec():
            created_path = dialog.get_created_path()
            if created_path:
                # Open the new folder
                self._open_folder_path(created_path)
                # Refresh to pick up the new project
                self.app.refresh_projects()

    def _open_folder_path(self, path: Path):
        """Open a folder path in file explorer.

        Args:
            path: Path to open.
        """
        try:
            if platform.system() == 'Windows':
                os.startfile(str(path))
            elif platform.system() == 'Darwin':
                subprocess.Popen(['open', str(path)])
            else:
                subprocess.Popen(['xdg-open', str(path)])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to open folder: {e}")

    def show_message(self, message: str):
        """Show a message to the user.

        Args:
            message: Message to display.
        """
        QMessageBox.information(self, "Project Manager", message)

    def resizeEvent(self, event):
        """Handle window resize to reflow grid."""
        super().resizeEvent(event)
        # Reflow grid on resize
        if self._project_cards and self._current_view == 'grid':
            projects = [card.project for card in self._project_cards]
            self.update_projects(projects)

    def _refresh_open_status(self):
        """Refresh the open status indicators for all project cards."""
        if not self._project_cards:
            return

        try:
            open_names = get_open_projects_by_window_titles()
            for card in self._project_cards:
                is_open = card.project.name.lower() in open_names
                card.set_open_status(is_open)
        except Exception:
            pass  # Silently ignore errors in background refresh
