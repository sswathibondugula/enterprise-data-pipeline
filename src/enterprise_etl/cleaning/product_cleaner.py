"""Cleaning operations for validated product data."""

import pandas as pd


class ProductDataCleaner:
    """Apply safe cleaning and type normalization to product records."""

    TEXT_COLUMNS = (
        "product_name",
        "category",
    )

    def clean(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return a cleaned copy of validated product records."""

        cleaned = dataframe.copy(deep=True)

        for column in self.TEXT_COLUMNS:
            cleaned[column] = (
                cleaned[column]
                .astype("string")
                .str.strip()
            )

        cleaned["product_id"] = pd.to_numeric(
            cleaned["product_id"]
        ).astype("int64")

        cleaned["unit_price"] = pd.to_numeric(
            cleaned["unit_price"]
        ).astype("float64")

        return cleaned