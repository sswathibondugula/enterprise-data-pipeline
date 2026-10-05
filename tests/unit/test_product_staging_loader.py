"""Unit tests for product staging database loading."""

from decimal import Decimal
from unittest.mock import MagicMock

import pandas as pd
import pytest

from enterprise_etl.database.product_staging_loader import (
    ProductStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError


def test_product_staging_loader_returns_zero_for_empty_dataframe() -> None:
    """Empty product datasets do not trigger a database load."""

    engine = MagicMock()

    loader = ProductStagingLoader(engine)

    loaded_count = loader.load(
        pd.DataFrame()
    )

    assert loaded_count == 0

    engine.begin.assert_not_called()


def test_product_staging_loader_rejects_missing_columns() -> None:
    """Product staging requires all expected columns."""

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

    loader = ProductStagingLoader(
        MagicMock()
    )

    with pytest.raises(
        DataValidationError
    ) as error:
        loader.load(dataframe)

    assert (
        "Product staging columns are missing:"
        in str(error.value)
    )


def test_product_staging_loader_inserts_product_records() -> None:
    """Processed product records are sent to PostgreSQL staging."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": 501,
                "product_name": "Laptop Pro",
                "category": "Laptops",
                "unit_price": 1299.99,
                "batch_id": "batch_001",
                "source_name": "products.csv",
                "processed_at": pd.Timestamp(
                    "2026-10-04T12:00:00Z"
                ),
            }
        ]
    )

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    loader = ProductStagingLoader(
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

    assert parameters[0]["product_id"] == 501

    assert (
        parameters[0]["product_name"]
        == "Laptop Pro"
    )

    assert (
        parameters[0]["category"]
        == "Laptops"
    )

    assert (
        parameters[0]["unit_price"]
        == Decimal("1299.99")
    )

    assert (
        parameters[0]["batch_id"]
        == "batch_001"
    )

    assert (
        parameters[0]["source_name"]
        == "products.csv"
    )