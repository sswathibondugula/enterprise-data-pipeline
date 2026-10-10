"""Unit tests for order-item transformation."""

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.transformation.order_item_transformer import (
    OrderItemTransformer,
)


def create_order_item_dataframe() -> pd.DataFrame:
    """Create a reusable valid order-item DataFrame."""

    return pd.DataFrame(
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


def test_order_item_transformer_adds_metadata() -> None:
    """Transformation adds ETL lineage metadata."""

    dataframe = create_order_item_dataframe()

    transformer = OrderItemTransformer()

    transformed = transformer.transform(
        dataframe=dataframe,
        batch_id="order_item_batch_001",
        source_name="order_items.csv",
    )

    assert (
        transformed.loc[
            0,
            "batch_id",
        ]
        == "order_item_batch_001"
    )

    assert (
        transformed.loc[
            0,
            "source_name",
        ]
        == "order_items.csv"
    )

    assert "processed_at" in transformed.columns

    assert pd.notna(
        transformed.loc[
            0,
            "processed_at",
        ]
    )


def test_order_item_transformer_preserves_business_values() -> None:
    """Transformation keeps order-item business fields unchanged."""

    dataframe = create_order_item_dataframe()

    transformer = OrderItemTransformer()

    transformed = transformer.transform(
        dataframe,
        "order_item_batch_001",
        "order_items.csv",
    )

    assert transformed.loc[
        0,
        "order_item_id",
    ] == 1

    assert transformed.loc[
        0,
        "order_id",
    ] == 1001

    assert transformed.loc[
        0,
        "product_id",
    ] == 501

    assert transformed.loc[
        0,
        "quantity",
    ] == 1

    assert transformed.loc[
        0,
        "unit_price",
    ] == 1299.99


def test_order_item_transformer_does_not_modify_input() -> None:
    """Transformation leaves the input DataFrame unchanged."""

    dataframe = create_order_item_dataframe()

    original_dataframe = dataframe.copy(
        deep=True
    )

    transformer = OrderItemTransformer()

    transformer.transform(
        dataframe,
        "order_item_batch_001",
        "order_items.csv",
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_order_item_transformer_rejects_empty_dataframe() -> None:
    """Transformation rejects an empty order-item dataset."""

    transformer = OrderItemTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            pd.DataFrame(),
            "order_item_batch_001",
            "order_items.csv",
        )

    assert (
        "Cannot transform an empty order-item dataset"
        in str(error.value)
    )


def test_order_item_transformer_rejects_empty_batch_id() -> None:
    """Transformation requires a batch identifier."""

    dataframe = create_order_item_dataframe()

    transformer = OrderItemTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            dataframe,
            "   ",
            "order_items.csv",
        )

    assert (
        "Batch ID cannot be empty"
        in str(error.value)
    )


def test_order_item_transformer_rejects_empty_source_name() -> None:
    """Transformation requires a source name."""

    dataframe = create_order_item_dataframe()

    transformer = OrderItemTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            dataframe,
            "order_item_batch_001",
            "   ",
        )

    assert (
        "Source name cannot be empty"
        in str(error.value)
    )