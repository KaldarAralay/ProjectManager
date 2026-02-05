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
from .dialogs.readme_viewer import ReadmeViewerDialog
from ..models.project import Project
from ..utils.process_checker import get_open_projects_by_window_titles
from .mission_control_view import MissionControlView

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

        # Selection mode state
        self._select_mode = False
        self._selected_projects: set[str] = set()  # Set of project paths

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
        self.toolbar.select_mode_changed.connect(self._on_select_mode_changed)
        self.toolbar.batch_status_changed.connect(self._on_batch_status_change)
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
        self.list_view.run_command_clicked.connect(self._run_custom_command)
        self.list_view.view_readme_clicked.connect(self._view_readme)
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

        # Mission Control view (hidden by default)
        self.mission_control_view = MissionControlView()
        mc = self.mission_control_view
        mc.open_clicked.connect(self._open_project)
        mc.details_clicked.connect(self._show_project_details)
        mc.open_folder_clicked.connect(self._open_folder)
        mc.open_terminal_clicked.connect(self._open_terminal)
        mc.open_claude_clicked.connect(self._open_claude)
        mc.run_command_clicked.connect(self._run_custom_command)
        mc.view_readme_clicked.connect(self._view_readme)
        mc.settings_requested.connect(self._show_settings)
        mc.refresh_requested.connect(self.app.refresh_projects)
        mc.batch_status_changed.connect(self._on_mc_batch_status_change)
        mc.setVisible(False)
        main_layout.addWidget(mc)

    def apply_theme_layout(self, theme_id: str):
        """Switch between normal and Mission Control layouts.

        Args:
            theme_id: Current theme identifier.
        """
        is_mc = theme_id == "mission_control"
        self.toolbar.setVisible(not is_mc)
        self.splitter.setVisible(not is_mc)
        self.mission_control_view.setVisible(is_mc)

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
            card.selection_changed.connect(self._on_selection_changed)
            card.run_command_clicked.connect(self._run_custom_command)
            card.view_readme_clicked.connect(self._view_readme)

            # Restore select mode if active
            if self._select_mode:
                card.set_select_mode(True)

            current_row.addWidget(card)
            self._project_cards.append(card)

        # Add stretch at the bottom to push cards to top
        self.grid_layout.addStretch()

        # Update list view
        self.list_view.set_projects(projects)

        # Update mission control view
        self.mission_control_view.update_projects(projects)

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

    def _run_custom_command(self, project: Project, command: dict):
        """Run a custom command for the project.

        Args:
            project: Project to run command for.
            command: Command dict with 'name' and 'command' keys.
        """
        try:
            # Replace placeholders
            cmd_str = command['command']
            cmd_str = cmd_str.replace('{path}', str(project.path))
            cmd_str = cmd_str.replace('{name}', project.name)

            if platform.system() == 'Windows':
                # Open a new terminal and run the command
                subprocess.Popen(
                    ['cmd', '/c', 'start', 'cmd', '/k', cmd_str],
                    cwd=str(project.path),
                    shell=True
                )
            elif platform.system() == 'Darwin':
                # macOS - open Terminal and run command
                subprocess.Popen(
                    ['osascript', '-e',
                     f'tell application "Terminal" to do script "cd {project.path} && {cmd_str}"']
                )
            else:
                # Linux - try to open terminal with command
                for term in ['gnome-terminal', 'konsole', 'xterm']:
                    try:
                        subprocess.Popen([term, '--', 'bash', '-c', cmd_str], cwd=str(project.path))
                        break
                    except FileNotFoundError:
                        continue
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to run command: {e}")

    def _show_project_details(self, project: Project):
        """Show project details dialog.

        Args:
            project: Project to edit.
        """
        dialog = ProjectDetailsDialog(project, self)
        if dialog.exec():
            updated = dialog.get_project()
            self.app.update_project(updated)

    def _view_readme(self, project: Project):
        """Show README viewer for a project.

        Args:
            project: Project to view README for.
        """
        dialog = ReadmeViewerDialog(project.path, self)
        dialog.exec()

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(
            self.app.get_scan_directories(),
            self.app.get_editor_command(),
            current_theme=self.app.get_theme(),
            parent=self
        )
        if dialog.exec():
            self.app.set_scan_directories(dialog.get_directories())
            self.app.set_editor_command(dialog.get_editor_command())
            self.app.set_theme(dialog.get_theme())

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
        # Reflow grid on resize (skip when mission control is active)
        if (self._project_cards and self._current_view == 'grid'
                and not self.mission_control_view.isVisible()):
            projects = [card.project for card in self._project_cards]
            self.update_projects(projects)

    def _refresh_open_status(self):
        """Refresh the open status indicators for all project cards."""
        try:
            open_names = get_open_projects_by_window_titles()

            # Update normal view cards
            for card in self._project_cards:
                is_open = card.project.name.lower() in open_names
                card.set_open_status(is_open)

            # Update mission control view
            self.mission_control_view.update_open_status(open_names)
        except Exception:
            pass  # Silently ignore errors in background refresh

    def _on_select_mode_changed(self, enabled: bool):
        """Handle selection mode toggle.

        Args:
            enabled: Whether selection mode is enabled.
        """
        self._select_mode = enabled
        self._selected_projects.clear()

        for card in self._project_cards:
            card.set_select_mode(enabled)

    def _on_selection_changed(self, project: Project, selected: bool):
        """Handle project selection change.

        Args:
            project: The project that was selected/deselected.
            selected: Whether it's now selected.
        """
        path_str = str(project.path)
        if selected:
            self._selected_projects.add(path_str)
        else:
            self._selected_projects.discard(path_str)

    def _on_batch_status_change(self, status: str):
        """Handle batch status change for selected projects.

        Args:
            status: New status ('active', 'hold', 'archived').
        """
        if not self._selected_projects:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more projects first."
            )
            return

        count = len(self._selected_projects)

        # Update each selected project
        for card in self._project_cards:
            if str(card.project.path) in self._selected_projects:
                card.project.status = status
                self.app.update_project(card.project)

        # Clear selection and exit select mode
        self._selected_projects.clear()
        self.toolbar.select_btn.setChecked(False)
        self._on_select_mode_changed(False)

        # Refresh the display
        self.app.load_projects()

        QMessageBox.information(
            self,
            "Status Updated",
            f"Updated {count} project(s) to '{status.replace('hold', 'On Hold').title()}'."
        )

    def _on_mc_batch_status_change(self, status: str):
        """Handle batch status change from Mission Control view.

        Args:
            status: New status ('active', 'hold', 'archived').
        """
        mc = self.mission_control_view
        selected_paths = mc._selected_paths

        if not selected_paths:
            QMessageBox.information(
                self,
                "No Selection",
                "Please select one or more projects first."
            )
            return

        count = len(selected_paths)

        # Update each selected project
        for project in self.app.get_all_projects():
            if str(project.path) in selected_paths:
                project.status = status
                self.app.update_project(project)

        # Clear selection
        mc.clear_selection()

        # Refresh the display
        self.app.load_projects()

        QMessageBox.information(
            self,
            "Status Updated",
            f"Updated {count} project(s) to '{status.replace('hold', 'On Hold').title()}'."
        )
