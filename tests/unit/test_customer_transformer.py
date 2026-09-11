"""Unit tests for customer data transformation."""

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.transformation.customer_transformer import (
    CustomerTransformer,
)


def test_customer_transformer_adds_audit_metadata() -> None:
    """Transformation adds batch, source, and processing metadata."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )

    transformer = CustomerTransformer()
    transformed = transformer.transform(
        dataframe=dataframe,
        batch_id="batch_001",
        source_name="customers.csv",
    )

    assert transformed.loc[0, "batch_id"] == "batch_001"
    assert transformed.loc[0, "source_name"] == "customers.csv"
    assert "processed_at" in transformed.columns
    assert pd.notna(transformed.loc[0, "processed_at"])


def test_customer_transformer_preserves_business_columns() -> None:
    """Transformation keeps original customer values unchanged."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )

    transformer = CustomerTransformer()
    transformed = transformer.transform(
        dataframe,
        "batch_001",
        "customers.csv",
    )

    assert transformed.loc[0, "customer_id"] == 101
    assert transformed.loc[0, "name"] == "Alice"
    assert transformed.loc[0, "country"] == "Canada"


def test_customer_transformer_does_not_modify_input_dataframe() -> None:
    """Transformation leaves its input DataFrame unchanged."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )
    original_dataframe = dataframe.copy(deep=True)

    transformer = CustomerTransformer()
    transformer.transform(
        dataframe,
        "batch_001",
        "customers.csv",
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_customer_transformer_rejects_empty_dataframe() -> None:
    """Transformation rejects empty customer datasets."""
    transformer = CustomerTransformer()

    with pytest.raises(DataValidationError) as error:
        transformer.transform(
            pd.DataFrame(),
            "batch_001",
            "customers.csv",
        )

    assert "Cannot transform an empty customer dataset" in str(
        error.value
    )


def test_customer_transformer_rejects_empty_batch_id() -> None:
    """Transformation requires a meaningful batch identifier."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )

    transformer = CustomerTransformer()

    with pytest.raises(DataValidationError) as error:
        transformer.transform(
            dataframe,
            "   ",
            "customers.csv",
        )

    assert "Batch ID cannot be empty" in str(error.value)