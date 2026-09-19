"""Unit tests for customer staging database loading."""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from enterprise_etl.database.customer_staging_loader import (
    CustomerStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError


def test_customer_staging_loader_returns_zero_for_empty_dataframe() -> None:
    """Empty datasets do not perform a database load."""
    engine = MagicMock()
    loader = CustomerStagingLoader(engine)

    loaded_count = loader.load(pd.DataFrame())

    assert loaded_count == 0
    engine.begin.assert_not_called()


def test_customer_staging_loader_rejects_missing_columns() -> None:
    """Staging load requires all expected customer columns."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            }
        ]
    )

    loader = CustomerStagingLoader(MagicMock())

    with pytest.raises(DataValidationError) as error:
        loader.load(dataframe)

    assert "Customer staging columns are missing:" in str(
        error.value
    )


def test_customer_staging_loader_inserts_customer_records() -> None:
    """Eligible customer records are sent to the database."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
                "batch_id": "batch_001",
                "source_name": "customers.csv",
                "processed_at": pd.Timestamp(
                    "2026-09-18T08:00:00Z"
                ),
            }
        ]
    )

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    loader = CustomerStagingLoader(engine)

    loaded_count = loader.load(dataframe)

    assert loaded_count == 1
    engine.begin.assert_called_once()
    connection.execute.assert_called_once()

    parameters = connection.execute.call_args.args[1]

    assert parameters[0]["customer_id"] == 101
    assert parameters[0]["customer_name"] == "Alice"
    assert parameters[0]["country"] == "Canada"
    assert parameters[0]["batch_id"] == "batch_001"