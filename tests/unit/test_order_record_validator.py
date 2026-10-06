"""Unit tests for order record validation."""

import pandas as pd

from enterprise_etl.validation.order_record_validator import (
    OrderRecordValidator,
)


def create_validator() -> OrderRecordValidator:
    """Create the standard order validator used by tests."""

    return OrderRecordValidator(
        allowed_statuses=(
            "PENDING",
            "COMPLETED",
            "CANCELLED",
        )
    )


def test_order_validator_accepts_valid_orders() -> None:
    """Valid orders remain in the valid dataset."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            },
            {
                "order_id": 1002,
                "customer_id": 101,
                "order_date": "2026-10-02",
                "order_status": "PENDING",
            },
        ]
    )

    validator = create_validator()

    result = validator.validate(dataframe)

    assert len(result.valid_records) == 2
    assert result.rejected_records.empty


def test_order_validator_rejects_invalid_identifiers() -> None:
    """Invalid order and customer identifiers are rejected."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": None,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            },
            {
                "order_id": 1002,
                "customer_id": "ABC",
                "order_date": "2026-10-02",
                "order_status": "COMPLETED",
            },
            {
                "order_id": -1003,
                "customer_id": 101,
                "order_date": "2026-10-03",
                "order_status": "PENDING",
            },
        ]
    )

    validator = create_validator()

    result = validator.validate(dataframe)

    assert result.valid_records.empty
    assert len(result.rejected_records) == 3

    reasons = result.rejected_records[
        "rejection_reason"
    ].tolist()

    assert reasons == [
        "order_id is required",
        "customer_id must be numeric",
        "order_id must be greater than zero",
    ]


def test_order_validator_rejects_invalid_dates() -> None:
    """Invalid calendar dates are rejected."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-02-30",
                "order_status": "COMPLETED",
            },
            {
                "order_id": 1002,
                "customer_id": 101,
                "order_date": "10/02/2026",
                "order_status": "PENDING",
            },
        ]
    )

    validator = create_validator()

    result = validator.validate(dataframe)

    assert result.valid_records.empty

    assert len(result.rejected_records) == 2

    assert (
        result.rejected_records[
            "rejection_reason"
        ]
        .str.contains(
            "order_date must be a valid"
        )
        .all()
    )


def test_order_validator_rejects_unknown_status() -> None:
    """Unsupported order statuses are rejected."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "UNKNOWN",
            }
        ]
    )

    validator = create_validator()

    result = validator.validate(dataframe)

    assert result.valid_records.empty

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "order_status is not allowed"
    )


def test_order_validator_accepts_status_case_and_spaces() -> None:
    """Status validation ignores case and surrounding spaces."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": " completed ",
            }
        ]
    )

    validator = create_validator()

    result = validator.validate(dataframe)

    assert len(result.valid_records) == 1
    assert result.rejected_records.empty


def test_order_validator_does_not_modify_input() -> None:
    """Validation leaves the original DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    validator = create_validator()

    validator.validate(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )