"""Unit tests for raw landing storage."""

from pathlib import Path

import pytest

from enterprise_etl.exceptions import DataIngestionError
from enterprise_etl.ingestion.raw_landing import RawLandingStore


def test_raw_landing_preserves_source_file(tmp_path: Path) -> None:
    """Source files are copied into the requested raw batch."""
    incoming = tmp_path / "incoming"
    raw = tmp_path / "raw"
    incoming.mkdir()
    raw.mkdir()

    source_path = incoming / "customers.csv"
    source_path.write_text(
        "customer_id,name\n101,Alice\n",
        encoding="utf-8",
    )

    store = RawLandingStore(raw)
    destination = store.store(source_path, "batch_001")

    assert destination == raw / "batch_001" / "customers.csv"
    assert destination.exists()
    assert destination.read_text(encoding="utf-8") == (
        source_path.read_text(encoding="utf-8")
    )
    assert source_path.exists()


def test_raw_landing_rejects_duplicate_file(tmp_path: Path) -> None:
    """Existing raw files cannot be silently overwritten."""
    incoming = tmp_path / "incoming"
    raw = tmp_path / "raw"
    incoming.mkdir()
    raw.mkdir()

    source_path = incoming / "customers.csv"
    source_path.write_text("customer_id\n101\n", encoding="utf-8")

    store = RawLandingStore(raw)
    store.store(source_path, "batch_001")

    with pytest.raises(DataIngestionError) as error:
        store.store(source_path, "batch_001")

    assert "Raw file already exists:" in str(error.value)


def test_raw_landing_fails_for_missing_source(tmp_path: Path) -> None:
    """Missing source files raise an ingestion error."""
    raw = tmp_path / "raw"
    raw.mkdir()

    source_path = tmp_path / "missing.csv"
    store = RawLandingStore(raw)

    with pytest.raises(DataIngestionError) as error:
        store.store(source_path, "batch_001")

    assert "Source file does not exist:" in str(error.value)