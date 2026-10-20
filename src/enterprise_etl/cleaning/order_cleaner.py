"""Cleaning logic for validated order data."""

import pandas as pd


class OrderDataCleaner:
    """Clean validated order records into consistent data types."""

    def clean(
        self,
        dataframe: pd.DataFrame,
    ) -> pd.DataFrame:
        """Return a cleaned copy of validated order data."""

        cleaned = dataframe.copy()

        # ---------------------------------------------------------
        # Business identifiers
        # ---------------------------------------------------------

        cleaned["order_id"] = pd.to_numeric(
            cleaned["order_id"]
        ).astype("int64")

        cleaned["customer_id"] = pd.to_numeric(
            cleaned["customer_id"]
        ).astype("int64")

        # ---------------------------------------------------------
        # Order date
        # ---------------------------------------------------------

        cleaned["order_date"] = (
            pd.to_datetime(
                cleaned["order_date"],
                format="%Y-%m-%d",
            )
            .dt.date
        )

        # ---------------------------------------------------------
        # Order status
        # ---------------------------------------------------------

        cleaned["order_status"] = (
            cleaned["order_status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        # ---------------------------------------------------------
        # Source change timestamp
        # ---------------------------------------------------------
        #
        # Real pipeline input now includes source_updated_at.
        # utc=True converts values such as:
        #
        # 2026-10-18T10:15:00Z
        #
        # into timezone-aware UTC timestamps.
        #
        # The conditional temporarily keeps older isolated unit
        # tests compatible if they do not yet include this column.

        if "source_updated_at" in cleaned.columns:
            cleaned["source_updated_at"] = pd.to_datetime(
                cleaned["source_updated_at"],
                utc=True,
            )

        return cleaned