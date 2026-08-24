"""Unit tests for the ETL command-line interface."""

import enterprise_etl.cli as cli
from enterprise_etl.exceptions import ConfigurationError


class ValidConfig:
    """Test configuration that always validates successfully."""

    project_root = "test-project-root"

    def validate(self) -> None:
        """Simulate successful configuration validation."""


class InvalidConfig:
    """Test configuration that always fails validation."""

    project_root = "test-project-root"

    def validate(self) -> None:
        """Simulate failed configuration validation."""
        raise ConfigurationError("Test configuration failure")


def test_main_returns_zero_for_valid_configuration(
    monkeypatch,
    capsys,
) -> None:
    """CLI returns success when configuration validation succeeds."""
    monkeypatch.setattr(cli, "AppConfig", ValidConfig)

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 0
    assert "ETL application is ready." in output


def test_main_returns_one_for_invalid_configuration(
    monkeypatch,
    capsys,
) -> None:
    """CLI returns failure when configuration validation fails."""
    monkeypatch.setattr(cli, "AppConfig", InvalidConfig)

    exit_code = cli.main()
    output = capsys.readouterr().out

    assert exit_code == 1
    assert "Application startup failed:" in output
    assert "Test configuration failure" in output