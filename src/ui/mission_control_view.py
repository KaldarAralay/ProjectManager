"""Mission Control themed dashboard view."""

import time
from datetime import datetime
from collections import Counter

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QProgressBar, QMenu, QPushButton
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from ..models.project import Project

# Mission Control palette
_GREEN = "#4ade80"
_BLUE = "#60a5fa"
_BLUE_DIM = "#3d6e8f"
_BLUE_DARK = "#1a3152"
_AMBER = "#fbbf24"
_PANEL_BG = "#0f1923"
_PANEL_BORDER = "#1a3152"
_BG = "#0a0e17"
_STYLE_BASE = "background: transparent; border: none;"

# Scrollbar style: dark track, lighter handle
_SCROLLBAR_STYLE = f"""
    QScrollArea {{ background: transparent; border: none; }}
    QScrollBar:vertical {{
        background-color: {_BG};
        width: 10px;
        border: none;
    }}
    QScrollBar::handle:vertical {{
        background-color: {_BLUE_DIM};
        min-height: 30px;
        border-radius: 5px;
        margin: 2px;
    }}
    QScrollBar::handle:vertical:hover {{
        background-color: {_BLUE};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
"""

# Known language colors for the bar chart
_LANG_COLORS = {
    'JavaScript': '#f7df1e', 'TypeScript': '#3178c6',
    'Python': '#3776ab', 'React': '#61dafb',
    'Java': '#ed8b00', 'C#': '#239120',
    'C++': '#00599C', 'Go': '#00ADD8',
    'Rust': '#dea584', 'Ruby': '#CC342D',
    'HTML': '#e34c26', 'CSS': '#1572B6',
}


def _elapsed_str(dt):
    if dt is None:
        return "T+???"
    delta = datetime.now() - dt
    hours = int(delta.total_seconds() / 3600)
    if hours < 1:
        return "T+<1 hour ago"
    if hours < 24:
        return f"T+{hours} hours ago"
    if delta.days == 1:
        return "T+Yesterday"
    return f"T+{delta.days} days ago"


def _label(text, color=_GREEN, size=11, bold=False, align=None):
    """Create a styled QLabel with transparent background."""
    lbl = QLabel(text)
    weight = "bold" if bold else "normal"
    lbl.setStyleSheet(
        f"color: {color}; font-size: {size}px; font-weight: {weight}; {_STYLE_BASE}"
    )
    if align:
        lbl.setAlignment(align)
    return lbl


def _panel_style():
    return (
        f"background-color: {_PANEL_BG}; "
        f"border: 1px solid {_PANEL_BORDER}; "
        f"border-radius: 4px;"
    )


def _mc_button(text):
    """Create a small themed button for the status bar."""
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"QPushButton {{ color: {_BLUE_DIM}; background: transparent; "
        f"border: 1px solid {_BLUE_DARK}; border-radius: 3px; "
        f"padding: 2px 8px; font-size: 10px; }}"
        f"QPushButton:hover {{ color: {_GREEN}; border-color: {_GREEN}; }}"
    )
    return btn


class _ContainedScrollArea(QScrollArea):
    """A QScrollArea that never propagates wheel events to its parent."""

    def wheelEvent(self, event):
        # Always accept so the event never bubbles up to the outer scroll area
        event.accept()
        sb = self.verticalScrollBar()
        delta = event.angleDelta().y()
        if delta != 0:
            sb.setValue(sb.value() - delta)


