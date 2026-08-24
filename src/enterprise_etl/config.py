"""Application configuration for the ETL system."""

from dataclasses import dataclass
from pathlib import Path

from .exceptions import ConfigurationError


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class AppConfig:
    """Filesystem configuration used by the ETL application."""

    project_root: Path = PROJECT_ROOT

    def validate(self) -> None:
        """Validate that required project directories exist."""
        required_directories = (
            self.project_root / "data" / "incoming",
            self.project_root / "data" / "raw",
            self.project_root / "data" / "rejected",
            self.project_root / "data" / "archive",
            self.project_root / "reports",
        )

        missing_directories = [
            path for path in required_directories if not path.exists()
        ]

        if missing_directories:
            missing_paths = ", ".join(str(path) for path in missing_directories)
            raise ConfigurationError(
                f"Required project directories are missing: {missing_paths}"
            )
        