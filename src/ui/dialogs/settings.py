"""Settings dialog for configuring scan directories and editor."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QFileDialog,
    QGroupBox, QMessageBox
)
from PyQt6.QtCore import Qt


class SettingsDialog(QDialog):
    """Dialog for application settings."""

    def __init__(self, directories: list[Path], editor_command: str, parent=None):
        """Initialize the settings dialog.

        Args:
            directories: Current scan directories.
            editor_command: Current editor command.
        """
        super().__init__(parent)
        self._directories = [str(d) for d in directories]
        self._editor_command = editor_command

        self.setWindowTitle("Settings")
        self.setMinimumSize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Scan directories section
        dirs_group = QGroupBox("Scan Directories")
        dirs_layout = QVBoxLayout(dirs_group)

        dirs_label = QLabel("Directories to scan for projects:")
        dirs_layout.addWidget(dirs_label)

        # Directory list
        self.dirs_list = QListWidget()
        for directory in self._directories:
            self.dirs_list.addItem(directory)
        dirs_layout.addWidget(self.dirs_list)

        # Directory buttons
        dirs_btn_layout = QHBoxLayout()

        add_btn = QPushButton("Add Directory")
        add_btn.clicked.connect(self._add_directory)
        dirs_btn_layout.addWidget(add_btn)

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_directory)
        dirs_btn_layout.addWidget(remove_btn)

        dirs_btn_layout.addStretch()
        dirs_layout.addLayout(dirs_btn_layout)

        layout.addWidget(dirs_group)

        # Editor section
        editor_group = QGroupBox("Editor")
        editor_layout = QVBoxLayout(editor_group)

        editor_label = QLabel("Command to open projects (e.g., 'code', 'cursor', 'idea'):")
        editor_layout.addWidget(editor_label)

        self.editor_input = QLineEdit(self._editor_command)
        self.editor_input.setPlaceholderText("code")
        editor_layout.addWidget(self.editor_input)

        layout.addWidget(editor_group)

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
        save_btn.clicked.connect(self._save)
        btn_layout.addWidget(save_btn)

        layout.addLayout(btn_layout)

    def _add_directory(self):
        """Add a new scan directory."""
        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Directory to Scan",
            str(Path.home())
        )

        if directory:
            # Check if already added
            for i in range(self.dirs_list.count()):
                if self.dirs_list.item(i).text() == directory:
                    QMessageBox.information(
                        self,
                        "Directory Exists",
                        "This directory is already in the list."
                    )
                    return

            self.dirs_list.addItem(directory)

    def _remove_directory(self):
        """Remove the selected directory."""
        current = self.dirs_list.currentRow()
        if current >= 0:
            self.dirs_list.takeItem(current)

    def _save(self):
        """Save settings and close dialog."""
        self._directories = []
        for i in range(self.dirs_list.count()):
            self._directories.append(self.dirs_list.item(i).text())

        self._editor_command = self.editor_input.text().strip() or 'code'

        self.accept()

    def get_directories(self) -> list[Path]:
        """Get the configured directories.

        Returns:
            List of directory paths.
        """
        return [Path(d) for d in self._directories]

    def get_editor_command(self) -> str:
        """Get the configured editor command.

        Returns:
            Editor command string.
        """
        return self._editor_command
