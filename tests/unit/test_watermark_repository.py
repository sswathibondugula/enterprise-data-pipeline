"""Unit tests for incremental watermark tracking."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from enterprise_etl.exceptions import (
    WatermarkTrackingError,
)
from enterprise_etl.database.watermark_repository import (
    WatermarkRepository,
)


def test_get_watermark_returns_existing_value() -> None:
    """Repository returns the stored watermark."""

    expected_watermark = datetime(
        2026,
        10,
        18,
        12,
        0,
        tzinfo=timezone.utc,
    )

    engine = MagicMock()
    connection = MagicMock()

    engine.connect.return_value.__enter__.return_value = (
        connection
    )

    result = MagicMock()

    result.scalar_one_or_none.return_value = (
        expected_watermark
    )

    connection.execute.return_value = result

    repository = WatermarkRepository(
        engine
    )

    watermark = repository.get_watermark(
        pipeline_name="order_pipeline",
        watermark_name="source_updated_at",
    )

    assert watermark == expected_watermark


def test_get_watermark_returns_none_when_missing() -> None:
    """Repository returns None before the first incremental run."""

    engine = MagicMock()
    connection = MagicMock()

    engine.connect.return_value.__enter__.return_value = (
        connection
    )

    result = MagicMock()
    result.scalar_one_or_none.return_value = None

    connection.execute.return_value = result

    repository = WatermarkRepository(
        engine
    )

    watermark = repository.get_watermark(
        pipeline_name="order_pipeline",
        watermark_name="source_updated_at",
    )

    assert watermark is None


def test_update_watermark_executes_database_write() -> None:
    """Repository writes the latest successful watermark."""

    engine = MagicMock()
    connection = MagicMock()

    engine.begin.return_value.__enter__.return_value = (
        connection
    )

    repository = WatermarkRepository(
        engine
    )

    watermark = datetime(
        2026,
        10,
        18,
        13,
        30,
        tzinfo=timezone.utc,
    )

    repository.update_watermark(
        pipeline_name="order_pipeline",
        watermark_name="source_updated_at",
        watermark_value=watermark,
    )

    connection.execute.assert_called_once()


def test_repository_rejects_blank_pipeline_name() -> None:
    """Pipeline names are mandatory."""

    engine = MagicMock()

    repository = WatermarkRepository(
        engine
    )

    with pytest.raises(
        WatermarkTrackingError
    ):
        repository.get_watermark(
            pipeline_name="",
            watermark_name="source_updated_at",
        )


def test_update_watermark_requires_datetime() -> None:
    """Watermark values must use datetime objects."""

    engine = MagicMock()

    repository = WatermarkRepository(
        engine
    )

    with pytest.raises(
        WatermarkTrackingError
    ):
        repository.update_watermark(
            pipeline_name="order_pipeline",
            watermark_name="source_updated_at",
            watermark_value="2026-10-18",
        )