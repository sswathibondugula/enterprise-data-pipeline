"""Unit tests for sales fact loading."""

from unittest.mock import MagicMock

from enterprise_etl.database.sales_fact_loader import (
    SalesFactLoader,
)


def test_sales_fact_loader_executes_fact_load() -> None:
    """Sales fact loader executes the warehouse upsert."""

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.rowcount = 4

    loader = SalesFactLoader(
        engine
    )

    affected_rows = loader.load()

    assert affected_rows == 4

    engine.begin.assert_called_once()

    connection.execute.assert_called_once()


def test_sales_fact_loader_returns_rowcount() -> None:
    """Loader returns the number of rows affected."""

    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.rowcount = 3

    loader = SalesFactLoader(
        engine
    )

    affected_rows = loader.load()

    assert affected_rows == 3