"""Cleaning operations for validated customer data."""

import pandas as pd


class CustomerDataCleaner:
    """Apply safe, deterministic cleaning to customer records."""

    TEXT_COLUMNS = ("name", "country")

    def clean(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        """Return a cleaned copy of the customer DataFrame."""
        cleaned = dataframe.copy(deep=True)

        for column in self.TEXT_COLUMNS:
            cleaned[column] = (
                cleaned[column]
                .astype("string")
                .str.strip()
            )

        return cleaned