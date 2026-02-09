"""Mission Control themed dashboard view."""

import time
from datetime import datetime
from collections import Counter

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QFrame, QScrollArea, QProgressBar, QMenu, QPushButton, QComboBox,
    QLineEdit
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QFont

from pathlib import Path

from ..models.project import Project

# Mission Control palette
_GREEN = "#4ade80"
_BLUE = "#60a5fa"
_BLUE_DIM = "#3d6e8f"
_BLUE_DARK = "#1a3152"
_AMBER = "#fbbf24"
_RED = "#f87171"
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


def _mc_button(text, color=_BLUE_DIM, hover_color=_GREEN):
    """Create a small themed button for the status bar."""
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"QPushButton {{ color: {color}; background: transparent; "
        f"border: 1px solid {_BLUE_DARK}; border-radius: 3px; "
        f"padding: 2px 8px; font-size: 10px; }}"
        f"QPushButton:hover {{ color: {hover_color}; border-color: {hover_color}; }}"
    )
    return btn


def _status_button(text, color):
    """Create a small colored status button."""
    btn = QPushButton(text)
    btn.setCursor(Qt.CursorShape.PointingHandCursor)
    btn.setStyleSheet(
        f"QPushButton {{ color: #ffffff; background: {color}; "
        f"border: none; border-radius: 3px; "
        f"padding: 2px 8px; font-size: 10px; }}"
        f"QPushButton:hover {{ background: {color}; opacity: 0.8; }}"
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

    # Selection signals
    selection_changed = pyqtSignal(object, bool)  # project, selected
    select_mode_changed = pyqtSignal(bool)
    batch_status_changed = pyqtSignal(str)  # 'active', 'hold', 'archived'

    # Workspace signal
    workspace_changed = pyqtSignal(str)  # directory path or 'all'

    # Global action signals
    settings_requested = pyqtSignal()
    refresh_requested = pyqtSignal()
    new_project_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._projects: list[Project] = []
        self._all_projects: list[Project] = []  # unfiltered projects from app
        self._scan_dirs: list[Path] = []
        self._active_workspace: str = 'all'  # 'all' or directory path string
        self._met_start = time.time()
        self._select_mode = False
        self._selected_paths: set[str] = set()
        self._open_names: set[str] = set()  # lowercase project names that are open
        self._row_widgets: dict[str, QFrame] = {}  # path -> widget for styling updates
        self._project_by_path: dict[str, Project] = {}  # for open status updates
        self._search_query: str = ''  # current search filter text

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

        # Left: systems nominal + search
        left = QHBoxLayout()
        left.setSpacing(6)
        left.addWidget(_label("\u25cf", _GREEN, 14))
        self._status_text = _label("SYSTEMS NOMINAL", _GREEN, 11)
        left.addWidget(self._status_text)

        left.addSpacing(12)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("\u2315 SEARCH MISSIONS...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.setFixedWidth(200)
        self._search_input.setStyleSheet(
            f"QLineEdit {{"
            f"  color: {_GREEN}; background: {_PANEL_BG};"
            f"  border: 1px solid {_BLUE_DARK}; border-radius: 3px;"
            f"  padding: 3px 8px; font-size: 11px;"
            f"  font-family: Consolas;"
            f"}}"
            f"QLineEdit:focus {{ border-color: {_GREEN}; }}"
            f"QLineEdit::placeholder {{ color: {_BLUE_DIM}; }}"
        )
        self._search_input.textChanged.connect(self._on_search_changed)
        left.addWidget(self._search_input)

        left.addStretch()
        status_bar.addLayout(left, 1)

        # Center: title + workspace selector
        center = QVBoxLayout()
        center.setSpacing(2)
        center.setContentsMargins(0, 0, 0, 0)

        center.addWidget(
            _label("MISSION CONTROL", _BLUE_DIM, 12,
                   align=Qt.AlignmentFlag.AlignCenter)
        )

        self._workspace_combo = QComboBox()
        self._workspace_combo.setCursor(Qt.CursorShape.PointingHandCursor)
        self._workspace_combo.setStyleSheet(
            f"QComboBox {{"
            f"  color: {_GREEN}; background: transparent;"
            f"  border: 1px solid {_BLUE_DARK}; border-radius: 3px;"
            f"  padding: 2px 8px; font-size: 11px;"
            f"  font-family: Consolas; min-width: 160px;"
            f"}}"
            f"QComboBox:hover {{ border-color: {_GREEN}; }}"
            f"QComboBox::drop-down {{ border: none; width: 16px; }}"
            f"QComboBox::down-arrow {{ width: 0; height: 0; }}"
            f"QComboBox QAbstractItemView {{"
            f"  background-color: {_PANEL_BG}; color: {_GREEN};"
            f"  border: 1px solid {_BLUE_DARK};"
            f"  selection-background-color: {_BLUE_DARK};"
            f"  font-family: Consolas; font-size: 11px;"
            f"}}"
        )
        self._workspace_combo.addItem("\u25c8 ALL WORKSPACES", "all")
        self._workspace_combo.currentIndexChanged.connect(self._on_workspace_changed)

        center.addWidget(self._workspace_combo, 0, Qt.AlignmentFlag.AlignCenter)

        center_widget = QWidget()
        center_widget.setStyleSheet("background: transparent;")
        center_widget.setLayout(center)
        status_bar.addWidget(center_widget, 2)

        # Right: buttons + MET
        right_bar = QHBoxLayout()
        right_bar.setSpacing(8)
        right_bar.addStretch()

        new_btn = _mc_button("+ New")
        new_btn.clicked.connect(self.new_project_clicked.emit)
        right_bar.addWidget(new_btn)

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

        # Selection controls (in footer for minimal look)
        footer.addSpacing(20)

        self._select_btn = _mc_button("\u2610 Select")
        self._select_btn.clicked.connect(self._toggle_select_mode)
        footer.addWidget(self._select_btn)

        # Batch status buttons (hidden by default)
        self._batch_container = QWidget()
        batch_layout = QHBoxLayout(self._batch_container)
        batch_layout.setContentsMargins(0, 0, 0, 0)
        batch_layout.setSpacing(4)

        self._select_count_label = _label("0 selected", _BLUE_DIM, 10)
        batch_layout.addWidget(self._select_count_label)

        active_btn = _status_button("Active", _GREEN)
        active_btn.clicked.connect(lambda: self._on_batch_status("active"))
        batch_layout.addWidget(active_btn)

        hold_btn = _status_button("Hold", _AMBER)
        hold_btn.clicked.connect(lambda: self._on_batch_status("hold"))
        batch_layout.addWidget(hold_btn)

        archive_btn = _status_button("Archive", _BLUE_DIM)
        archive_btn.clicked.connect(lambda: self._on_batch_status("archived"))
        batch_layout.addWidget(archive_btn)

        cancel_btn = _mc_button("\u2715", _RED, _RED)
        cancel_btn.setToolTip("Cancel selection")
        cancel_btn.clicked.connect(self._exit_select_mode)
        batch_layout.addWidget(cancel_btn)

        self._batch_container.setVisible(False)
        footer.addWidget(self._batch_container)

        footer.addStretch()
        self._uplink_label = _label("", _BLUE_DIM, 10)
        footer.addWidget(self._uplink_label)
        footer.addWidget(_label("SIGNAL: STRONG", _BLUE_DIM, 10))
        main.addLayout(footer)

    # ------------------------------------------------------------------
    # Selection mode
    # ------------------------------------------------------------------

    def _toggle_select_mode(self):
        self._select_mode = not self._select_mode
        self._selected_paths.clear()
        self._update_select_ui()
        self.select_mode_changed.emit(self._select_mode)
        self._rebuild()

    def _exit_select_mode(self):
        self._select_mode = False
        self._selected_paths.clear()
        self._update_select_ui()
        self.select_mode_changed.emit(False)
        self._rebuild()

    def _update_select_ui(self):
        if self._select_mode:
            self._select_btn.setText("\u2611 Select")
            self._batch_container.setVisible(True)
        else:
            self._select_btn.setText("\u2610 Select")
            self._batch_container.setVisible(False)
        self._update_select_count()

    def _update_select_count(self):
        count = len(self._selected_paths)
        self._select_count_label.setText(f"{count} selected")

    def _on_batch_status(self, status: str):
        if self._selected_paths:
            self.batch_status_changed.emit(status)
            self._exit_select_mode()

    def set_select_mode(self, enabled: bool):
        """External control for select mode (from main window)."""
        if enabled != self._select_mode:
            self._select_mode = enabled
            self._selected_paths.clear()
            self._update_select_ui()
            self._rebuild()

    def clear_selection(self):
        """Clear selection state (called after batch operation)."""
        self._selected_paths.clear()
        self._update_select_count()

    # ------------------------------------------------------------------
    # Workspace management
    # ------------------------------------------------------------------

    def set_scan_directories(self, dirs: list[Path]):
        """Update the list of scan directories (workspaces).

        Args:
            dirs: List of scan directory paths.
        """
        self._scan_dirs = list(dirs)
        self._update_workspace_combo()

    def set_active_workspace(self, workspace: str):
        """Set the active workspace without emitting a signal.

        Args:
            workspace: Directory path string, or 'all'.
        """
        self._active_workspace = workspace
        self._update_workspace_combo()

    def _filter_by_workspace(self, projects: list[Project]) -> list[Project]:
        """Filter projects to only those in the active workspace.

        Args:
            projects: Full list of projects.

        Returns:
            Filtered list, or the full list if workspace is 'all'.
        """
        if self._active_workspace == 'all':
            return projects

        workspace_path = Path(self._active_workspace)
        filtered = []
        for p in projects:
            try:
                p.path.resolve().relative_to(workspace_path.resolve())
                filtered.append(p)
            except ValueError:
                continue
        return filtered

    def _update_workspace_combo(self):
        """Sync the workspace dropdown with current scan directories and selection."""
        if not hasattr(self, '_workspace_combo'):
            return

        combo = self._workspace_combo
        combo.blockSignals(True)
        combo.clear()

        combo.addItem("\u25c8 ALL WORKSPACES", "all")
        for scan_dir in self._scan_dirs:
            display_name = scan_dir.name.upper()
            combo.addItem(f"\u25cb {display_name}", str(scan_dir))

        # Restore selection
        idx = combo.findData(self._active_workspace)
        if idx >= 0:
            combo.setCurrentIndex(idx)
        else:
            combo.setCurrentIndex(0)  # fallback to "all"
            self._active_workspace = 'all'

        combo.blockSignals(False)

    def _on_workspace_changed(self, index: int):
        """Handle workspace dropdown selection change."""
        workspace = self._workspace_combo.itemData(index)
        if workspace is None:
            workspace = 'all'
        self._active_workspace = workspace
        self._projects = self._filter_projects(self._all_projects)
        self._rebuild()
        self.workspace_changed.emit(workspace)

        # Update status text
        if workspace == 'all':
            self._status_text.setText("SYSTEMS NOMINAL")
        else:
            name = Path(workspace).name.upper()
            self._status_text.setText(f"WORKSPACE: {name}")

    def _on_search_changed(self, text: str):
        """Handle search input text changes.

        Args:
            text: Current search text.
        """
        self._search_query = text.lower().strip()
        self._projects = self._filter_projects(self._all_projects)
        self._rebuild()

    def _filter_projects(self, projects: list[Project]) -> list[Project]:
        """Apply workspace and search filters to the project list.

        Args:
            projects: Full list of projects.

        Returns:
            Filtered list.
        """
        filtered = self._filter_by_workspace(projects)
        if self._search_query:
            filtered = [
                p for p in filtered
                if self._search_query in p.name.lower()
            ]
        return filtered

    def update_open_status(self, open_names: set[str]):
        """Update which projects are currently open.

        Args:
            open_names: Set of lowercase project names that are open.
        """
        if open_names == self._open_names:
            return  # No change

        self._open_names = open_names

        # Update styling for all tracked widgets
        for path_str, widget in self._row_widgets.items():
            project = self._project_by_path.get(path_str)
            if project:
                is_selected = path_str in self._selected_paths
                is_open = project.name.lower() in self._open_names
                # Determine if this is a tile (secondary) or row (primary)
                # by checking the layout - tiles have centered alignment
                self._apply_row_style(widget, is_selected, is_open)

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
        self._all_projects = list(projects)
        self._projects = self._filter_projects(self._all_projects)
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
        self._row_widgets.clear()
        self._project_by_path.clear()
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
        path_str = str(project.path)
        is_selected = path_str in self._selected_paths

        # Status color mapping
        status_colors = {"active": _GREEN, "hold": _AMBER, "archived": _BLUE_DIM}
        status_color = status_colors.get(project.status, _GREEN)

        is_open = project.name.lower() in self._open_names

        row = QFrame()
        row.setCursor(Qt.CursorShape.PointingHandCursor)
        self._row_widgets[path_str] = row
        self._project_by_path[path_str] = project
        self._apply_row_style(row, is_selected, is_open)

        h = QHBoxLayout(row)
        h.setContentsMargins(8, 6, 8, 6)
        h.setSpacing(8)

        # Selection indicator or status dot
        if self._select_mode:
            check = "\u2611" if is_selected else "\u2610"
            h.addWidget(_label(check, _GREEN if is_selected else _BLUE_DIM, 12))
        else:
            # Status dot colored by project status
            h.addWidget(_label("\u25cf", status_color, 10))

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
        # Status badge
        status_labels = {"active": "ACT", "hold": "HLD", "archived": "ARC"}
        status_text = status_labels.get(project.status, "ACT")
        right.addWidget(
            _label(status_text, status_color, 9, bold=True,
                   align=Qt.AlignmentFlag.AlignRight)
        )
        if project.favorite:
            right.addWidget(
                _label("\u2605 PRI", _AMBER, 10, align=Qt.AlignmentFlag.AlignRight)
            )
        h.addLayout(right)

        row.mousePressEvent = lambda e, p=project: self._on_row_click(e, p)
        return row

    def _apply_row_style(self, row: QFrame, selected: bool, is_open: bool = False):
        if selected:
            row.setStyleSheet(
                f"QFrame {{ background-color: rgba(74,222,128,0.2); "
                f"border: 1px solid {_GREEN}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(74,222,128,0.3); }}"
            )
        elif is_open:
            row.setStyleSheet(
                f"QFrame {{ background-color: rgba(30,58,95,0.3); "
                f"border: 1px solid {_GREEN}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(30,58,95,0.5); }}"
            )
        else:
            row.setStyleSheet(
                f"QFrame {{ background-color: rgba(30,58,95,0.3); "
                f"border: 1px solid transparent; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(30,58,95,0.5); }}"
            )

    def _on_row_click(self, event, project: Project):
        """Handle mouse clicks on a project row."""
        if event.button() == Qt.MouseButton.RightButton:
            self._show_project_menu(project, event.globalPosition().toPoint())
        elif self._select_mode:
            self._toggle_selection(project)
        else:
            self.open_clicked.emit(project)

    def _toggle_selection(self, project: Project):
        path_str = str(project.path)
        if path_str in self._selected_paths:
            self._selected_paths.discard(path_str)
            selected = False
        else:
            self._selected_paths.add(path_str)
            selected = True

        # Update visual
        if path_str in self._row_widgets:
            self._apply_row_style(self._row_widgets[path_str], selected)

        self._update_select_count()
        self.selection_changed.emit(project, selected)
        # Rebuild to update checkbox icons
        self._rebuild()

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

        # Status color mapping
        status_colors = {"active": _GREEN, "hold": _AMBER, "archived": _BLUE_DIM}
        status_labels = {"active": "ACT", "hold": "HLD", "archived": "ARC"}

        for i, p in enumerate(projects):
            path_str = str(p.path)
            is_selected = path_str in self._selected_paths
            is_open = p.name.lower() in self._open_names
            status_color = status_colors.get(p.status, _GREEN)
            status_text = status_labels.get(p.status, "ACT")

            tile = QFrame()
            tile.setCursor(Qt.CursorShape.PointingHandCursor)
            self._row_widgets[path_str] = tile
            self._project_by_path[path_str] = p
            self._apply_tile_style(tile, is_selected, is_open)

            tl = QVBoxLayout(tile)
            tl.setContentsMargins(8, 6, 8, 6)

            # Checkbox at top if in select mode
            if self._select_mode:
                check = "\u2611" if is_selected else "\u2610"
                tl.addWidget(
                    _label(check, _GREEN if is_selected else _BLUE_DIM, 10,
                           align=Qt.AlignmentFlag.AlignCenter)
                )

            # Project name centered
            tl.addWidget(
                _label(p.name, _GREEN, 11, align=Qt.AlignmentFlag.AlignCenter)
            )

            # Bottom row: time on left, status on right
            bottom_row = QHBoxLayout()
            bottom_row.addWidget(
                _label(_elapsed_str(p.last_modified), _BLUE_DIM, 9)
            )
            bottom_row.addStretch()
            bottom_row.addWidget(_label("\u25cf", status_color, 8))
            bottom_row.addWidget(_label(status_text, status_color, 8))
            tl.addLayout(bottom_row)

            tile.mousePressEvent = lambda e, proj=p: self._on_row_click(e, proj)
            grid.addWidget(tile, i // cols, i % cols)
        inner.addLayout(grid)
        return panel

    def _apply_tile_style(self, tile: QFrame, selected: bool, is_open: bool = False):
        if selected:
            tile.setStyleSheet(
                f"QFrame {{ background-color: rgba(74,222,128,0.2); "
                f"border: 1px solid {_GREEN}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(74,222,128,0.3); }}"
            )
        elif is_open:
            tile.setStyleSheet(
                f"QFrame {{ background-color: rgba(30,58,95,0.3); "
                f"border: 1px solid {_GREEN}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(30,58,95,0.5); }}"
            )
        else:
            tile.setStyleSheet(
                f"QFrame {{ background-color: rgba(30,58,95,0.3); "
                f"border: 1px solid {_PANEL_BORDER}; border-radius: 4px; }}"
                f"QFrame:hover {{ background-color: rgba(30,58,95,0.5); }}"
            )

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
