"""Transformation logic for cleaned order data."""

from datetime import datetime, timezone

import pandas as pd

from enterprise_etl.exceptions import (
    DataValidationError,
)


class OrderTransformer:
    """Add ETL metadata to cleaned order records."""

    def transform(
        self,
        dataframe: pd.DataFrame,
        batch_id: str,
        source_name: str,
    ) -> pd.DataFrame:
        """Transform cleaned orders and add ETL metadata."""

        # ---------------------------------------------------------
        # Validate input DataFrame
        # ---------------------------------------------------------

        if dataframe.empty:
            raise DataValidationError(
                "Cannot transform an empty order dataset"
            )

        # ---------------------------------------------------------
        # Validate batch_id
        # ---------------------------------------------------------

        if (
            not isinstance(batch_id, str)
            or not batch_id.strip()
        ):
            raise DataValidationError(
                "Batch ID cannot be empty"
            )

        # ---------------------------------------------------------
        # Validate source_name
        # ---------------------------------------------------------

        if (
            not isinstance(source_name, str)
            or not source_name.strip()
        ):
            raise DataValidationError(
                "Source name cannot be empty"
            )

        # ---------------------------------------------------------
        # Copy source data
        # ---------------------------------------------------------
        #
        # This is important because we do not want the transformer
        # to modify the DataFrame that was passed into it.
        #
        # source_updated_at is automatically preserved because
        # dataframe.copy() copies all existing columns.

        transformed = dataframe.copy()

        # ---------------------------------------------------------
        # Processing timestamp
        # ---------------------------------------------------------

        processed_at = datetime.now(
            timezone.utc
        )

        # ---------------------------------------------------------
        # Add ETL metadata
        # ---------------------------------------------------------

        transformed["batch_id"] = (
            batch_id.strip()
        )

        transformed["source_name"] = (
            source_name.strip()
        )

        transformed["processed_at"] = (
            processed_at
        )

        return transformed