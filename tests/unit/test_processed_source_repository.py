"""Unit tests for processed-source tracking."""

import hashlib
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from enterprise_etl.database.processed_source_repository import (
    ProcessedSourceRepository,
    SourceFingerprint,
)
from enterprise_etl.exceptions import DataIngestionError

def test_calculate_fingerprint_returns_expected_hash(
    tmp_path: Path,
) -> None:
    """File fingerprint matches the expected SHA-256 value."""

    source_path = tmp_path / "orders.csv"

    content = (
        b"order_id,customer_id\n"
        b"1001,101\n"
    )

    source_path.write_bytes(
        content
    )

    fingerprint = (
        ProcessedSourceRepository.calculate_fingerprint(
            source_path
        )
    )

    expected_hash = hashlib.sha256(
        content
    ).hexdigest()

    assert (
        fingerprint.source_hash
        == expected_hash
    )

    assert (
        fingerprint.source_size_bytes
        == len(content)
    )

def test_calculate_fingerprint_rejects_missing_file(
    tmp_path: Path,
) -> None:
    """Fingerprint calculation requires an existing file."""

    source_path = (
        tmp_path
        / "missing.csv"
    )

    with pytest.raises(
        DataIngestionError
    ) as error:
        ProcessedSourceRepository.calculate_fingerprint(
            source_path
        )

    assert (
        "Source file does not exist"
        in str(error.value)
    )


def test_is_processed_returns_true_when_hash_exists() -> None:
    """Repository identifies a source that was already processed."""

    engine = MagicMock()

    connection = (
        engine.connect.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.scalar_one.return_value = (
        True
    )

    repository = ProcessedSourceRepository(
        engine
    )

    result = repository.is_processed(
        pipeline_name="order_pipeline",
        source_hash="abc123",
    )

    assert result is True

    engine.connect.assert_called_once()

    connection.execute.assert_called_once()


def test_is_processed_returns_false_for_new_hash() -> None:
    """Repository identifies a source that has not been processed."""

    engine = MagicMock()

    connection = (
        engine.connect.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.scalar_one.return_value = (
        False
    )

    repository = ProcessedSourceRepository(
        engine
    )

    result = repository.is_processed(
        pipeline_name="order_pipeline",
        source_hash="new_hash",
    )

    assert result is False


def test_register_processed_stores_source_metadata() -> None:
    """Successfully processed source metadata is sent to PostgreSQL."""

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    repository = ProcessedSourceRepository(
        engine
    )

    fingerprint = SourceFingerprint(
        source_hash="abc123",
        source_size_bytes=2048,
    )

    repository.register_processed(
        pipeline_name="order_pipeline",
        source_name="orders.csv",
        fingerprint=fingerprint,
        batch_id="order_batch_001",
    )

    engine.begin.assert_called_once()

    connection.execute.assert_called_once()

    parameters = (
        connection.execute.call_args.args[1]
    )

    assert (
        parameters["pipeline_name"]
        == "order_pipeline"
    )

    assert (
        parameters["source_name"]
        == "orders.csv"
    )

    assert (
        parameters["source_hash"]
        == "abc123"
    )

    assert (
        parameters["source_size_bytes"]
        == 2048
    )

    assert (
        parameters["batch_id"]
        == "order_batch_001"
    )