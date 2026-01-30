"""Comprehensive unit tests for Project Manager."""

import sys
import os
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models.project import Project
from src.database import Database
from src.scanner import ProjectScanner, scan_directories
from src.utils.detector import detect_languages, detect_frameworks


class TestProject:
    """Tests for Project model."""

    def test_project_creation(self):
        """Test basic project creation."""
        project = Project(
            name="TestProject",
            path=Path("/test/path"),
            languages=["Python", "JavaScript"],
            status="active"
        )
        assert project.name == "TestProject"
        assert project.path == Path("/test/path")
        assert project.languages == ["Python", "JavaScript"]
        assert project.status == "active"
        assert project.favorite == False
        print("  [PASS] Project creation")

    def test_project_status_display(self):
        """Test status display names."""
        project = Project(name="Test", path=Path("/test"))

        project.status = "active"
        assert project.status_display == "Active"

        project.status = "hold"
        assert project.status_display == "On Hold"

        project.status = "archived"
        assert project.status_display == "Archived"
        print("  [PASS] Status display")

    def test_project_primary_language(self):
        """Test primary language property."""
        project = Project(name="Test", path=Path("/test"), languages=["Python", "JS"])
        assert project.primary_language == "Python"

        project2 = Project(name="Test2", path=Path("/test2"), languages=[])
        assert project2.primary_language is None
        print("  [PASS] Primary language")

    def test_project_last_modified_display(self):
        """Test last modified display formatting."""
        now = datetime.now()

        project = Project(name="Test", path=Path("/test"), last_modified=now)
        assert "min" in project.last_modified_display or "Just now" in project.last_modified_display

        project.last_modified = now - timedelta(hours=2)
        assert "hour" in project.last_modified_display

        project.last_modified = now - timedelta(days=1)
        assert project.last_modified_display == "Yesterday"

        project.last_modified = now - timedelta(days=5)
        assert "days" in project.last_modified_display
        print("  [PASS] Last modified display")

    def test_project_to_dict(self):
        """Test project serialization."""
        project = Project(
            name="Test",
            path=Path("/test"),
            languages=["Python"],
            status="active",
            favorite=True
        )
        data = project.to_dict()
        assert data["name"] == "Test"
        assert "test" in data["path"]  # Path format varies by OS
        assert data["languages"] == ["Python"]
        assert data["favorite"] == True
        print("  [PASS] Project to dict")

    def test_project_from_dict(self):
        """Test project deserialization."""
        data = {
            "name": "Test",
            "path": "/test",
            "languages": ["Rust"],
            "status": "hold",
            "favorite": True
        }
        project = Project.from_dict(data)
        assert project.name == "Test"
        assert project.status == "hold"
        assert project.favorite == True
        print("  [PASS] Project from dict")


