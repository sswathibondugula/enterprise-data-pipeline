"""Unit tests for customer record validation."""

import pandas as pd

from enterprise_etl.validation.record_validator import (
    CustomerRecordValidator,
)


def test_record_validation_accepts_valid_records() -> None:
    """Valid customer records remain in the valid dataset."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            },
            {
                "customer_id": 102,
                "name": "Ravi",
                "country": "India",
            },
        ]
    )

    validator = CustomerRecordValidator()
    result = validator.validate(dataframe)

    assert len(result.valid_records) == 2
    assert result.rejected_records.empty


def test_record_validation_separates_invalid_records() -> None:
    """Invalid records are separated with rejection reasons."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            },
            {
                "customer_id": None,
                "name": "Ravi",
                "country": "India",
            },
            {
                "customer_id": 103,
                "name": "   ",
                "country": "India",
            },
            {
                "customer_id": 104,
                "name": "Maria",
                "country": None,
            },
        ]
    )

    validator = CustomerRecordValidator()
    result = validator.validate(dataframe)

    assert len(result.valid_records) == 1
    assert len(result.rejected_records) == 3

    assert result.rejected_records["rejection_reason"].tolist() == [
        "customer_id is required",
        "name is required",
        "country is required",
    ]


def test_record_validation_reports_multiple_errors() -> None:
    """A rejected record contains all applicable validation errors."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": None,
                "name": " ",
                "country": None,
            }
        ]
    )

    validator = CustomerRecordValidator()
    result = validator.validate(dataframe)

    assert result.rejected_records.loc[0, "rejection_reason"] == (
        "customer_id is required; "
        "name is required; "
        "country is required"
    )


def test_record_validation_does_not_modify_original_dataframe() -> None:
    """Validation leaves the original DataFrame unchanged."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": None,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )
    original_dataframe = dataframe.copy(deep=True)

    validator = CustomerRecordValidator()
    validator.validate(dataframe)

    pd.testing.assert_frame_equal(dataframe, original_dataframe)