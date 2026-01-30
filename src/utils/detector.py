"""Language and framework detection for projects."""

from pathlib import Path
from typing import Optional


# Language detection rules with priority (lower = higher priority)
LANGUAGE_MARKERS = {
    'Python': {
        'files': ['pyproject.toml', 'setup.py', 'requirements.txt', 'Pipfile', 'setup.cfg'],
        'extensions': ['.py'],
        'priority': 1
    },
    'JavaScript': {
        'files': ['package.json'],
        'extensions': ['.js', '.jsx'],
        'priority': 2
    },
    'TypeScript': {
        'files': ['tsconfig.json'],
        'extensions': ['.ts', '.tsx'],
        'priority': 2
    },
    'Rust': {
        'files': ['Cargo.toml'],
        'extensions': ['.rs'],
        'priority': 1
    },
    'Go': {
        'files': ['go.mod', 'go.sum'],
        'extensions': ['.go'],
        'priority': 1
    },
    'Java': {
        'files': ['pom.xml', 'build.gradle', 'build.gradle.kts'],
        'extensions': ['.java'],
        'priority': 2
    },
    'Kotlin': {
        'files': ['build.gradle.kts'],
        'extensions': ['.kt', '.kts'],
        'priority': 2
    },
    'C#': {
        'files': [],
        'extensions': ['.cs', '.csproj', '.sln'],
        'priority': 2
    },
    'C++': {
        'files': ['CMakeLists.txt'],
        'extensions': ['.cpp', '.cxx', '.cc', '.hpp', '.hxx'],
        'priority': 3
    },
    'C': {
        'files': ['Makefile', 'CMakeLists.txt'],
        'extensions': ['.c', '.h'],
        'priority': 4
    },
    'Ruby': {
        'files': ['Gemfile', 'Rakefile'],
        'extensions': ['.rb'],
        'priority': 2
    },
    'PHP': {
        'files': ['composer.json'],
        'extensions': ['.php'],
        'priority': 2
    },
    'Swift': {
        'files': ['Package.swift'],
        'extensions': ['.swift'],
        'priority': 1
    },
    'Dart': {
        'files': ['pubspec.yaml'],
        'extensions': ['.dart'],
        'priority': 1
    },
    'Elixir': {
        'files': ['mix.exs'],
        'extensions': ['.ex', '.exs'],
        'priority': 1
    },
    'Haskell': {
        'files': ['stack.yaml', 'cabal.project'],
        'extensions': ['.hs'],
        'priority': 1
    },
    'Scala': {
        'files': ['build.sbt'],
        'extensions': ['.scala'],
        'priority': 1
    },
    'Lua': {
        'files': [],
        'extensions': ['.lua'],
        'priority': 3
    },
    'Shell': {
        'files': [],
        'extensions': ['.sh', '.bash', '.zsh'],
        'priority': 5
    },
}

# Framework detection (more specific than languages)
FRAMEWORK_MARKERS = {
    'React': {
        'files': ['package.json'],
        'content_check': ('package.json', ['react', 'react-dom']),
    },
    'Vue': {
        'files': ['package.json'],
        'content_check': ('package.json', ['vue']),
    },
    'Angular': {
        'files': ['angular.json'],
        'content_check': None,
    },
    'Next.js': {
        'files': ['next.config.js', 'next.config.mjs', 'next.config.ts'],
        'content_check': None,
    },
    'Django': {
        'files': ['manage.py'],
        'content_check': ('manage.py', ['django']),
    },
    'Flask': {
        'files': [],
        'content_check': ('requirements.txt', ['flask']),
    },
    'FastAPI': {
        'files': [],
        'content_check': ('requirements.txt', ['fastapi']),
    },
    'Rails': {
        'files': ['Gemfile'],
        'content_check': ('Gemfile', ['rails']),
    },
    'Laravel': {
        'files': ['artisan'],
        'content_check': None,
    },
    'Spring': {
        'files': [],
        'content_check': ('pom.xml', ['spring']),
    },
    '.NET': {
        'files': [],
        'extensions': ['.csproj', '.sln'],
        'content_check': None,
    },
    'Flutter': {
        'files': ['pubspec.yaml'],
        'content_check': ('pubspec.yaml', ['flutter']),
    },
    'Electron': {
        'files': ['package.json'],
        'content_check': ('package.json', ['electron']),
    },
    'Tauri': {
        'files': ['tauri.conf.json', 'src-tauri'],
        'content_check': None,
    },
}


