"""Unit tests for customer dimension loading."""

from unittest.mock import MagicMock

import pytest

from enterprise_etl.database.customer_dimension_loader import (
    CustomerDimensionLoader,
)


def test_customer_dimension_loader_upserts_batch() -> None:
    """Customer dimension loader processes the requested batch."""
    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.rowcount = 2

    loader = CustomerDimensionLoader(engine)

    affected_rows = loader.load("batch_001")

    assert affected_rows == 2

    parameters = connection.execute.call_args.args[1]

    assert parameters["batch_id"] == "batch_001"

    engine.begin.assert_called_once()


def test_customer_dimension_loader_rejects_empty_batch_id() -> None:
    """Warehouse loading requires a valid batch identifier."""
    engine = MagicMock()

    loader = CustomerDimensionLoader(engine)

    with pytest.raises(ValueError) as error:
        loader.load("   ")

    assert "Batch ID cannot be empty" in str(error.value)

    engine.begin.assert_not_called()