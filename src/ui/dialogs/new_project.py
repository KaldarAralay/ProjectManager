"""New project dialog for creating project folders."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt


class NewProjectDialog(QDialog):
    """Dialog for creating a new project folder."""

    def __init__(self, default_directories: list[Path], parent=None):
        """Initialize the new project dialog.

        Args:
            default_directories: List of scan directories to choose from.
        """
        super().__init__(parent)
        self._directories = default_directories
        self._created_path: Path | None = None

        self.setWindowTitle("New Project")
        self.setMinimumWidth(450)
        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)

        # Project name
        name_label = QLabel("Project Name:")
        layout.addWidget(name_label)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("my-awesome-project")
        self.name_input.textChanged.connect(self._update_preview)
        layout.addWidget(self.name_input)

        # Location
        location_label = QLabel("Location:")
        layout.addWidget(location_label)

        location_layout = QHBoxLayout()

        self.location_combo = QComboBox()
        self.location_combo.setEditable(True)
        for directory in self._directories:
            self.location_combo.addItem(str(directory))
        self.location_combo.currentTextChanged.connect(self._update_preview)
        location_layout.addWidget(self.location_combo, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_location)
        location_layout.addWidget(browse_btn)

        layout.addLayout(location_layout)

        # Preview
        preview_label = QLabel("Will create:")
        preview_label.setStyleSheet("color: #808080; margin-top: 8px;")
        layout.addWidget(preview_label)

        self.preview_path = QLabel("")
        self.preview_path.setStyleSheet("color: #0078d4; font-family: monospace;")
        self.preview_path.setWordWrap(True)
        layout.addWidget(self.preview_path)

        # Spacer
        layout.addStretch()

        # Dialog buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.create_btn = QPushButton("Create")
        self.create_btn.setObjectName("primaryButton")
        self.create_btn.clicked.connect(self._create_project)
        self.create_btn.setEnabled(False)
        btn_layout.addWidget(self.create_btn)

        layout.addLayout(btn_layout)

        # Initial preview update
        self._update_preview()

    def _update_preview(self):
        """Update the path preview."""
        name = self.name_input.text().strip()
        location = self.location_combo.currentText().strip()

        if name and location:
            # Sanitize name for filesystem
            safe_name = self._sanitize_name(name)
            full_path = Path(location) / safe_name
            self.preview_path.setText(str(full_path))
            self.create_btn.setEnabled(True)
        else:
            self.preview_path.setText("")
            self.create_btn.setEnabled(False)

    def _sanitize_name(self, name: str) -> str:
        """Sanitize project name for filesystem.

        Args:
            name: Raw project name.

        Returns:
            Filesystem-safe name.
        """
        # Replace spaces with hyphens, remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        safe_name = name
        for char in invalid_chars:
            safe_name = safe_name.replace(char, '')
        return safe_name.strip()

    def _browse_location(self):
        """Open directory browser for location."""
        current = self.location_combo.currentText()
        start_dir = current if current and Path(current).exists() else str(Path.home())

        directory = QFileDialog.getExistingDirectory(
            self,
            "Select Location for New Project",
            start_dir
        )

        if directory:
            # Add to combo if not already there
            index = self.location_combo.findText(directory)
            if index == -1:
                self.location_combo.addItem(directory)
            self.location_combo.setCurrentText(directory)

    def _create_project(self):
        """Create the project folder."""
        name = self.name_input.text().strip()
        location = self.location_combo.currentText().strip()

        if not name:
            QMessageBox.warning(self, "Error", "Please enter a project name.")
            return

        if not location:
            QMessageBox.warning(self, "Error", "Please select a location.")
            return

        safe_name = self._sanitize_name(name)
        full_path = Path(location) / safe_name

        # Check if already exists
        if full_path.exists():
            QMessageBox.warning(
                self,
                "Folder Exists",
                f"A folder already exists at:\n{full_path}"
            )
            return

        # Check if parent exists
        if not Path(location).exists():
            QMessageBox.warning(
                self,
                "Invalid Location",
                f"The location does not exist:\n{location}"
            )
            return

        # Create the folder
        try:
            full_path.mkdir(parents=True, exist_ok=False)
            self._created_path = full_path
            self.accept()
        except Exception as e:
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to create folder:\n{e}"
            )

    def get_created_path(self) -> Path | None:
        """Get the path of the created project folder.

        Returns:
            Path to the created folder, or None if cancelled.
        """
        return self._created_path
