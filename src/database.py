"""SQLite database handler for project metadata."""

import sqlite3
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from .models.project import Project


class Database:
    """Handles all database operations for the project manager."""

    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection.

        Args:
            db_path: Path to database file. Defaults to user data directory.
        """
        if db_path is None:
            # Default to user's app data directory
            app_data = Path.home() / '.projectmanager'
            app_data.mkdir(exist_ok=True)
            db_path = app_data / 'projects.db'

        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path))
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        """Create database tables if they don't exist."""
        cursor = self.conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                path TEXT UNIQUE NOT NULL,
                languages TEXT,
                status TEXT DEFAULT 'active',
                notes TEXT,
                favorite INTEGER DEFAULT 0,
                last_modified TEXT,
                last_scanned TEXT,
                commands TEXT
            )
        """)

        # Migration: add commands column if it doesn't exist
        cursor.execute("PRAGMA table_info(projects)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'commands' not in columns:
            cursor.execute("ALTER TABLE projects ADD COLUMN commands TEXT")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            )
        """)

        self.conn.commit()

    def close(self):
        """Close the database connection."""
        self.conn.close()

    # Project operations

    def add_project(self, project: Project) -> int:
        """Add a new project to the database.

        Args:
            project: Project to add.

        Returns:
            The ID of the inserted project.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO projects
            (name, path, languages, status, notes, favorite, last_modified, last_scanned, commands)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            project.name,
            str(project.path),
            json.dumps(project.languages),
            project.status,
            project.notes,
            1 if project.favorite else 0,
            project.last_modified.isoformat() if project.last_modified else None,
            datetime.now().isoformat(),
            json.dumps(project.commands)
        ))
        self.conn.commit()
        return cursor.lastrowid

    def update_project(self, project: Project):
        """Update an existing project.

        Args:
            project: Project with updated data.
        """
        cursor = self.conn.cursor()
        cursor.execute("""
            UPDATE projects
            SET name = ?, languages = ?, status = ?, notes = ?,
                favorite = ?, last_modified = ?, last_scanned = ?, commands = ?
            WHERE path = ?
        """, (
            project.name,
            json.dumps(project.languages),
            project.status,
            project.notes,
            1 if project.favorite else 0,
            project.last_modified.isoformat() if project.last_modified else None,
            datetime.now().isoformat(),
            json.dumps(project.commands),
            str(project.path)
        ))
        self.conn.commit()

    def get_project_by_path(self, path: Path) -> Optional[Project]:
        """Get a project by its path.

        Args:
            path: Path to the project directory.

        Returns:
            Project if found, None otherwise.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects WHERE path = ?", (str(path),))
        row = cursor.fetchone()

        if row:
            return self._row_to_project(row)
        return None

    def get_all_projects(self) -> list[Project]:
        """Get all projects from the database.

        Returns:
            List of all projects.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM projects ORDER BY name")
        return [self._row_to_project(row) for row in cursor.fetchall()]

    def delete_project(self, path: Path):
        """Delete a project from the database.

        Args:
            path: Path of the project to delete.
        """
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM projects WHERE path = ?", (str(path),))
        self.conn.commit()

    def get_projects_by_status(self, status: str) -> list[Project]:
        """Get projects filtered by status.

        Args:
            status: Status to filter by ('active', 'hold', 'archived').

        Returns:
            List of matching projects.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM projects WHERE status = ? ORDER BY name",
            (status,)
        )
        return [self._row_to_project(row) for row in cursor.fetchall()]

    def get_projects_by_language(self, language: str) -> list[Project]:
        """Get projects that use a specific language.

        Args:
            language: Language to filter by.

        Returns:
            List of matching projects.
        """
        cursor = self.conn.cursor()
        # Use LIKE to search within the JSON array
        cursor.execute(
            "SELECT * FROM projects WHERE languages LIKE ? ORDER BY name",
            (f'%"{language}"%',)
        )
        return [self._row_to_project(row) for row in cursor.fetchall()]

    def get_all_languages(self) -> list[str]:
        """Get all unique languages from projects.

        Returns:
            List of unique language names.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT languages FROM projects WHERE languages IS NOT NULL")

        languages = set()
        for row in cursor.fetchall():
            if row['languages']:
                try:
                    langs = json.loads(row['languages'])
                    languages.update(langs)
                except json.JSONDecodeError:
                    pass

        return sorted(languages)

    def _row_to_project(self, row: sqlite3.Row) -> Project:
        """Convert a database row to a Project object.

        Args:
            row: Database row.

        Returns:
            Project object.
        """
        languages = []
        if row['languages']:
            try:
                languages = json.loads(row['languages'])
            except json.JSONDecodeError:
                pass

        last_modified = None
        if row['last_modified']:
            try:
                last_modified = datetime.fromisoformat(row['last_modified'])
            except ValueError:
                pass

        commands = []
        if row['commands']:
            try:
                commands = json.loads(row['commands'])
            except json.JSONDecodeError:
                pass

        return Project(
            id=row['id'],
            name=row['name'],
            path=Path(row['path']),
            languages=languages,
            status=row['status'],
            notes=row['notes'] or '',
            favorite=bool(row['favorite']),
            last_modified=last_modified,
            commands=commands
        )

    # Settings operations

    def get_setting(self, key: str, default: str = None) -> Optional[str]:
        """Get a setting value.

        Args:
            key: Setting key.
            default: Default value if not found.

        Returns:
            Setting value or default.
        """
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()

        if row:
            return row['value']
        return default

    def set_setting(self, key: str, value: str):
        """Set a setting value.

        Args:
            key: Setting key.
            value: Setting value.
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value)
        )
        self.conn.commit()

    def get_theme(self) -> str:
        """Get the saved theme ID.

        Returns:
            Theme ID string, defaults to 'dark'.
        """
        return self.get_setting('theme', 'dark')

    def set_theme(self, theme_id: str):
        """Save the selected theme ID.

        Args:
            theme_id: Theme identifier to persist.
        """
        self.set_setting('theme', theme_id)

    def get_scan_directories(self) -> list[Path]:
        """Get configured scan directories.

        Returns:
            List of directory paths to scan.
        """
        value = self.get_setting('scan_directories', '[]')
        try:
            dirs = json.loads(value)
            return [Path(d) for d in dirs]
        except json.JSONDecodeError:
            return []

    def set_scan_directories(self, directories: list[Path]):
        """Set scan directories.

        Args:
            directories: List of directory paths.
        """
        self.set_setting('scan_directories', json.dumps([str(d) for d in directories]))

    def get_editor_command(self) -> str:
        """Get the configured editor command.

        Returns:
            Editor command (defaults to 'code' for VS Code).
        """
        return self.get_setting('editor_command', 'code')

    def set_editor_command(self, command: str):
        """Set the editor command.

        Args:
            command: Editor command to use.
        """
        self.set_setting('editor_command', command)

    def get_active_workspace(self) -> str:
        """Get the active workspace directory for Mission Control.

        Returns:
            Directory path string, or 'all' for all workspaces.
        """
        return self.get_setting('mc_active_workspace', 'all')

    def set_active_workspace(self, workspace: str):
        """Set the active workspace directory for Mission Control.

        Args:
            workspace: Directory path string, or 'all' for all workspaces.
        """
        self.set_setting('mc_active_workspace', workspace)