class TestDatabase:
    """Tests for Database operations."""

    def setup_method(self):
        """Create temp database for each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = Path(self.temp_dir) / "test.db"
        self.db = Database(self.db_path)

    def teardown_method(self):
        """Clean up temp database."""
        self.db.close()
        shutil.rmtree(self.temp_dir)

    def test_add_and_get_project(self):
        """Test adding and retrieving a project."""
        project = Project(
            name="TestProject",
            path=Path("/test/project"),
            languages=["Python"],
            status="active"
        )
        self.db.add_project(project)

        retrieved = self.db.get_project_by_path(Path("/test/project"))
        assert retrieved is not None
        assert retrieved.name == "TestProject"
        assert retrieved.languages == ["Python"]
        print("  [PASS] Add and get project")

    def test_get_all_projects(self):
        """Test getting all projects."""
        for i in range(3):
            project = Project(name=f"Project{i}", path=Path(f"/test/{i}"))
            self.db.add_project(project)

        projects = self.db.get_all_projects()
        assert len(projects) == 3
        print("  [PASS] Get all projects")

    def test_update_project(self):
        """Test updating a project."""
        project = Project(name="Test", path=Path("/test"), status="active")
        self.db.add_project(project)

        project.status = "archived"
        project.notes = "Updated notes"
        self.db.update_project(project)

        retrieved = self.db.get_project_by_path(Path("/test"))
        assert retrieved.status == "archived"
        assert retrieved.notes == "Updated notes"
        print("  [PASS] Update project")

    def test_delete_project(self):
        """Test deleting a project."""
        project = Project(name="Test", path=Path("/test"))
        self.db.add_project(project)

        self.db.delete_project(Path("/test"))

        retrieved = self.db.get_project_by_path(Path("/test"))
        assert retrieved is None
        print("  [PASS] Delete project")

    def test_get_projects_by_status(self):
        """Test filtering by status."""
        self.db.add_project(Project(name="Active1", path=Path("/a1"), status="active"))
        self.db.add_project(Project(name="Active2", path=Path("/a2"), status="active"))
        self.db.add_project(Project(name="Hold1", path=Path("/h1"), status="hold"))

        active = self.db.get_projects_by_status("active")
        assert len(active) == 2

        hold = self.db.get_projects_by_status("hold")
        assert len(hold) == 1
        print("  [PASS] Filter by status")

    def test_get_projects_by_language(self):
        """Test filtering by language."""
        self.db.add_project(Project(name="P1", path=Path("/p1"), languages=["Python", "JS"]))
        self.db.add_project(Project(name="P2", path=Path("/p2"), languages=["Python"]))
        self.db.add_project(Project(name="P3", path=Path("/p3"), languages=["Rust"]))

        python_projects = self.db.get_projects_by_language("Python")
        assert len(python_projects) == 2

        rust_projects = self.db.get_projects_by_language("Rust")
        assert len(rust_projects) == 1
        print("  [PASS] Filter by language")

    def test_get_all_languages(self):
        """Test getting unique languages."""
        self.db.add_project(Project(name="P1", path=Path("/p1"), languages=["Python", "JS"]))
        self.db.add_project(Project(name="P2", path=Path("/p2"), languages=["Python", "Rust"]))

        languages = self.db.get_all_languages()
        assert set(languages) == {"JS", "Python", "Rust"}
        print("  [PASS] Get all languages")

    def test_settings(self):
        """Test settings storage."""
        self.db.set_setting("test_key", "test_value")
        assert self.db.get_setting("test_key") == "test_value"
        assert self.db.get_setting("nonexistent", "default") == "default"
        print("  [PASS] Settings storage")

    def test_scan_directories_setting(self):
        """Test scan directories setting."""
        dirs = [Path("/dir1"), Path("/dir2")]
        self.db.set_scan_directories(dirs)

        retrieved = self.db.get_scan_directories()
        assert len(retrieved) == 2
        print("  [PASS] Scan directories setting")


class TestScanner:
    """Tests for project scanner."""

    def setup_method(self):
        """Create temp directory structure for testing."""
        self.temp_dir = tempfile.mkdtemp()

        # Create a Python project
        py_project = Path(self.temp_dir) / "python_project"
        py_project.mkdir()
        (py_project / "requirements.txt").write_text("pytest\n")
        (py_project / "main.py").write_text("print('hello')\n")

        # Create a Node.js project
        node_project = Path(self.temp_dir) / "node_project"
        node_project.mkdir()
        (node_project / "package.json").write_text('{"name": "test"}\n')

        # Create a Rust project
        rust_project = Path(self.temp_dir) / "rust_project"
        rust_project.mkdir()
        (rust_project / "Cargo.toml").write_text('[package]\nname = "test"\n')

        # Create a non-project directory
        non_project = Path(self.temp_dir) / "not_a_project"
        non_project.mkdir()
        (non_project / "random.txt").write_text("just a file\n")

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_scan_finds_projects(self):
        """Test that scanner finds valid projects."""
        projects = scan_directories([Path(self.temp_dir)])

        names = [p.name for p in projects]
        assert "python_project" in names
        assert "node_project" in names
        assert "rust_project" in names
        assert "not_a_project" not in names
        print("  [PASS] Scanner finds projects")

    def test_scan_detects_languages(self):
        """Test that scanner detects languages."""
        projects = scan_directories([Path(self.temp_dir)])

        py_project = next(p for p in projects if p.name == "python_project")
        assert "Python" in py_project.languages

        node_project = next(p for p in projects if p.name == "node_project")
        assert "JavaScript" in node_project.languages

        rust_project = next(p for p in projects if p.name == "rust_project")
        assert "Rust" in rust_project.languages
        print("  [PASS] Scanner detects languages")

    def test_scanner_skips_node_modules(self):
        """Test that scanner skips node_modules."""
        # Create nested project in node_modules (should be skipped)
        node_modules = Path(self.temp_dir) / "node_project" / "node_modules"
        node_modules.mkdir()
        nested = node_modules / "nested_project"
        nested.mkdir()
        (nested / "package.json").write_text('{"name": "nested"}\n')

        projects = scan_directories([Path(self.temp_dir)])
        names = [p.name for p in projects]
        assert "nested_project" not in names
        print("  [PASS] Scanner skips node_modules")


class TestDetector:
    """Tests for language detection."""

    def setup_method(self):
        """Create temp directory for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def teardown_method(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_detect_python(self):
        """Test Python detection."""
        (Path(self.temp_dir) / "requirements.txt").write_text("flask\n")
        languages = detect_languages(Path(self.temp_dir))
        assert "Python" in languages
        print("  [PASS] Detect Python")

    def test_detect_javascript(self):
        """Test JavaScript detection."""
        (Path(self.temp_dir) / "package.json").write_text('{"name": "test"}\n')
        languages = detect_languages(Path(self.temp_dir))
        assert "JavaScript" in languages
        print("  [PASS] Detect JavaScript")

    def test_detect_typescript(self):
        """Test TypeScript detection."""
        (Path(self.temp_dir) / "tsconfig.json").write_text('{"compilerOptions": {}}\n')
        languages = detect_languages(Path(self.temp_dir))
        assert "TypeScript" in languages
        print("  [PASS] Detect TypeScript")

    def test_detect_rust(self):
        """Test Rust detection."""
        (Path(self.temp_dir) / "Cargo.toml").write_text('[package]\n')
        languages = detect_languages(Path(self.temp_dir))
        assert "Rust" in languages
        print("  [PASS] Detect Rust")

    def test_detect_go(self):
        """Test Go detection."""
        (Path(self.temp_dir) / "go.mod").write_text('module test\n')
        languages = detect_languages(Path(self.temp_dir))
        assert "Go" in languages
        print("  [PASS] Detect Go")

    def test_detect_multiple_languages(self):
        """Test detecting multiple languages."""
        (Path(self.temp_dir) / "requirements.txt").write_text("flask\n")
        (Path(self.temp_dir) / "package.json").write_text('{"name": "test"}\n')

        languages = detect_languages(Path(self.temp_dir))
        assert "Python" in languages
        assert "JavaScript" in languages
        print("  [PASS] Detect multiple languages")

    def test_detect_react_framework(self):
        """Test React framework detection."""
        (Path(self.temp_dir) / "package.json").write_text('{"dependencies": {"react": "^18.0.0"}}\n')
        frameworks = detect_frameworks(Path(self.temp_dir))
        assert "React" in frameworks
        print("  [PASS] Detect React framework")


def run_tests():
    """Run all tests."""
    print("\n" + "="*60)
    print("Running Project Manager Unit Tests")
    print("="*60)

    test_classes = [
        ("Project Model", TestProject),
        ("Database", TestDatabase),
        ("Scanner", TestScanner),
        ("Detector", TestDetector),
    ]

    total_passed = 0
    total_failed = 0

    for name, test_class in test_classes:
        print(f"\n{name} Tests:")
        print("-" * 40)

        instance = test_class()

        for method_name in dir(instance):
            if method_name.startswith("test_"):
                # Setup if exists
                if hasattr(instance, "setup_method"):
                    instance.setup_method()

                try:
                    getattr(instance, method_name)()
                    total_passed += 1
                except AssertionError as e:
                    print(f"  [FAIL] {method_name}: {e}")
                    total_failed += 1
                except Exception as e:
                    print(f"  [ERROR] {method_name}: {e}")
                    total_failed += 1
                finally:
                    # Teardown if exists
                    if hasattr(instance, "teardown_method"):
                        try:
                            instance.teardown_method()
                        except:
                            pass

    print("\n" + "="*60)
    print(f"Results: {total_passed} passed, {total_failed} failed")
    print("="*60)

    return total_failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
