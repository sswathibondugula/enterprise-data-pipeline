"""Unit tests for application configuration."""

from pathlib import Path

import pytest

from enterprise_etl.config import AppConfig
from enterprise_etl.exceptions import ConfigurationError


def create_required_directories(project_root: Path) -> None:
    """Create the directories required by AppConfig validation."""
    required_directories = (
        project_root / "data" / "incoming",
        project_root / "data" / "raw",
        project_root / "data" / "rejected",
        project_root / "data" / "archive",
        project_root / "reports",
    )

    for directory in required_directories:
        directory.mkdir(parents=True, exist_ok=True)


def test_config_validation_succeeds(tmp_path: Path) -> None:
    """Validation succeeds when all required directories exist."""
    create_required_directories(tmp_path)

    config = AppConfig(project_root=tmp_path)

    config.validate()


def test_config_validation_fails_for_missing_directories(
    tmp_path: Path,
) -> None:
    """Validation reports missing required directories."""
    config = AppConfig(project_root=tmp_path)

    with pytest.raises(ConfigurationError) as error:
        config.validate()

    error_message = str(error.value)

    assert "Required project directories are missing:" in error_message
    assert str(tmp_path / "data" / "incoming") in error_message