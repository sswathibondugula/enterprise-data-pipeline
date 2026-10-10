"""Unit tests for order staging database loading."""

from datetime import date
from unittest.mock import MagicMock

import pandas as pd
import pytest

from enterprise_etl.database.order_staging_loader import (
    OrderStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError


def test_order_staging_loader_returns_zero_for_empty_dataframe() -> None:
    """Empty order datasets do not trigger a database operation."""

    engine = MagicMock()

    loader = OrderStagingLoader(
        engine
    )

    loaded_count = loader.load(
        pd.DataFrame()
    )

    assert loaded_count == 0

    engine.begin.assert_not_called()


def test_order_staging_loader_rejects_missing_columns() -> None:
    """Order staging requires all expected columns."""

    dataframe = pd.DataFrame(
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

    loader = OrderStagingLoader(
        MagicMock()
    )

    with pytest.raises(
        DataValidationError
    ) as error:
        loader.load(
            dataframe
        )

    assert (
        "Order staging columns are missing:"
        in str(error.value)
    )


def test_order_staging_loader_inserts_order_records() -> None:
    """Transformed orders are sent to PostgreSQL staging."""

    dataframe = pd.DataFrame(
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
                "batch_id": "order_batch_001",
                "source_name": "orders.csv",
                "processed_at": pd.Timestamp(
                    "2026-10-06T12:00:00Z"
                ),
            }
        ]
    )

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    loader = OrderStagingLoader(
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
        parameters[0]["order_id"]
        == 1001
    )

    assert (
        parameters[0]["customer_id"]
        == 101
    )

    assert (
        parameters[0]["order_date"]
        == date(
            2026,
            10,
            1,
        )
    )

    assert (
        parameters[0]["order_status"]
        == "COMPLETED"
    )

    assert (
        parameters[0]["batch_id"]
        == "order_batch_001"
    )

    assert (
        parameters[0]["source_name"]
        == "orders.csv"
    )