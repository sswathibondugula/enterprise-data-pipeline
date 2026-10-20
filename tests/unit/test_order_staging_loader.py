"""Unit tests for the order staging loader."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pandas as pd
import pytest
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.database.order_staging_loader import (
    OrderStagingLoader,
)
from enterprise_etl.exceptions import (
    DatabaseLoadError,
    DataValidationError,
)


def create_order_dataframe() -> pd.DataFrame:
    """Create a valid transformed order DataFrame for loader tests."""

    return pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": datetime(
                    2026,
                    10,
                    1,
                ).date(),
                "order_status": "COMPLETED",
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:15:00Z"
                ),
                "batch_id": "order_batch_test",
                "source_name": "orders.csv",
                "processed_at": datetime(
                    2026,
                    10,
                    20,
                    7,
                    0,
                    tzinfo=timezone.utc,
                ),
            }
        ]
    )


def test_order_staging_loader_inserts_order_records() -> None:
    """Valid order records are inserted into staging."""

    engine = MagicMock()
    connection = MagicMock()

    engine.begin.return_value.__enter__.return_value = (
        connection
    )

    dataframe = create_order_dataframe()

    loader = OrderStagingLoader(
        engine
    )

    loaded_records = loader.load(
        dataframe
    )

    assert loaded_records == 1

    connection.execute.assert_called_once()

    _, records = (
        connection.execute.call_args.args
    )

    assert len(records) == 1

    record = records[0]

    assert record["order_id"] == 1001
    assert record["customer_id"] == 101

    assert (
        record["order_status"]
        == "COMPLETED"
    )

    assert (
        record["batch_id"]
        == "order_batch_test"
    )

    assert (
        record["source_name"]
        == "orders.csv"
    )


def test_order_staging_loader_includes_source_updated_at() -> None:
    """Source update timestamp is passed to PostgreSQL."""

    engine = MagicMock()
    connection = MagicMock()

    engine.begin.return_value.__enter__.return_value = (
        connection
    )

    dataframe = create_order_dataframe()

    loader = OrderStagingLoader(
        engine
    )

    loaded_records = loader.load(
        dataframe
    )

    assert loaded_records == 1

    connection.execute.assert_called_once()

    _, records = (
        connection.execute.call_args.args
    )

    source_updated_at = records[0][
        "source_updated_at"
    ]

    assert isinstance(
        source_updated_at,
        datetime,
    )

    assert (
        source_updated_at
        == pd.Timestamp(
            "2026-10-18T10:15:00Z"
        ).to_pydatetime()
    )

    assert (
        source_updated_at.tzinfo
        is not None
    )


def test_order_staging_loader_returns_zero_for_empty_dataframe() -> None:
    """An empty DataFrame causes no database insert."""

    engine = MagicMock()

    loader = OrderStagingLoader(
        engine
    )

    dataframe = pd.DataFrame()

    loaded_records = loader.load(
        dataframe
    )

    assert loaded_records == 0

    engine.begin.assert_not_called()


def test_order_staging_loader_rejects_missing_required_columns() -> None:
    """Loader rejects transformed data with missing columns."""

    engine = MagicMock()

    loader = OrderStagingLoader(
        engine
    )

    dataframe = create_order_dataframe().drop(
        columns=[
            "source_updated_at",
        ]
    )

    with pytest.raises(
        DataValidationError,
        match=(
            "Order staging columns are missing: "
            "source_updated_at"
        ),
    ):
        loader.load(
            dataframe
        )

    engine.begin.assert_not_called()


def test_order_staging_loader_wraps_database_errors() -> None:
    """SQLAlchemy failures become application DatabaseLoadError."""

    engine = MagicMock()
    connection = MagicMock()

    engine.begin.return_value.__enter__.return_value = (
        connection
    )

    connection.execute.side_effect = (
        SQLAlchemyError(
            "Database failure"
        )
    )

    dataframe = create_order_dataframe()

    loader = OrderStagingLoader(
        engine
    )

    with pytest.raises(
        DatabaseLoadError,
        match=(
            "Unable to load order records "
            "into staging.stg_orders"
        ),
    ):
        loader.load(
            dataframe
        )