"""Main application class."""

import sys
from pathlib import Path
from typing import Optional

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from .database import Database
from .scanner import scan_directories
from .models.project import Project
from .ui.main_window import MainWindow
from .utils.theme import get_dark_theme


class ProjectManagerApp:
    """Main application controller."""

    def __init__(self):
        """Initialize the application."""
        self.app = QApplication(sys.argv)
        self.app.setApplicationName("Project Manager")
        self.app.setApplicationDisplayName("Project Manager")

        # Apply dark theme
        self.app.setStyleSheet(get_dark_theme())

        # Initialize database
        self.db = Database()

        # Create main window
        self.main_window = MainWindow(self)

        # Load projects
        self._projects: list[Project] = []
        self._filtered_projects: list[Project] = []
        self._current_filter = {'status': None, 'language': None, 'search': ''}

    def run(self) -> int:
        """Run the application.

        Returns:
            Exit code.
        """
        self.main_window.show()

        # Load projects after window is shown
        QTimer.singleShot(100, self.load_projects)

        return self.app.exec()

    def load_projects(self):
        """Load projects from database."""
        self._projects = self.db.get_all_projects()
        self._apply_filters()
        self.main_window.update_projects(self._filtered_projects)
        self.main_window.update_language_filters(self.db.get_all_languages())

    def refresh_projects(self):
        """Re-scan directories and refresh project list."""
        scan_dirs = self.db.get_scan_directories()

        if not scan_dirs:
            self.main_window.show_message("No scan directories configured. Please add directories in Settings.")
            return

        # Scan for new projects
        discovered = scan_directories(scan_dirs)

        # Update database
        for project in discovered:
            existing = self.db.get_project_by_path(project.path)
            if existing:
                # Update detected info but keep user data
                project.id = existing.id
                project.status = existing.status
                project.notes = existing.notes
                project.favorite = existing.favorite
                if existing.name != existing.path.name:
                    # Keep custom name
                    project.name = existing.name
                self.db.update_project(project)
            else:
                self.db.add_project(project)

        # Remove projects that no longer exist
        for project in self._projects:
            if not project.exists:
                self.db.delete_project(project.path)

        # Reload
        self.load_projects()
        self.main_window.show_message(f"Found {len(discovered)} projects.")

    def get_projects(self) -> list[Project]:
        """Get the current filtered project list.

        Returns:
            List of filtered projects.
        """
        return self._filtered_projects

    def get_all_projects(self) -> list[Project]:
        """Get all projects.

        Returns:
            List of all projects.
        """
        return self._projects

    def filter_by_status(self, status: Optional[str]):
        """Filter projects by status.

        Args:
            status: Status to filter by, or None for all.
        """
        self._current_filter['status'] = status
        self._apply_filters()
        self.main_window.update_projects(self._filtered_projects)

    def filter_by_language(self, language: Optional[str]):
        """Filter projects by language.

        Args:
            language: Language to filter by, or None for all.
        """
        self._current_filter['language'] = language
        self._apply_filters()
        self.main_window.update_projects(self._filtered_projects)

    def search_projects(self, query: str):
        """Search projects by name.

        Args:
            query: Search query.
        """
        self._current_filter['search'] = query.lower()
        self._apply_filters()
        self.main_window.update_projects(self._filtered_projects)

    def _apply_filters(self):
        """Apply all current filters to the project list."""
        filtered = self._projects

        # Filter by status
        status = self._current_filter['status']
        if status:
            filtered = [p for p in filtered if p.status == status]

        # Filter by language
        language = self._current_filter['language']
        if language:
            filtered = [p for p in filtered if language in p.languages]

        # Filter by search query
        search = self._current_filter['search']
        if search:
            filtered = [p for p in filtered if search in p.name.lower()]

        # Sort by favorites first, then by most recent
        from datetime import datetime
        filtered.sort(
            key=lambda p: (
                not p.favorite,  # False (favorite) sorts before True (not favorite)
                -(p.last_modified.timestamp() if p.last_modified else 0)  # Newer first
            )
        )

        self._filtered_projects = filtered

    def update_project(self, project: Project):
        """Update a project's metadata.

        Args:
            project: Project with updated data.
        """
        self.db.update_project(project)

        # Update local cache
        for i, p in enumerate(self._projects):
            if p.path == project.path:
                self._projects[i] = project
                break

        self._apply_filters()
        self.main_window.update_projects(self._filtered_projects)
        self.main_window.update_language_filters(self.db.get_all_languages())

    def get_scan_directories(self) -> list[Path]:
        """Get configured scan directories.

        Returns:
            List of scan directories.
        """
        return self.db.get_scan_directories()

    def set_scan_directories(self, directories: list[Path]):
        """Set scan directories.

        Args:
            directories: List of directories.
        """
        self.db.set_scan_directories(directories)

    def get_editor_command(self) -> str:
        """Get the configured editor command.

        Returns:
            Editor command.
        """
        return self.db.get_editor_command()

    def set_editor_command(self, command: str):
        """Set the editor command.

        Args:
            command: Editor command.
        """
        self.db.set_editor_command(command)

    def cleanup(self):
        """Clean up resources."""
        self.db.close()
