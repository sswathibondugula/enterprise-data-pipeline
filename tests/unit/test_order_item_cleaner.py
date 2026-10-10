"""Unit tests for order-item data cleaning."""

import pandas as pd

from enterprise_etl.cleaning.order_item_cleaner import (
    OrderItemDataCleaner,
)


def test_order_item_cleaner_normalizes_identifiers() -> None:
    """Order-item identifiers become integers."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": "1",
                "order_id": "1001",
                "product_id": "501",
                "quantity": "2",
                "unit_price": "29.99",
            }
        ]
    )

    cleaner = OrderItemDataCleaner()

    cleaned = cleaner.clean(
        dataframe
    )

    assert cleaned.loc[
        0,
        "order_item_id",
    ] == 1

    assert cleaned.loc[
        0,
        "order_id",
    ] == 1001

    assert cleaned.loc[
        0,
        "product_id",
    ] == 501

    assert (
        cleaned["order_item_id"].dtype
        == "int64"
    )

    assert (
        cleaned["order_id"].dtype
        == "int64"
    )

    assert (
        cleaned["product_id"].dtype
        == "int64"
    )


def test_order_item_cleaner_normalizes_quantity() -> None:
    """Quantity becomes an integer."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": "2",
                "unit_price": 29.99,
            }
        ]
    )

    cleaner = OrderItemDataCleaner()

    cleaned = cleaner.clean(
        dataframe
    )

    assert cleaned.loc[
        0,
        "quantity",
    ] == 2

    assert (
        cleaned["quantity"].dtype
        == "int64"
    )


def test_order_item_cleaner_normalizes_unit_price() -> None:
    """Unit price becomes a numeric decimal-capable value."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": 1,
                "order_id": 1001,
                "product_id": 501,
                "quantity": 1,
                "unit_price": "1299.99",
            }
        ]
    )

    cleaner = OrderItemDataCleaner()

    cleaned = cleaner.clean(
        dataframe
    )

    assert (
        cleaned.loc[
            0,
            "unit_price",
        ]
        == 1299.99
    )

    assert (
        cleaned["unit_price"].dtype
        == "float64"
    )


def test_order_item_cleaner_handles_multiple_rows() -> None:
    """Cleaning is applied consistently across all order items."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": "1",
                "order_id": "1001",
                "product_id": "501",
                "quantity": "1",
                "unit_price": "1299.99",
            },
            {
                "order_item_id": "2",
                "order_id": "1001",
                "product_id": "502",
                "quantity": "2",
                "unit_price": "29.99",
            },
        ]
    )

    cleaner = OrderItemDataCleaner()

    cleaned = cleaner.clean(
        dataframe
    )

    assert cleaned[
        "order_item_id"
    ].tolist() == [
        1,
        2,
    ]

    assert cleaned[
        "quantity"
    ].tolist() == [
        1,
        2,
    ]

    assert cleaned[
        "unit_price"
    ].tolist() == [
        1299.99,
        29.99,
    ]


def test_order_item_cleaner_does_not_modify_input() -> None:
    """Cleaning leaves the original DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "order_item_id": "1",
                "order_id": "1001",
                "product_id": "501",
                "quantity": "2",
                "unit_price": "29.99",
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    cleaner = OrderItemDataCleaner()

    cleaner.clean(
        dataframe
    )

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )