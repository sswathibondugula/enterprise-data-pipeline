"""Cleaning operations for validated order data."""

import pandas as pd


class OrderDataCleaner:
    """Normalize validated order records for downstream processing."""

    def clean(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return a cleaned copy of validated order records."""

        cleaned = dataframe.copy(deep=True)

        cleaned["order_id"] = pd.to_numeric(
            cleaned["order_id"]
        ).astype("int64")

        cleaned["customer_id"] = pd.to_numeric(
            cleaned["customer_id"]
        ).astype("int64")

        cleaned["order_date"] = (
            pd.to_datetime(
                cleaned["order_date"],
                format="%Y-%m-%d",
            )
            .dt.date
        )

        cleaned["order_status"] = (
            cleaned["order_status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        return cleaned