"""Unit tests for product data cleaning."""

import pandas as pd

from enterprise_etl.cleaning.product_cleaner import (
    ProductDataCleaner,
)


def test_product_cleaner_trims_text_columns() -> None:
    """Product text values are stripped of surrounding whitespace."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": 501,
                "product_name": " Laptop Pro ",
                "category": " Laptops ",
                "unit_price": 1299.99,
            },
            {
                "product_id": 502,
                "product_name": " Wireless Mouse ",
                "category": " Accessories ",
                "unit_price": 29.99,
            },
        ]
    )

    cleaner = ProductDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert cleaned["product_name"].tolist() == [
        "Laptop Pro",
        "Wireless Mouse",
    ]

    assert cleaned["category"].tolist() == [
        "Laptops",
        "Accessories",
    ]


def test_product_cleaner_normalizes_numeric_columns() -> None:
    """Product identifiers and prices receive consistent numeric types."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": "501",
                "product_name": "Laptop Pro",
                "category": "Laptops",
                "unit_price": "1299.99",
            }
        ]
    )

    cleaner = ProductDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert cleaned.loc[0, "product_id"] == 501
    assert cleaned.loc[0, "unit_price"] == 1299.99

    assert cleaned["product_id"].dtype == "int64"
    assert cleaned["unit_price"].dtype == "float64"


def test_product_cleaner_preserves_internal_spaces() -> None:
    """Meaningful spaces inside product names remain unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": 501,
                "product_name": " Laptop Pro Max ",
                "category": " Premium Laptops ",
                "unit_price": 1499.99,
            }
        ]
    )

    cleaner = ProductDataCleaner()

    cleaned = cleaner.clean(dataframe)

    assert (
        cleaned.loc[0, "product_name"]
        == "Laptop Pro Max"
    )

    assert (
        cleaned.loc[0, "category"]
        == "Premium Laptops"
    )


def test_product_cleaner_does_not_modify_input() -> None:
    """Cleaning leaves the input DataFrame unchanged."""

    dataframe = pd.DataFrame(
        [
            {
                "product_id": "501",
                "product_name": " Laptop Pro ",
                "category": " Laptops ",
                "unit_price": "1299.99",
            }
        ]
    )

    original_dataframe = dataframe.copy(
        deep=True
    )

    cleaner = ProductDataCleaner()

    cleaner.clean(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )