"""Project data model."""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass
class Project:
    """Represents a programming project."""

    name: str
    path: Path
    languages: list[str] = field(default_factory=list)
    status: str = 'active'  # 'active', 'hold', 'archived'
    notes: str = ''
    favorite: bool = False
    last_modified: Optional[datetime] = None
    id: Optional[int] = None

    def __post_init__(self):
        """Validate and normalize data after initialization."""
        # Ensure path is a Path object
        if isinstance(self.path, str):
            self.path = Path(self.path)

        # Validate status
        valid_statuses = ('active', 'hold', 'archived')
        if self.status not in valid_statuses:
            self.status = 'active'

    @property
    def status_display(self) -> str:
        """Get human-readable status name."""
        status_names = {
            'active': 'Active',
            'hold': 'On Hold',
            'archived': 'Archived'
        }
        return status_names.get(self.status, 'Unknown')

    @property
    def primary_language(self) -> Optional[str]:
        """Get the primary (first) language."""
        return self.languages[0] if self.languages else None

    @property
    def exists(self) -> bool:
        """Check if the project directory still exists."""
        return self.path.exists()

    @property
    def last_modified_display(self) -> str:
        """Get human-readable last modified date."""
        if not self.last_modified:
            return 'Unknown'

        now = datetime.now()
        diff = now - self.last_modified

        if diff.days == 0:
            if diff.seconds < 3600:
                minutes = diff.seconds // 60
                return f'{minutes} min ago' if minutes > 1 else 'Just now'
            hours = diff.seconds // 3600
            return f'{hours} hour{"s" if hours > 1 else ""} ago'
        elif diff.days == 1:
            return 'Yesterday'
        elif diff.days < 7:
            return f'{diff.days} days ago'
        elif diff.days < 30:
            weeks = diff.days // 7
            return f'{weeks} week{"s" if weeks > 1 else ""} ago'
        elif diff.days < 365:
            months = diff.days // 30
            return f'{months} month{"s" if months > 1 else ""} ago'
        else:
            years = diff.days // 365
            return f'{years} year{"s" if years > 1 else ""} ago'

    def to_dict(self) -> dict:
        """Convert project to dictionary."""
        return {
            'id': self.id,
            'name': self.name,
            'path': str(self.path),
            'languages': self.languages,
            'status': self.status,
            'notes': self.notes,
            'favorite': self.favorite,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Project':
        """Create project from dictionary."""
        last_modified = None
        if data.get('last_modified'):
            try:
                last_modified = datetime.fromisoformat(data['last_modified'])
            except ValueError:
                pass

        return cls(
            id=data.get('id'),
            name=data['name'],
            path=Path(data['path']),
            languages=data.get('languages', []),
            status=data.get('status', 'active'),
            notes=data.get('notes', ''),
            favorite=data.get('favorite', False),
            last_modified=last_modified
        )