def detect_languages(project_path: Path) -> list[str]:
    """Detect programming languages used in a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        List of detected languages, sorted by priority.
    """
    if not project_path.exists():
        return []

    detected = {}  # language -> priority

    # Check for marker files and extensions
    for language, markers in LANGUAGE_MARKERS.items():
        # Check for specific files
        for marker_file in markers.get('files', []):
            if (project_path / marker_file).exists():
                if language not in detected or markers['priority'] < detected[language]:
                    detected[language] = markers['priority']
                break

        # Check for file extensions (scan top-level and src directories)
        extensions = markers.get('extensions', [])
        if extensions and language not in detected:
            if _has_files_with_extensions(project_path, extensions):
                detected[language] = markers['priority']

    # Sort by priority (lower first) and return language names
    sorted_languages = sorted(detected.items(), key=lambda x: x[1])
    return [lang for lang, _ in sorted_languages]


def detect_frameworks(project_path: Path) -> list[str]:
    """Detect frameworks used in a project.

    Args:
        project_path: Path to the project directory.

    Returns:
        List of detected frameworks.
    """
    if not project_path.exists():
        return []

    detected = []

    for framework, markers in FRAMEWORK_MARKERS.items():
        # Check for marker files
        for marker_file in markers.get('files', []):
            marker_path = project_path / marker_file
            if marker_path.exists():
                # If there's a content check, verify it
                if markers.get('content_check'):
                    file_to_check, keywords = markers['content_check']
                    if _file_contains_keywords(project_path / file_to_check, keywords):
                        detected.append(framework)
                        break
                else:
                    detected.append(framework)
                    break

        # Check content-only rules
        if framework not in detected and markers.get('content_check'):
            file_to_check, keywords = markers['content_check']
            check_path = project_path / file_to_check
            if check_path.exists() and _file_contains_keywords(check_path, keywords):
                detected.append(framework)

    return detected


def _has_files_with_extensions(path: Path, extensions: list[str], max_depth: int = 2) -> bool:
    """Check if directory has files with given extensions.

    Args:
        path: Directory to search.
        extensions: List of file extensions to look for.
        max_depth: Maximum directory depth to search.

    Returns:
        True if matching files found.
    """
    def search(current_path: Path, depth: int) -> bool:
        if depth > max_depth:
            return False

        try:
            for item in current_path.iterdir():
                # Skip hidden directories and common non-source directories
                if item.name.startswith('.') or item.name in ('node_modules', 'venv', '__pycache__', 'target', 'build', 'dist'):
                    continue

                if item.is_file():
                    if item.suffix.lower() in extensions:
                        return True
                elif item.is_dir() and depth < max_depth:
                    if search(item, depth + 1):
                        return True
        except PermissionError:
            pass

        return False

    return search(path, 0)


def _file_contains_keywords(file_path: Path, keywords: list[str]) -> bool:
    """Check if a file contains any of the given keywords.

    Args:
        file_path: Path to the file.
        keywords: Keywords to search for.

    Returns:
        True if any keyword is found.
    """
    if not file_path.exists():
        return False

    try:
        content = file_path.read_text(encoding='utf-8').lower()
        return any(keyword.lower() in content for keyword in keywords)
    except (PermissionError, UnicodeDecodeError):
        return False


def get_language_icon(language: str) -> Optional[str]:
    """Get an icon character for a language.

    Args:
        language: Language name.

    Returns:
        Unicode icon character or None.
    """
    # Using simple text abbreviations since we don't have actual icon files
    icons = {
        'Python': 'Py',
        'JavaScript': 'JS',
        'TypeScript': 'TS',
        'Rust': 'Rs',
        'Go': 'Go',
        'Java': 'Jv',
        'Kotlin': 'Kt',
        'C#': 'C#',
        'C++': '++',
        'C': 'C',
        'Ruby': 'Rb',
        'PHP': 'PHP',
        'Swift': 'Sw',
        'Dart': 'Da',
        'Elixir': 'Ex',
        'Haskell': 'Hs',
        'Scala': 'Sc',
        'Lua': 'Lu',
        'Shell': 'Sh',
        'React': 'Re',
        'Vue': 'Vu',
        'Angular': 'Ng',
        'Next.js': 'Nx',
        'Django': 'Dj',
        'Flask': 'Fl',
        'FastAPI': 'FA',
        'Rails': 'Rl',
        'Laravel': 'Lv',
        'Spring': 'Sp',
        '.NET': '.N',
        'Flutter': 'Fl',
        'Electron': 'El',
        'Tauri': 'Ta',
    }
    return icons.get(language)
