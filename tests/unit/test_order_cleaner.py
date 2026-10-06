"""Unit tests for order data cleaning."""

from datetime import date

import pandas as pd

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)


def test_order_cleaner_normalizes_identifiers() -> None:
    """Order and customer identifiers become integers."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": "1001",
                "customer_id": "101",
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            }
        ]
    )

    cleaner = OrderDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert cleaned.loc[0, "order_id"] == 1001
    assert cleaned.loc[0, "customer_id"] == 101

    assert cleaned["order_id"].dtype == "int64"
    assert cleaned["customer_id"].dtype == "int64"


def test_order_cleaner_converts_order_date() -> None:
    """Order date becomes a Python date value."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            }
        ]
    )

    cleaner = OrderDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert (
        cleaned.loc[0, "order_date"]
        == date(2026, 10, 1)
    )

    assert isinstance(
        cleaned.loc[0, "order_date"],
        date,
    )


def test_order_cleaner_normalizes_status() -> None:
    """Order status is trimmed and converted to uppercase."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": " completed ",
            },
            {
                "order_id": 1002,
                "customer_id": 101,
                "order_date": "2026-10-02",
                "order_status": "Pending",
            },
        ]
    )

    cleaner = OrderDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert cleaned["order_status"].tolist() == [
        "COMPLETED",
        "PENDING",
    ]


def test_order_cleaner_preserves_other_values() -> None:
    """Cleaning preserves the business meaning of order records."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": "1001",
                "customer_id": "101",
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            }
        ]
    )

    cleaner = OrderDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert cleaned.loc[0, "order_id"] == 1001
    assert cleaned.loc[0, "customer_id"] == 101

    assert (
        cleaned.loc[0, "order_status"]
        == "COMPLETED"
    )


def test_order_cleaner_does_not_modify_input() -> None:
    """Cleaning leaves the original DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "order_id": "1001",
                "customer_id": "101",
                "order_date": "2026-10-01",
                "order_status": " completed ",
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    cleaner = OrderDataCleaner()

    cleaner.clean(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )