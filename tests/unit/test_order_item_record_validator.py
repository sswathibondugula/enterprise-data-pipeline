"""Unit tests for order-item record validation."""

import pandas as pd

from enterprise_etl.validation.order_item_record_validator import (
    OrderItemRecordValidator,
)


def test_order_item_validator_accepts_valid_records() -> None:
    """Valid order items remain in the valid dataset."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 1299.99,
            },
            {
                "order_item_id": 2,
                "order_id": 1001,
                "product_id": 502,
                "quantity": 2,
                "unit_price": 29.99,
            },
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    assert len(result.valid_records) == 2
    assert result.rejected_records.empty


def test_order_item_validator_rejects_missing_values() -> None:
    """Required order-item fields cannot be missing."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": None,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 1299.99,
            }
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    assert result.valid_records.empty

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "order_item_id is required"
    )


def test_order_item_validator_rejects_invalid_quantity() -> None:
    """Quantity must be a positive whole number."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 0,
                "unit_price": 1299.99,
            },
            {
                "order_item_id": 2,
                "order_id": 1001,
                "product_id": 502,
                "quantity": 2.5,
                "unit_price": 29.99,
            },
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    assert result.valid_records.empty
    assert len(result.rejected_records) == 2

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "quantity must be greater than zero"
    )

    assert (
        result.rejected_records.loc[
            1,
            "rejection_reason",
        ]
        == "quantity must be a whole number"
    )


def test_order_item_validator_rejects_invalid_price() -> None:
    """Unit price must be numeric and non-negative."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": -10,
            },
            {
                "order_item_id": 2,
                "order_id": 1001,
                "product_id": 502,
                "quantity": 1,
                "unit_price": "ABC",
            },
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    assert result.valid_records.empty

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "unit_price cannot be negative"
    )

    assert (
        result.rejected_records.loc[
            1,
            "rejection_reason",
        ]
        == "unit_price must be numeric"
    )


def test_order_item_validator_rejects_fractional_ids() -> None:
    """Identifiers must be whole numbers."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1.5,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 29.99,
            }
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    assert result.valid_records.empty

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "order_item_id must be a whole number"
    )


def test_order_item_validator_reports_multiple_errors() -> None:
    """One order-item row can contain multiple validation failures."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": None,
                "order_id": -1001,
                "product_id": "ABC",
                "quantity": 0,
                "unit_price": -5,
            }
        ]
    )

    validator = OrderItemRecordValidator()

    result = validator.validate(
        dataframe
    )

    reason = result.rejected_records.loc[
        0,
        "rejection_reason",
    ]

    assert "order_item_id is required" in reason

    assert (
        "order_id must be greater than zero"
        in reason
    )

    assert (
        "product_id must be numeric"
        in reason
    )

    assert (
        "quantity must be greater than zero"
        in reason
    )

    assert (
        "unit_price cannot be negative"
        in reason
    )


def test_order_item_validator_does_not_modify_input() -> None:
    """Validation leaves the source DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 1299.99,
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    validator = OrderItemRecordValidator()

    validator.validate(
        dataframe
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )