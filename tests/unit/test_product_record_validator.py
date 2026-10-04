"""Unit tests for product record validation."""

import pandas as pd

from enterprise_etl.validation.product_record_validator import (
    ProductRecordValidator,
)


def test_product_validator_accepts_valid_products() -> None:
    """Valid products remain in the valid dataset."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": 501,
                "product_name": "Laptop Pro",
                "category": "Laptops",
                "unit_price": 1299.99,
            },
            {
                "product_id": 502,
                "product_name": "Wireless Mouse",
                "category": "Accessories",
                "unit_price": 29.99,
            },
        ]
    )

    validator = ProductRecordValidator()

    result = validator.validate(dataframe)

    assert len(result.valid_records) == 2

    assert result.rejected_records.empty


def test_product_validator_rejects_invalid_products() -> None:
    """Invalid products are separated with reasons."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": None,
                "product_name": "Laptop",
                "category": "Laptops",
                "unit_price": 999.99,
            },
            {
                "product_id": 502,
                "product_name": " ",
                "category": "Accessories",
                "unit_price": 29.99,
            },
            {
                "product_id": 503,
                "product_name": "Keyboard",
                "category": "Accessories",
                "unit_price": -10,
            },
            {
                "product_id": 504,
                "product_name": "Monitor",
                "category": "Displays",
                "unit_price": "ABC",
            },
        ]
    )

    validator = ProductRecordValidator()

    result = validator.validate(dataframe)

    assert result.valid_records.empty

    assert len(result.rejected_records) == 4

    reasons = (
        result.rejected_records[
            "rejection_reason"
        ].tolist()
    )

    assert reasons == [
        "product_id is required",
        "product_name is required",
        "unit_price cannot be negative",
        "unit_price must be numeric",
    ]


def test_product_validator_reports_multiple_errors() -> None:
    """One product can contain multiple validation failures."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": None,
                "product_name": " ",
                "category": "",
                "unit_price": -20,
            }
        ]
    )

    validator = ProductRecordValidator()

    result = validator.validate(dataframe)

    assert len(result.rejected_records) == 1

    reason = result.rejected_records.loc[
        0,
        "rejection_reason",
    ]

    assert "product_id is required" in reason
    assert "product_name is required" in reason
    assert "category is required" in reason
    assert "unit_price cannot be negative" in reason


def test_product_validator_does_not_modify_input() -> None:
    """Validation leaves the source DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": 501,
                "product_name": "Laptop Pro",
                "category": "Laptops",
                "unit_price": 1299.99,
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    validator = ProductRecordValidator()

    validator.validate(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )