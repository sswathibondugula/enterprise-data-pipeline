"""Incremental filtering for cleaned order records."""

from datetime import datetime

import pandas as pd

from enterprise_etl.exceptions import (
    WatermarkTrackingError,
)


class OrderIncrementalFilter:
    """Select order rows newer than the previous watermark."""

    def filter(
        self,
        dataframe: pd.DataFrame,
        watermark: datetime | None,
    ) -> pd.DataFrame:
        """Return only records newer than the supplied watermark."""

        if dataframe.empty:
            return dataframe.copy()

        if "source_updated_at" not in dataframe.columns:
            raise WatermarkTrackingError(
                "source_updated_at is required for incremental filtering."
            )

        filtered = dataframe.copy()

        filtered[
            "source_updated_at"
        ] = pd.to_datetime(
            filtered["source_updated_at"],
            utc=True,
        )

        # First incremental run:
        # no previous watermark exists, so process every valid row.
        if watermark is None:
            return filtered.reset_index(
                drop=True
            )

        if not isinstance(
            watermark,
            datetime,
        ):
            raise WatermarkTrackingError(
                "watermark must be a datetime or None."
            )

        watermark_timestamp = pd.Timestamp(
            watermark
        )

        if (
            watermark_timestamp.tzinfo
            is None
        ):
            watermark_timestamp = (
                watermark_timestamp.tz_localize(
                    "UTC"
                )
            )
        else:
            watermark_timestamp = (
                watermark_timestamp.tz_convert(
                    "UTC"
                )
            )

        incremental_records = filtered.loc[
            filtered["source_updated_at"]
            > watermark_timestamp
        ].copy()

        return incremental_records.reset_index(
            drop=True
        )

    def get_next_watermark(
        self,
        dataframe: pd.DataFrame,
    ) -> datetime | None:
        """Return the maximum source timestamp from processed rows."""

        if dataframe.empty:
            return None

        if "source_updated_at" not in dataframe.columns:
            raise WatermarkTrackingError(
                "source_updated_at is required to calculate a watermark."
            )

        timestamps = pd.to_datetime(
            dataframe["source_updated_at"],
            utc=True,
        )

        maximum_timestamp = timestamps.max()

        if pd.isna(
            maximum_timestamp
        ):
            return None

        return maximum_timestamp.to_pydatetime()