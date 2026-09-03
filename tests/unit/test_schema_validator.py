"""Unit tests for DataFrame structural validation."""

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


def test_schema_validation_succeeds_for_valid_dataframe() -> None:
    """Validation succeeds when required columns and rows exist."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )

    validator = DataFrameSchemaValidator(
        required_columns=("customer_id", "name", "country")
    )

    validator.validate(dataframe)


def test_schema_validation_fails_for_empty_dataframe() -> None:
    """Validation fails when the dataset contains no records."""
    dataframe = pd.DataFrame(
        columns=["customer_id", "name", "country"]
    )

    validator = DataFrameSchemaValidator(
        required_columns=("customer_id", "name", "country")
    )

    with pytest.raises(DataValidationError) as error:
        validator.validate(dataframe)

    assert "Dataset is empty" in str(error.value)


def test_schema_validation_reports_missing_columns() -> None:
    """Validation identifies required columns that are missing."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
            }
        ]
    )

    validator = DataFrameSchemaValidator(
        required_columns=("customer_id", "name", "country")
    )

    with pytest.raises(DataValidationError) as error:
        validator.validate(dataframe)

    assert "Required columns are missing: country" in str(error.value)


def test_schema_validation_rejects_unexpected_columns_in_strict_mode() -> None:
    """Strict validation rejects columns outside the expected schema."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
                "email": "alice@example.com",
            }
        ]
    )

    validator = DataFrameSchemaValidator(
        required_columns=("customer_id", "name", "country"),
        allow_extra_columns=False,
    )

    with pytest.raises(DataValidationError) as error:
        validator.validate(dataframe)

    assert "Unexpected columns found: email" in str(error.value)