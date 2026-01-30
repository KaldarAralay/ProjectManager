"""Project details dialog for editing project metadata."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QTextEdit, QCheckBox, QGroupBox
)
from PyQt6.QtCore import Qt

from ...models.project import Project


class ProjectDetailsDialog(QDialog):
    """Dialog for viewing and editing project details."""

    def __init__(self, project: Project, parent=None):
        """Initialize the project details dialog.

        Args:
            project: Project to edit.
        """
        super().__init__(parent)
        self._project = project

        self.setWindowTitle(f"Project Details - {project.name}")
        self.setMinimumSize(450, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Project info section
        info_group = QGroupBox("Project Information")
        info_layout = QVBoxLayout(info_group)

        # Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        name_label.setMinimumWidth(80)
        name_layout.addWidget(name_label)

        self.name_input = QLineEdit(self._project.name)
        name_layout.addWidget(self.name_input)
        info_layout.addLayout(name_layout)

        # Path (read-only)
        path_layout = QHBoxLayout()
        path_label = QLabel("Path:")
        path_label.setMinimumWidth(80)
        path_layout.addWidget(path_label)

        path_value = QLabel(str(self._project.path))
        path_value.setObjectName("secondaryText")
        path_value.setWordWrap(True)
        path_layout.addWidget(path_value, 1)
        info_layout.addLayout(path_layout)

        # Languages (read-only)
        lang_layout = QHBoxLayout()
        lang_label = QLabel("Languages:")
        lang_label.setMinimumWidth(80)
        lang_layout.addWidget(lang_label)

        languages = ', '.join(self._project.languages) if self._project.languages else 'None detected'
        lang_value = QLabel(languages)
        lang_value.setObjectName("secondaryText")
        lang_layout.addWidget(lang_value, 1)
        info_layout.addLayout(lang_layout)

        # Last modified (read-only)
        modified_layout = QHBoxLayout()
        modified_label = QLabel("Modified:")
        modified_label.setMinimumWidth(80)
        modified_layout.addWidget(modified_label)

        modified_value = QLabel(self._project.last_modified_display)
        modified_value.setObjectName("secondaryText")
        modified_layout.addWidget(modified_value, 1)
        info_layout.addLayout(modified_layout)

        layout.addWidget(info_group)

        # Status section
        status_group = QGroupBox("Status & Settings")
        status_layout = QVBoxLayout(status_group)

        # Status dropdown
        status_row = QHBoxLayout()
        status_label = QLabel("Status:")
        status_label.setMinimumWidth(80)
        status_row.addWidget(status_label)

        self.status_combo = QComboBox()
        self.status_combo.addItem("Active", "active")
        self.status_combo.addItem("On Hold", "hold")
        self.status_combo.addItem("Archived", "archived")

        # Set current status
        index = self.status_combo.findData(self._project.status)
        if index >= 0:
            self.status_combo.setCurrentIndex(index)
        status_row.addWidget(self.status_combo, 1)
        status_layout.addLayout(status_row)

        # Favorite checkbox
        fav_row = QHBoxLayout()
        fav_label = QLabel("")
        fav_label.setMinimumWidth(80)
        fav_row.addWidget(fav_label)

        self.favorite_check = QCheckBox("Mark as favorite")
        self.favorite_check.setChecked(self._project.favorite)
        fav_row.addWidget(self.favorite_check)
        fav_row.addStretch()
        status_layout.addLayout(fav_row)

        layout.addWidget(status_group)

        # Notes section
        notes_group = QGroupBox("Notes")
        notes_layout = QVBoxLayout(notes_group)

        self.notes_edit = QTextEdit()
        self.notes_edit.setPlaceholderText("Add notes about this project...")
        self.notes_edit.setPlainText(self._project.notes)
        self.notes_edit.setMaximumHeight(120)
        notes_layout.addWidget(self.notes_edit)

        layout.addWidget(notes_group)

        # Spacer
        layout.addStretch()

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryButton")
        save_btn.clicked.connect(self.accept)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def get_project(self) -> Project:
        """Get the project with updated values.

        Returns:
            Updated project.
        """
        self._project.name = self.name_input.text().strip() or self._project.path.name
        self._project.status = self.status_combo.currentData()
        self._project.favorite = self.favorite_check.isChecked()
        self._project.notes = self.notes_edit.toPlainText()

        return self._project
