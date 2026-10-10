"""Unit tests for order data transformation."""

from datetime import date

import pandas as pd
import pytest

from enterprise_etl.exceptions import (
    DataValidationError,
)
from enterprise_etl.transformation.order_transformer import (
    OrderTransformer,
)


def create_order_dataframe() -> pd.DataFrame:
    """Create a reusable valid order DataFrame."""

    return pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": date(
                    2026,
                    10,
                    1,
                ),
                "order_status": "COMPLETED",
            }
        ]
    )


def test_order_transformer_adds_metadata() -> None:
    """Transformation adds ETL lineage metadata."""

    dataframe = create_order_dataframe()

    transformer = OrderTransformer()

    transformed = transformer.transform(
        dataframe=dataframe,
        batch_id="order_batch_001",
        source_name="orders.csv",
    )

    assert (
        transformed.loc[
            0,
            "batch_id",
        ]
        == "order_batch_001"
    )

    assert (
        transformed.loc[
            0,
            "source_name",
        ]
        == "orders.csv"
    )

    assert "processed_at" in transformed.columns

    assert pd.notna(
        transformed.loc[
            0,
            "processed_at",
        ]
    )


def test_order_transformer_preserves_order_values() -> None:
    """Transformation keeps business fields unchanged."""

    dataframe = create_order_dataframe()

    transformer = OrderTransformer()

    transformed = transformer.transform(
        dataframe,
        "order_batch_001",
        "orders.csv",
    )

    assert (
        transformed.loc[
            0,
            "order_id",
        ]
        == 1001
    )

    assert (
        transformed.loc[
            0,
            "customer_id",
        ]
        == 101
    )

    assert (
        transformed.loc[
            0,
            "order_date",
        ]
        == date(
            2026,
            10,
            1,
        )
    )

    assert (
        transformed.loc[
            0,
            "order_status",
        ]
        == "COMPLETED"
    )


def test_order_transformer_does_not_modify_input() -> None:
    """Transformation leaves the source DataFrame unchanged."""

    dataframe = create_order_dataframe()

    original_dataframe = dataframe.copy(
        deep=True
    )

    transformer = OrderTransformer()

    transformer.transform(
        dataframe,
        "order_batch_001",
        "orders.csv",
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_order_transformer_rejects_empty_dataframe() -> None:
    """Transformation rejects an empty order dataset."""

    transformer = OrderTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            pd.DataFrame(),
            "order_batch_001",
            "orders.csv",
        )

    assert (
        "Cannot transform an empty order dataset"
        in str(error.value)
    )


def test_order_transformer_rejects_empty_batch_id() -> None:
    """Transformation requires a batch ID."""

    dataframe = create_order_dataframe()

    transformer = OrderTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            dataframe,
            "   ",
            "orders.csv",
        )

    assert (
        "Batch ID cannot be empty"
        in str(error.value)
    )


def test_order_transformer_rejects_empty_source_name() -> None:
    """Transformation requires a source name."""

    dataframe = create_order_dataframe()

    transformer = OrderTransformer()

    with pytest.raises(
        DataValidationError
    ) as error:
        transformer.transform(
            dataframe,
            "order_batch_001",
            "   ",
        )

    assert (
        "Source name cannot be empty"
        in str(error.value)
    )