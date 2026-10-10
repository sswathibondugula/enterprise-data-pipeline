"""Unit tests for order-item staging database loading."""

from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from enterprise_etl.database.order_item_staging_loader import (
    OrderItemStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError


def test_order_item_staging_loader_returns_zero_for_empty_dataframe() -> None:
    """Empty datasets do not trigger a database operation."""

    engine = MagicMock()

    loader = OrderItemStagingLoader(
        engine
    )

    loaded_count = loader.load(
        pd.DataFrame()
    )

    assert loaded_count == 0

    engine.begin.assert_not_called()


def test_order_item_staging_loader_rejects_missing_columns() -> None:
    """Order-item staging requires all expected columns."""

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

    loader = OrderItemStagingLoader(
        MagicMock()
    )

    with pytest.raises(
        DataValidationError
    ) as error:
        loader.load(
            dataframe
        )

    assert (
        "Order-item staging columns are missing:"
        in str(error.value)
    )


def test_order_item_staging_loader_inserts_records() -> None:
    """Transformed order items are sent to PostgreSQL staging."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 1299.99,
                "batch_id": "order_item_batch_001",
                "source_name": "order_items.csv",
                "processed_at": pd.Timestamp(
                    "2026-10-10T12:00:00Z"
                ),
            }
        ]
    )

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    loader = OrderItemStagingLoader(
        engine
    )

    loaded_count = loader.load(
        dataframe
    )

    assert loaded_count == 1

    engine.begin.assert_called_once()

    connection.execute.assert_called_once()

    parameters = (
        connection.execute.call_args.args[1]
    )

    assert (
        parameters[0]["order_item_id"]
        == 1
    )

    assert (
        parameters[0]["order_id"]
        == 1001
    )

    assert (
        parameters[0]["product_id"]
        == 501
    )

    assert (
        parameters[0]["quantity"]
        == 1
    )

    assert (
        parameters[0]["unit_price"]
        == Decimal("1299.99")
    )

    assert (
        parameters[0]["batch_id"]
        == "order_item_batch_001"
    )

    assert (
        parameters[0]["source_name"]
        == "order_items.csv"
    )


def test_order_item_staging_loader_inserts_multiple_records() -> None:
    """Multiple order items are prepared and inserted together."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": 1299.99,
                "batch_id": "order_item_batch_001",
                "source_name": "order_items.csv",
                "processed_at": pd.Timestamp(
                    "2026-10-10T12:00:00Z"
                ),
            },
            {
                "order_item_id": 2,
                "order_id": 1001,
                "product_id": 502,
                "quantity": 2,
                "unit_price": 29.99,
                "batch_id": "order_item_batch_001",
                "source_name": "order_items.csv",
                "processed_at": pd.Timestamp(
                    "2026-10-10T12:00:00Z"
                ),
            },
        ]
    )

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    loader = OrderItemStagingLoader(
        engine
    )

    loaded_count = loader.load(
        dataframe
    )

    assert loaded_count == 2

    parameters = (
        connection.execute.call_args.args[1]
    )

    assert len(parameters) == 2

    assert (
        parameters[1]["product_id"]
        == 502
    )

    assert (
        parameters[1]["quantity"]
        == 2
    )

    assert (
        parameters[1]["unit_price"]
        == Decimal("29.99")
    )