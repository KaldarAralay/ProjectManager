"""Check if project folders are open in terminals or editors."""

import subprocess
import platform
import re
import ctypes
from pathlib import Path


def get_open_projects_by_window_titles() -> dict[str, bool]:
    """Get a dict mapping folder names to open status based on window titles.

    Returns:
        Dict mapping lowercase folder names to True if they appear in a window title.
    """
    open_names = {}

    if platform.system() != 'Windows':
        return open_names

    try:
        # Use Windows API to enumerate windows and get titles
        titles = _get_all_window_titles()

        for title in titles:
            if not title:
                continue

            title_lower = title.lower()

            # Skip known non-project windows
            skip_words = ['discord', 'chrome', 'firefox', 'edge', 'spotify',
                         'slack', 'teams', 'outlook', 'telegram', 'whatsapp',
                         'settings', 'calculator', 'photos', 'movies']
            if any(w in title_lower for w in skip_words):
                continue

            # VS Code: "foldername - Visual Studio Code"
            if 'visual studio code' in title_lower:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    name = parts[0].strip().lower()
                    # Remove unsaved indicator
                    name = name.lstrip('● ').strip()
                    if name and len(name) > 1:
                        open_names[name] = True
                continue

            # Cursor: "foldername - Cursor"
            if ' - cursor' in title_lower:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    name = parts[0].strip().lower()
                    name = name.lstrip('● ').strip()
                    if name and len(name) > 1:
                        open_names[name] = True
                continue

            # File Explorer: "foldername - File Explorer"
            if 'file explorer' in title_lower:
                parts = title.split(' - ')
                if len(parts) >= 2:
                    name = parts[0].strip().lower()
                    if name and len(name) > 1:
                        open_names[name] = True
                continue

            # Windows Terminal often shows path
            if 'windows terminal' in title_lower or title_lower.startswith('administrator:'):
                paths = re.findall(r'([A-Za-z]:\\[^<>"|?*\n]+)', title)
                for p in paths:
                    p = p.strip().rstrip('\\>')
                    try:
                        path = Path(p)
                        if path.exists() and path.is_dir():
                            open_names[path.name.lower()] = True
                    except:
                        pass
                continue

            # File Explorer shows folder name or path
            paths = re.findall(r'([A-Za-z]:\\[^<>"|?*\n]+)', title)
            for p in paths:
                p = p.strip().rstrip('\\')
                try:
                    path = Path(p)
                    if path.exists() and path.is_dir():
                        open_names[path.name.lower()] = True
                except:
                    pass

    except Exception:
        pass

    return open_names


def _get_all_window_titles() -> list[str]:
    """Get all visible window titles using Windows API.

    Returns:
        List of window title strings.
    """
    titles = []

    try:
        import ctypes
        from ctypes import wintypes

        user32 = ctypes.windll.user32

        # Callback function type
        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

        def enum_callback(hwnd, lparam):
            if user32.IsWindowVisible(hwnd):
                length = user32.GetWindowTextLengthW(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    user32.GetWindowTextW(hwnd, buff, length + 1)
                    if buff.value:
                        titles.append(buff.value)
            return True

        user32.EnumWindows(WNDENUMPROC(enum_callback), 0)

    except Exception:
        pass

    return titles


def is_project_open(project_path: Path, open_names: dict[str, bool] | None = None) -> bool:
    """Check if a specific project is open.

    Args:
        project_path: Path to the project.
        open_names: Pre-fetched dict of open names (for efficiency).

    Returns:
        True if the project appears to be open.
    """
    if open_names is None:
        open_names = get_open_projects_by_window_titles()

    return project_path.name.lower() in open_names
