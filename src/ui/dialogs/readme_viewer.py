"""README viewer dialog with GitHub-style markdown rendering."""

import os
from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout, QLabel
)
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

import markdown


class ReadmeViewerDialog(QDialog):
    """Dialog for viewing README files with GitHub-style markdown rendering."""

    def __init__(self, project_path: Path, parent=None):
        """Initialize the README viewer dialog.

        Args:
            project_path: Path to the project directory.
        """
        super().__init__(parent)
        self._project_path = project_path
        self._readme_path = self._find_readme()

        self.setWindowTitle(f"README - {project_path.name}")
        self.setMinimumSize(800, 600)
        self.resize(900, 700)
        self._setup_ui()

    def _find_readme(self) -> Path | None:
        """Find README file in the project directory.

        Returns:
            Path to README file or None if not found.
        """
        readme_names = [
            'README.md', 'readme.md', 'Readme.md',
            'README.MD', 'README', 'readme'
        ]

        for name in readme_names:
            readme_path = self._project_path / name
            if readme_path.exists():
                return readme_path
        return None

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = QHBoxLayout()
        header.setContentsMargins(16, 12, 16, 12)

        if self._readme_path:
            path_label = QLabel(str(self._readme_path.relative_to(self._project_path)))
        else:
            path_label = QLabel("No README found")
        path_label.setStyleSheet("color: #808080; font-size: 12px;")
        header.addWidget(path_label)
        header.addStretch()

        layout.addLayout(header)

        # Markdown viewer
        self.browser = QTextBrowser()
        self.browser.setOpenExternalLinks(False)
        self.browser.anchorClicked.connect(self._handle_link)
        self.browser.setStyleSheet(self._get_browser_stylesheet())
        layout.addWidget(self.browser)

        # Load and render content
        self._load_readme()

        # Footer with close button
        footer = QHBoxLayout()
        footer.setContentsMargins(16, 12, 16, 12)
        footer.addStretch()

        close_btn = QPushButton("Close")
        close_btn.setObjectName("primaryButton")
        close_btn.clicked.connect(self.accept)
        footer.addWidget(close_btn)

        layout.addLayout(footer)

    def _load_readme(self):
        """Load and render the README content."""
        if not self._readme_path:
            self.browser.setHtml(self._wrap_html(
                '<p style="color: #808080; text-align: center; padding: 40px;">'
                'No README.md file found in this project.</p>'
            ))
            return

        try:
            with open(self._readme_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Convert markdown to HTML with extensions
            html = markdown.markdown(
                content,
                extensions=[
                    'fenced_code',
                    'tables',
                    'toc',
                    'nl2br',
                    'sane_lists',
                ]
            )

            # Process relative image paths
            html = self._process_images(html)

            self.browser.setHtml(self._wrap_html(html))

        except Exception as e:
            self.browser.setHtml(self._wrap_html(
                f'<p style="color: #ff6b6b;">Error reading README: {e}</p>'
            ))

    def _process_images(self, html: str) -> str:
        """Convert relative image paths to absolute file:// URLs.

        Args:
            html: HTML content with potentially relative image paths.

        Returns:
            HTML with absolute image paths.
        """
        import re

        def replace_src(match):
            src = match.group(1)
            # Skip if already absolute URL
            if src.startswith(('http://', 'https://', 'file://')):
                return match.group(0)

            # Convert relative path to absolute
            abs_path = self._project_path / src
            if abs_path.exists():
                return f'src="file:///{abs_path.as_posix()}"'
            return match.group(0)

        return re.sub(r'src="([^"]+)"', replace_src, html)

    def _handle_link(self, url: QUrl):
        """Handle clicked links.

        Args:
            url: The URL that was clicked.
        """
        url_str = url.toString()

        # Handle external links
        if url_str.startswith(('http://', 'https://')):
            QDesktopServices.openUrl(url)
        # Handle local file links
        elif url_str.startswith('file://'):
            QDesktopServices.openUrl(url)
        # Handle relative links
        else:
            local_path = self._project_path / url_str
            if local_path.exists():
                QDesktopServices.openUrl(QUrl.fromLocalFile(str(local_path)))

    def _wrap_html(self, content: str) -> str:
        """Wrap HTML content with styling.

        Args:
            content: HTML content to wrap.

        Returns:
            Complete HTML document with styling.
        """
        return f'''
<!DOCTYPE html>
<html>
<head>
    <style>
        {self._get_github_css()}
    </style>
</head>
<body>
    <div class="markdown-body">
        {content}
    </div>
</body>
</html>
'''

    def _get_browser_stylesheet(self) -> str:
        """Get stylesheet for the QTextBrowser widget."""
        return '''
            QTextBrowser {
                background-color: #1e1e1e;
                border: none;
                padding: 20px;
            }
        '''

    def _get_github_css(self) -> str:
        """Get GitHub-style markdown CSS for dark theme."""
        return '''
            body {
                background-color: #1e1e1e;
                color: #e6edf3;
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Noto Sans", Helvetica, Arial, sans-serif;
                font-size: 14px;
                line-height: 1.6;
                margin: 0;
                padding: 20px;
            }

            .markdown-body {
                max-width: 900px;
                margin: 0 auto;
            }

            h1, h2, h3, h4, h5, h6 {
                color: #e6edf3;
                font-weight: 600;
                margin-top: 24px;
                margin-bottom: 16px;
                line-height: 1.25;
            }

            h1 {
                font-size: 2em;
                padding-bottom: 0.3em;
                border-bottom: 1px solid #3c3c3c;
            }

            h2 {
                font-size: 1.5em;
                padding-bottom: 0.3em;
                border-bottom: 1px solid #3c3c3c;
            }

            h3 { font-size: 1.25em; }
            h4 { font-size: 1em; }
            h5 { font-size: 0.875em; }
            h6 { font-size: 0.85em; color: #8b949e; }

            p {
                margin-top: 0;
                margin-bottom: 16px;
            }

            a {
                color: #58a6ff;
                text-decoration: none;
            }

            a:hover {
                text-decoration: underline;
            }

            code {
                background-color: #343942;
                padding: 0.2em 0.4em;
                border-radius: 6px;
                font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, monospace;
                font-size: 85%;
            }

            pre {
                background-color: #2d2d2d;
                border: 1px solid #3c3c3c;
                border-radius: 6px;
                padding: 16px;
                overflow: auto;
                font-size: 85%;
                line-height: 1.45;
                margin-top: 0;
                margin-bottom: 16px;
            }

            pre code {
                background-color: transparent;
                padding: 0;
                border-radius: 0;
                font-size: 100%;
            }

            blockquote {
                color: #8b949e;
                border-left: 4px solid #3c3c3c;
                padding: 0 16px;
                margin: 0 0 16px 0;
            }

            ul, ol {
                margin-top: 0;
                margin-bottom: 16px;
                padding-left: 2em;
            }

            li {
                margin-top: 4px;
            }

            li + li {
                margin-top: 4px;
            }

            hr {
                height: 4px;
                padding: 0;
                margin: 24px 0;
                background-color: #3c3c3c;
                border: 0;
            }

            table {
                border-collapse: collapse;
                margin-top: 0;
                margin-bottom: 16px;
                width: 100%;
            }

            table th, table td {
                padding: 6px 13px;
                border: 1px solid #3c3c3c;
            }

            table th {
                font-weight: 600;
                background-color: #2d2d2d;
            }

            table tr {
                background-color: #1e1e1e;
            }

            table tr:nth-child(2n) {
                background-color: #252526;
            }

            img {
                max-width: 100%;
                height: auto;
                border-radius: 6px;
            }

            strong {
                font-weight: 600;
            }

            em {
                font-style: italic;
            }

            .task-list-item {
                list-style-type: none;
            }

            .task-list-item input {
                margin-right: 8px;
            }
        '''


def find_readme_in_project(project_path: Path) -> Path | None:
    """Check if a README file exists in the project.

    Args:
        project_path: Path to the project directory.

    Returns:
        Path to README file if found, None otherwise.
    """
    readme_names = [
        'README.md', 'readme.md', 'Readme.md',
        'README.MD', 'README', 'readme'
    ]

    for name in readme_names:
        readme_path = project_path / name
        if readme_path.exists():
            return readme_path
    return None