class MissionControlView(QWidget):
    """NASA Mission Control themed project dashboard."""

    # Project action signals (matching ProjectCard signals)
    open_clicked = pyqtSignal(object)
    details_clicked = pyqtSignal(object)
    open_folder_clicked = pyqtSignal(object)
    open_terminal_clicked = pyqtSignal(object)
    open_claude_clicked = pyqtSignal(object)
    run_command_clicked = pyqtSignal(object, dict)
    view_readme_clicked = pyqtSignal(object)

    # Global action signals
    settings_requested = pyqtSignal()
    refresh_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[Project] = []
        self._met_start = time.time()

        font = QFont("Consolas")
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)

        self._setup_ui()

        self._met_timer = QTimer(self)
        self._met_timer.timeout.connect(self._update_met)
        self._met_timer.start(1000)

    def _setup_ui(self):
        main = QVBoxLayout(self)
        main.setContentsMargins(16, 8, 16, 8)
        main.setSpacing(8)

        # === Status bar ===
        status_bar = QHBoxLayout()

        # Left: systems nominal
        left = QHBoxLayout()
        left.setSpacing(6)
        left.addWidget(_label("\u25cf", _GREEN, 14))
        left.addWidget(_label("SYSTEMS NOMINAL", _GREEN, 11))
        left.addStretch()
        status_bar.addLayout(left, 1)

        # Center: title
        status_bar.addWidget(
            _label("MISSION CONTROL", _BLUE_DIM, 18, align=Qt.AlignmentFlag.AlignCenter),
            2,
        )

        # Right: buttons + MET
        right_bar = QHBoxLayout()
        right_bar.setSpacing(8)
        right_bar.addStretch()

        refresh_btn = _mc_button("\u21bb Refresh")
        refresh_btn.clicked.connect(self.refresh_requested.emit)
        right_bar.addWidget(refresh_btn)

        settings_btn = _mc_button("\u2699 Settings")
        settings_btn.clicked.connect(self.settings_requested.emit)
        right_bar.addWidget(settings_btn)

        self._met_label = _label(
            "MET: 000:00:00:00", _BLUE_DIM, 11,
            align=Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
        )
        right_bar.addWidget(self._met_label)
        status_bar.addLayout(right_bar, 1)

        main.addLayout(status_bar)

        # Divider
        div = QFrame()
        div.setFixedHeight(1)
        div.setStyleSheet(f"background-color: {_BLUE_DARK}; border: none;")
        main.addWidget(div)

        # === Scrollable content ===
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(_SCROLLBAR_STYLE)
        main.addWidget(self._scroll, 1)

        # === Footer ===
        footer = QHBoxLayout()
        footer.addWidget(_label("HOUSTON \u2022 CAPCOM", _BLUE_DIM, 10))
        footer.addStretch()
        self._uplink_label = _label("", _BLUE_DIM, 10)
        footer.addWidget(self._uplink_label)
        footer.addWidget(_label("SIGNAL: STRONG", _BLUE_DIM, 10))
        main.addLayout(footer)

    # ------------------------------------------------------------------
    # MET timer
    # ------------------------------------------------------------------

    def _update_met(self):
        elapsed = int(time.time() - self._met_start)
        d, rem = divmod(elapsed, 86400)
        h, rem = divmod(rem, 3600)
        m, s = divmod(rem, 60)
        self._met_label.setText(f"MET: {d:03d}:{h:02d}:{m:02d}:{s:02d}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update_projects(self, projects: list[Project]):
        self._projects = list(projects)
        self._rebuild()

    # ------------------------------------------------------------------
    # Project context menu (matches ProjectCard)
    # ------------------------------------------------------------------

    def _show_project_menu(self, project: Project, global_pos):
        """Show the right-click context menu for a project."""
        from .dialogs.readme_viewer import find_readme_in_project

        menu = QMenu(self)

        open_action = menu.addAction("Open Folder")
        open_action.triggered.connect(lambda: self.open_folder_clicked.emit(project))

        terminal_action = menu.addAction("Open Terminal")
        terminal_action.triggered.connect(lambda: self.open_terminal_clicked.emit(project))

        claude_action = menu.addAction("Open in Claude Code")
        claude_action.triggered.connect(lambda: self.open_claude_clicked.emit(project))

        if find_readme_in_project(project.path):
            menu.addSeparator()
            readme_action = menu.addAction("View README")
            readme_action.triggered.connect(lambda: self.view_readme_clicked.emit(project))

        menu.addSeparator()

        details_action = menu.addAction("Edit Details")
        details_action.triggered.connect(lambda: self.details_clicked.emit(project))

        if project.commands:
            menu.addSeparator()
            commands_menu = menu.addMenu("Custom Commands")
            for cmd in project.commands:
                action = commands_menu.addAction(cmd['name'])
                action.triggered.connect(
                    lambda checked, c=cmd: self.run_command_clicked.emit(project, c)
                )

        menu.exec(global_pos)

    # ------------------------------------------------------------------
    # Content rebuild
    # ------------------------------------------------------------------

    def _rebuild(self):
        projects = self._projects
        primary = [p for p in projects if p.favorite]
        secondary = [p for p in projects if not p.favorite]

        content = QWidget()
        content.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 8, 0, 0)
        layout.setSpacing(12)

        # --- Main split: primary (left) | info panels (right) ---
        top = QHBoxLayout()
        top.setSpacing(12)
        top.addWidget(self._build_primary(primary), 3)

        right_col = QVBoxLayout()
        right_col.setSpacing(12)

        info_row = QHBoxLayout()
        info_row.setSpacing(12)
        info_row.addWidget(self._build_gauge())
        info_row.addWidget(self._build_languages())
        right_col.addLayout(info_row)

        right_col.addWidget(self._build_log())
        top.addLayout(right_col, 2)

        top_w = QWidget()
        top_w.setStyleSheet("background: transparent;")
        top_w.setLayout(top)
        layout.addWidget(top_w)

        # --- Secondary missions ---
        if secondary:
            layout.addWidget(self._build_secondary(secondary))

        layout.addStretch()

        # Swap into scroll area
        old = self._scroll.takeWidget()
        if old:
            old.deleteLater()
        self._scroll.setWidget(content)

        # Update uplink bar
        self._update_uplink()

    # ------------------------------------------------------------------
    # Panel builders
    # ------------------------------------------------------------------

    def _make_panel(self, title: str) -> tuple[QFrame, QVBoxLayout]:
        """Return a styled panel frame and its inner layout."""
        panel = QFrame()
        panel.setStyleSheet(_panel_style())
        inner = QVBoxLayout(panel)
        inner.setContentsMargins(12, 8, 12, 8)
        inner.setSpacing(8)
        inner.addWidget(_label(title, _BLUE_DIM, 10))
        return panel, inner

    # --- Primary display ---

    def _build_primary(self, projects):
        panel, inner = self._make_panel("PRIMARY DISPLAY \u2014 ACTIVE MISSIONS")

        if not projects:
            inner.addWidget(
                _label("No active missions", _BLUE_DIM, 12,
                       align=Qt.AlignmentFlag.AlignCenter)
            )
            inner.addStretch()
            return panel

        # Scrollable list of favorited projects (contained — won't bleed into outer scroll)
        scroll = _ContainedScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(_SCROLLBAR_STYLE)

        rows_widget = QWidget()
        rows_widget.setStyleSheet("background: transparent;")
        rows_layout = QVBoxLayout(rows_widget)
        rows_layout.setContentsMargins(0, 0, 0, 0)
        rows_layout.setSpacing(8)
        for p in projects:
            rows_layout.addWidget(self._make_row(p))
        rows_layout.addStretch()

        scroll.setWidget(rows_widget)
        inner.addWidget(scroll)
        return panel

    def _make_row(self, project: Project) -> QFrame:
        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        row.setStyleSheet(
            "QFrame { background-color: rgba(30,58,95,0.3); "
            "border: 1px solid transparent; border-radius: 4px; }"
            "QFrame:hover { background-color: rgba(30,58,95,0.5); }"
        )
        h = QHBoxLayout(row)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(8)

        h.addWidget(_label("\u25cf", _GREEN, 10))

        info = QVBoxLayout()
        info.setSpacing(2)
        info.addWidget(_label(project.name, _GREEN, 13, bold=True))
        langs_text = " / ".join(project.languages) if project.languages else "Unknown"
        info.addWidget(_label(langs_text, _BLUE_DIM, 10))
        h.addLayout(info, 1)

        right = QVBoxLayout()
        right.setAlignment(Qt.AlignmentFlag.AlignRight)
        right.addWidget(
            _label(_elapsed_str(project.last_modified), _BLUE_DIM, 10,
                   align=Qt.AlignmentFlag.AlignRight)
        )
        if project.favorite:
            right.addWidget(
                _label("\u2605 PRI", _AMBER, 10, align=Qt.AlignmentFlag.AlignRight)
            )
        h.addLayout(right)

        # Left-click opens folder, right-click shows context menu
        row.mousePressEvent = lambda e, p=project: self._on_row_click(e, p)
        return row

    def _on_row_click(self, event, project: Project):
        """Handle mouse clicks on a project row."""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_project_menu(project, event.globalPosition().toPoint())
        else:
            self.open_clicked.emit(project)

    # --- Projects gauge ---

    def _build_gauge(self):
        panel, inner = self._make_panel("PROJECTS")
        total = len(self._projects)
        active = sum(1 for p in self._projects if p.status == "active")

        inner.addWidget(
            _label(str(total), _GREEN, 36, bold=True,
                   align=Qt.AlignmentFlag.AlignCenter)
        )
        inner.addWidget(
            _label("TOTAL", _GREEN, 10, align=Qt.AlignmentFlag.AlignCenter)
        )

        bar = QProgressBar()
        bar.setRange(0, max(total, 1))
        bar.setValue(active)
        bar.setTextVisible(False)
        bar.setFixedHeight(8)
        bar.setStyleSheet(
            f"QProgressBar {{ background-color: {_BLUE_DARK}; border: none; border-radius: 4px; }}"
            f"QProgressBar::chunk {{ background-color: {_GREEN}; border-radius: 4px; }}"
        )
        inner.addWidget(bar)

        inner.addWidget(
            _label(f"{active} ACTIVE / {total - active} IDLE", _BLUE_DIM, 10,
                   align=Qt.AlignmentFlag.AlignCenter)
        )
        inner.addStretch()
        return panel

    # --- Languages ---

    def _build_languages(self):
        panel, inner = self._make_panel("LANGUAGES")
        counts = Counter()
        for p in self._projects:
            for lang in p.languages:
                counts[lang] += 1

        top = counts.most_common(5)
        max_val = top[0][1] if top else 1

        for lang, count in top:
            row = QHBoxLayout()
            row.setSpacing(6)
            color = _LANG_COLORS.get(lang, _BLUE)
            bar = QProgressBar()
            bar.setRange(0, max_val)
            bar.setValue(count)
            bar.setTextVisible(False)
            bar.setFixedHeight(6)
            bar.setStyleSheet(
                f"QProgressBar {{ background-color: {_BLUE_DARK}; border: none; border-radius: 3px; }}"
                f"QProgressBar::chunk {{ background-color: {color}; border-radius: 3px; }}"
            )
            row.addWidget(bar, 1)
            row.addWidget(_label(lang[:3], _BLUE_DIM, 10))
            inner.addLayout(row)

        if not top:
            inner.addWidget(_label("No data", _BLUE_DIM, 10))

        inner.addStretch()
        return panel

    # --- Mission log ---

    def _build_log(self):
        panel, inner = self._make_panel("MISSION LOG")
        actions = [
            "commit pushed", "build successful",
            "dependencies updated", "scan completed",
        ]
        recent = sorted(
            [p for p in self._projects if p.last_modified],
            key=lambda p: p.last_modified, reverse=True,
        )[:4]

        for i, p in enumerate(recent):
            ts = p.last_modified.strftime("%H:%M:%S")
            action = actions[i % len(actions)]
            color = _AMBER if p.status == "hold" else _GREEN
            entry = QLabel(
                f'<span style="color:{_BLUE_DIM};">[{ts}]</span> '
                f'<span style="color:{color};">{p.name}</span> '
                f'<span style="color:{_BLUE_DIM};">\u2014 {action}</span>'
            )
            entry.setTextFormat(Qt.TextFormat.RichText)
            entry.setStyleSheet(f"font-size: 11px; {_STYLE_BASE}")
            inner.addWidget(entry)

        if not recent:
            inner.addWidget(_label("No log entries", _BLUE_DIM, 10))

        inner.addStretch()
        return panel

    # --- Secondary missions ---

    def _build_secondary(self, projects):
        panel, inner = self._make_panel("SECONDARY MISSIONS")
        grid = QGridLayout()
        grid.setSpacing(8)
        cols = 4
        for i, p in enumerate(projects):
            tile = QFrame()
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            tile.setStyleSheet(
                f"QFrame {{ background-color: rgba(30,58,95,0.3); "
                f"border: 1px solid {_PANEL_BORDER}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(30,58,95,0.5); }}"
            )
            tl = QVBoxLayout(tile)
            tl.setContentsMargins(8, 8, 8, 8)
            tl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            tl.addWidget(
                _label(p.name, _GREEN, 11, align=Qt.AlignmentFlag.AlignCenter)
            )
            tl.addWidget(
                _label(_elapsed_str(p.last_modified), _BLUE_DIM, 10,
                       align=Qt.AlignmentFlag.AlignCenter)
            )
            tile.mousePressEvent = lambda e, proj=p: self._on_row_click(e, proj)
            grid.addWidget(tile, i // cols, i % cols)
        inner.addLayout(grid)
        return panel

    # --- Footer helpers ---

    def _update_uplink(self):
        projects = self._projects
        if projects:
            active = sum(1 for p in projects if p.status == "active")
            pct = int((active / len(projects)) * 100)
        else:
            pct = 0
        filled = pct // 10
        bar = "\u2588" * filled + "\u2591" * (10 - filled)
        self._uplink_label.setText(f"UPLINK: {bar}  {pct}%")
