"""Unit tests for product data transformation."""

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.transformation.product_transformer import (
    ProductTransformer,
)


def test_product_transformer_adds_audit_metadata() -> None:
    """Transformation adds ETL lineage fields."""

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

    transformer = ProductTransformer()

    transformed = transformer.transform(
        dataframe=dataframe,
        batch_id="batch_001",
        source_name="products.csv",
    )

    assert transformed.loc[0, "batch_id"] == "batch_001"

    assert (
        transformed.loc[0, "source_name"]
        == "products.csv"
    )

    assert "processed_at" in transformed.columns

    assert pd.notna(
        transformed.loc[0, "processed_at"]
    )


def test_product_transformer_preserves_product_values() -> None:
    """Transformation keeps existing product values unchanged."""

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

    transformer = ProductTransformer()

    transformed = transformer.transform(
        dataframe,
        "batch_001",
        "products.csv",
    )

    assert transformed.loc[0, "product_id"] == 501

    assert (
        transformed.loc[0, "product_name"]
        == "Laptop Pro"
    )

    assert (
        transformed.loc[0, "category"]
        == "Laptops"
    )

    assert (
        transformed.loc[0, "unit_price"]
        == 1299.99
    )


def test_product_transformer_does_not_modify_input() -> None:
    """Transformation leaves its input DataFrame unchanged."""

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

    transformer = ProductTransformer()

    transformer.transform(
        dataframe,
        "batch_001",
        "products.csv",
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_product_transformer_rejects_empty_dataframe() -> None:
    """Transformation rejects empty product datasets."""

    transformer = ProductTransformer()

    with pytest.raises(DataValidationError) as error:
        transformer.transform(
            pd.DataFrame(),
            "batch_001",
            "products.csv",
        )

    assert (
        "Cannot transform an empty product dataset"
        in str(error.value)
    )


def test_product_transformer_rejects_empty_batch_id() -> None:
    """Transformation requires a meaningful batch identifier."""

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

    transformer = ProductTransformer()

    with pytest.raises(DataValidationError) as error:
        transformer.transform(
            dataframe,
            "   ",
            "products.csv",
        )

    assert (
        "Batch ID cannot be empty"
        in str(error.value)
    )


def test_product_transformer_rejects_empty_source_name() -> None:
    """Transformation requires a meaningful source name."""

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

    transformer = ProductTransformer()

    with pytest.raises(DataValidationError) as error:
        transformer.transform(
            dataframe,
            "batch_001",
            "   ",
        )

    assert (
        "Source name cannot be empty"
        in str(error.value)
    )