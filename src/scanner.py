"""Project directory scanner."""

import os
from pathlib import Path
from datetime import datetime
from typing import Generator, Optional

from .models.project import Project
from .utils.detector import detect_languages, detect_frameworks


# Markers that indicate a directory is a project root
PROJECT_MARKERS = [
    '.git',
    'package.json',
    'Cargo.toml',
    'pyproject.toml',
    'setup.py',
    'requirements.txt',
    'go.mod',
    'pom.xml',
    'build.gradle',
    'build.gradle.kts',
    'Makefile',
    'CMakeLists.txt',
    'Gemfile',
    'composer.json',
    'pubspec.yaml',
    'mix.exs',
    'stack.yaml',
    'Package.swift',
]

# File patterns that indicate a project
PROJECT_FILE_PATTERNS = [
    '*.sln',
    '*.csproj',
]

# Directories to skip when scanning
SKIP_DIRECTORIES = {
    'node_modules',
    'venv',
    '.venv',
    'env',
    '.env',
    '__pycache__',
    '.git',
    '.svn',
    '.hg',
    'target',
    'build',
    'dist',
    'out',
    'bin',
    'obj',
    '.idea',
    '.vscode',
    '.vs',
    'vendor',
    'packages',
    '.cache',
    '.tox',
    '.mypy_cache',
    '.pytest_cache',
    'coverage',
    '.coverage',
    'htmlcov',
    'sdk',
    'lib',
    'libs',
    'third_party',
    'external',
    'deps',
    'dependencies',
}


class ProjectScanner:
    """Scans directories to discover programming projects."""

    def __init__(self, max_depth: int = 5):
        """Initialize the scanner.

        Args:
            max_depth: Maximum directory depth to scan.
        """
        self.max_depth = max_depth

    def scan_directory(self, root_path: Path) -> Generator[Project, None, None]:
        """Scan a directory for projects.

        Args:
            root_path: Root directory to scan.

        Yields:
            Project objects for each discovered project.
        """
        if not root_path.exists() or not root_path.is_dir():
            return

        # Direct children of scan directories are always treated as projects
        try:
            for item in root_path.iterdir():
                if item.is_dir() and not self._should_skip(item):
                    # Always create a project for direct children
                    project = self._create_project(item)
                    if project:
                        yield project
        except PermissionError:
            pass

    def _scan_recursive(self, path: Path, depth: int) -> Generator[Project, None, None]:
        """Recursively scan for projects.

        Args:
            path: Current directory path.
            depth: Current depth level.

        Yields:
            Project objects.
        """
        if depth > self.max_depth:
            return

        # Check if current directory is a project
        if self._is_project(path):
            project = self._create_project(path)
            if project:
                yield project
            # Don't scan subdirectories of a project
            return

        # Scan subdirectories
        try:
            for item in path.iterdir():
                if item.is_dir() and not self._should_skip(item):
                    yield from self._scan_recursive(item, depth + 1)
        except PermissionError:
            pass

    def _is_project(self, path: Path) -> bool:
        """Check if a directory is a project root.

        Args:
            path: Directory to check.

        Returns:
            True if it's a project root.
        """
        # Check for marker files/directories
        for marker in PROJECT_MARKERS:
            if (path / marker).exists():
                return True

        # Check for file patterns
        try:
            for pattern in PROJECT_FILE_PATTERNS:
                if list(path.glob(pattern)):
                    return True
        except PermissionError:
            pass

        return False

    def _should_skip(self, path: Path) -> bool:
        """Check if a directory should be skipped.

        Args:
            path: Directory to check.

        Returns:
            True if it should be skipped.
        """
        name = path.name

        # Skip hidden directories
        if name.startswith('.'):
            return True

        # Skip known non-project directories
        if name.lower() in SKIP_DIRECTORIES:
            return True

        return False

    def _create_project(self, path: Path) -> Optional[Project]:
        """Create a Project object from a directory.

        Args:
            path: Project directory path.

        Returns:
            Project object or None if creation fails.
        """
        try:
            # Get project name from directory name
            name = path.name

            # Detect languages
            languages = detect_languages(path)

            # Also detect frameworks and add them to the list
            frameworks = detect_frameworks(path)
            for framework in frameworks:
                if framework not in languages:
                    languages.append(framework)

            # Get last modified time
            last_modified = self._get_last_modified(path)

            return Project(
                name=name,
                path=path,
                languages=languages,
                last_modified=last_modified
            )
        except Exception:
            return None

    def _get_last_modified(self, path: Path) -> Optional[datetime]:
        """Get the most recent modification time for a project.

        Args:
            path: Project directory.

        Returns:
            Most recent modification datetime.
        """
        try:
            # Get the most recent modification time from key files
            most_recent = None

            # Check common files that indicate recent activity
            check_files = [
                '.git/FETCH_HEAD',
                '.git/index',
                'package.json',
                'Cargo.toml',
                'pyproject.toml',
                'go.mod',
            ]

            for file_name in check_files:
                file_path = path / file_name
                if file_path.exists():
                    mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if most_recent is None or mtime > most_recent:
                        most_recent = mtime

            # Fall back to directory modification time
            if most_recent is None:
                most_recent = datetime.fromtimestamp(path.stat().st_mtime)

            return most_recent
        except Exception:
            return None


def scan_directories(directories: list[Path], max_depth: int = 5) -> list[Project]:
    """Scan multiple directories for projects.

    Args:
        directories: List of directories to scan.
        max_depth: Maximum depth to scan.

    Returns:
        List of discovered projects.
    """
    scanner = ProjectScanner(max_depth=max_depth)
    projects = []
    seen_paths = set()

    for directory in directories:
        for project in scanner.scan_directory(directory):
            # Avoid duplicates
            if project.path not in seen_paths:
                seen_paths.add(project.path)
                projects.append(project)

    return projects
