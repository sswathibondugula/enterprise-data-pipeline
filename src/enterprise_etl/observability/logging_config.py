"""Centralized logging configuration for the ETL application."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path


LOGGER_NAME = "enterprise_etl"

LOG_FORMAT = (
    "%(asctime)s | "
    "%(levelname)s | "
    "%(name)s | "
    "%(message)s"
)


def configure_logging(
    project_root: Path,
    log_level: int = logging.INFO,
) -> logging.Logger:
    """Configure console and rotating-file logging."""

    log_directory = (
        project_root
        / "logs"
    )

    log_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_file = (
        log_directory
        / "enterprise_etl.log"
    )

    logger = logging.getLogger(
        LOGGER_NAME
    )

    logger.setLevel(
        log_level
    )

    logger.propagate = False

    for handler in logger.handlers[:]:
        handler.close()
        logger.removeHandler(
            handler
        )

    formatter = logging.Formatter(
        LOG_FORMAT
    )

    console_handler = logging.StreamHandler()

    console_handler.setLevel(
        log_level
    )

    console_handler.setFormatter(
        formatter
    )

    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=5 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )

    file_handler.setLevel(
        log_level
    )

    file_handler.setFormatter(
        formatter
    )

    logger.addHandler(
        console_handler
    )

    logger.addHandler(
        file_handler
    )

    return logger