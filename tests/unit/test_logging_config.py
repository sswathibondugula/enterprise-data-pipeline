"""Unit tests for centralized ETL logging."""

import logging
from pathlib import Path

from enterprise_etl.observability.logging_config import (
    configure_logging,
)


def test_configure_logging_creates_log_directory(
    tmp_path: Path,
) -> None:
    """Logging configuration creates its runtime directory."""

    logger = configure_logging(
        tmp_path
    )

    assert (
        tmp_path
        / "logs"
    ).is_dir()

    for handler in logger.handlers:
        handler.close()


def test_configure_logging_creates_log_file(
    tmp_path: Path,
) -> None:
    """Logging configuration creates the ETL log file."""

    logger = configure_logging(
        tmp_path
    )

    logger.info(
        "Test ETL log message"
    )

    for handler in logger.handlers:
        handler.flush()

    log_file = (
        tmp_path
        / "logs"
        / "enterprise_etl.log"
    )

    assert log_file.exists()

    log_contents = log_file.read_text(
        encoding="utf-8"
    )

    assert (
        "Test ETL log message"
        in log_contents
    )

    for handler in logger.handlers:
        handler.close()


def test_configure_logging_uses_requested_level(
    tmp_path: Path,
) -> None:
    """Logger respects the configured logging level."""

    logger = configure_logging(
        project_root=tmp_path,
        log_level=logging.WARNING,
    )

    assert (
        logger.level
        == logging.WARNING
    )

    for handler in logger.handlers:
        handler.close()


def test_reconfiguring_logging_does_not_duplicate_handlers(
    tmp_path: Path,
) -> None:
    """Repeated configuration does not create duplicate handlers."""

    logger = configure_logging(
        tmp_path
    )

    logger = configure_logging(
        tmp_path
    )

    assert len(
        logger.handlers
    ) == 2

    for handler in logger.handlers:
        handler.close()