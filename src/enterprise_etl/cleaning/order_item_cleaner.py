"""Cleaning operations for validated order-item data."""

import pandas as pd


class OrderItemDataCleaner:
    """Normalize validated order-item records."""

    def clean(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return a cleaned copy of validated order-item records."""

        cleaned = dataframe.copy(deep=True)

        integer_columns = (
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
        )

        for column in integer_columns:
            cleaned[column] = (
                pd.to_numeric(
                    cleaned[column]
                )
                .astype("int64")
            )

        cleaned["unit_price"] = (
            pd.to_numeric(
                cleaned["unit_price"]
            )
            .astype("float64")
        )

        return cleaned