"""Unit tests for customer data cleaning."""

import pandas as pd

from enterprise_etl.cleaning.customer_cleaner import (
    CustomerDataCleaner,
)


def test_customer_cleaner_trims_text_columns() -> None:
    """Whitespace is removed from customer text fields."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "  Alice  ",
                "country": " Canada ",
            },
            {
                "customer_id": 102,
                "name": "Ravi ",
                "country": "  India",
            },
        ]
    )

    cleaner = CustomerDataCleaner()
    cleaned = cleaner.clean(dataframe)

    assert cleaned["name"].tolist() == ["Alice", "Ravi"]
    assert cleaned["country"].tolist() == ["Canada", "India"]


def test_customer_cleaner_preserves_customer_id() -> None:
    """Cleaning does not alter customer identifiers."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": " Alice ",
                "country": " Canada ",
            }
        ]
    )

    cleaner = CustomerDataCleaner()
    cleaned = cleaner.clean(dataframe)

    assert cleaned.loc[0, "customer_id"] == 101


def test_customer_cleaner_does_not_modify_input_dataframe() -> None:
    """Cleaning leaves the original DataFrame unchanged."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": " Alice ",
                "country": " Canada ",
            }
        ]
    )
    original_dataframe = dataframe.copy(deep=True)

    cleaner = CustomerDataCleaner()
    cleaner.clean(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_customer_cleaner_preserves_internal_spaces() -> None:
    """Meaningful spaces inside text values are preserved."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": " Mary Jane ",
                "country": " New Zealand ",
            }
        ]
    )

    cleaner = CustomerDataCleaner()
    cleaned = cleaner.clean(dataframe)

    assert cleaned.loc[0, "name"] == "Mary Jane"
    assert cleaned.loc[0, "country"] == "New Zealand"