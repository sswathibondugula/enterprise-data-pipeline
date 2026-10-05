"""Unit tests for product dimension loading."""

from unittest.mock import MagicMock

import pytest

from enterprise_etl.database.product_dimension_loader import (
    ProductDimensionLoader,
)


def test_product_dimension_loader_upserts_batch() -> None:
    """Product dimension loader processes the requested batch."""

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.rowcount = 3

    loader = ProductDimensionLoader(
        engine
    )

    affected_rows = loader.load(
        "batch_001"
    )

    assert affected_rows == 3

    parameters = (
        connection.execute.call_args.args[1]
    )

    assert (
        parameters["batch_id"]
        == "batch_001"
    )

    engine.begin.assert_called_once()


def test_product_dimension_loader_rejects_empty_batch_id() -> None:
    """Warehouse product loading requires a valid batch ID."""

    engine = MagicMock()

    loader = ProductDimensionLoader(
        engine
    )

    with pytest.raises(ValueError) as error:
        loader.load("   ")

    assert (
        "Batch ID cannot be empty"
        in str(error.value)
    )

    engine.begin.assert_not_called()