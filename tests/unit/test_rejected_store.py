"""Unit tests for rejected-record storage."""

from pathlib import Path

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.validation.rejected_store import (
    RejectedRecordStore,
)


def test_rejected_store_writes_records_with_metadata(
    tmp_path: Path,
) -> None:
    """Rejected records are stored with operational metadata."""
    rejected_root = tmp_path / "rejected"
    rejected_root.mkdir()

    rejected_records = pd.DataFrame(
        [
            {
                "customer_id": None,
                "name": "Ravi",
                "country": "India",
                "rejection_reason": "customer_id is required",
            }
        ]
    )

    store = RejectedRecordStore(rejected_root)

    destination = store.store(
        rejected_records=rejected_records,
        batch_id="batch_001",
        source_name="customers.csv",
    )

    assert destination == (
        rejected_root / "batch_001" / "customers_rejected.csv"
    )
    assert destination.exists()

    stored_records = pd.read_csv(destination)

    assert stored_records.loc[0, "batch_id"] == "batch_001"
    assert stored_records.loc[0, "source_name"] == "customers.csv"
    assert "rejected_at" in stored_records.columns


def test_rejected_store_does_not_modify_input_dataframe(
    tmp_path: Path,
) -> None:
    """Storing rejected records leaves the input DataFrame unchanged."""
    rejected_root = tmp_path / "rejected"
    rejected_root.mkdir()

    rejected_records = pd.DataFrame(
        [
            {
                "customer_id": None,
                "rejection_reason": "customer_id is required",
            }
        ]
    )
    original_records = rejected_records.copy(deep=True)

    store = RejectedRecordStore(rejected_root)
    store.store(
        rejected_records,
        "batch_001",
        "customers.csv",
    )

    pd.testing.assert_frame_equal(
        rejected_records,
        original_records,
    )


def test_rejected_store_rejects_duplicate_output(
    tmp_path: Path,
) -> None:
    """Existing quarantine files cannot be silently overwritten."""
    rejected_root = tmp_path / "rejected"
    rejected_root.mkdir()

    rejected_records = pd.DataFrame(
        [{"rejection_reason": "test failure"}]
    )

    store = RejectedRecordStore(rejected_root)

    store.store(
        rejected_records,
        "batch_001",
        "customers.csv",
    )

    with pytest.raises(DataValidationError) as error:
        store.store(
            rejected_records,
            "batch_001",
            "customers.csv",
        )

    assert "Rejected-record file already exists:" in str(error.value)


def test_rejected_store_fails_for_empty_dataframe(
    tmp_path: Path,
) -> None:
    """Empty rejected datasets are not written to storage."""
    rejected_root = tmp_path / "rejected"
    rejected_root.mkdir()

    store = RejectedRecordStore(rejected_root)

    with pytest.raises(DataValidationError) as error:
        store.store(
            pd.DataFrame(),
            "batch_001",
            "customers.csv",
        )

    assert "No rejected records to store" in str(error.value)