"""Transformation logic for cleaned order data."""

from datetime import datetime, timezone

import pandas as pd

from enterprise_etl.exceptions import DataValidationError


class OrderTransformer:
    """Enrich cleaned order records with ETL metadata."""

    def transform(
        self,
        dataframe: pd.DataFrame,
        batch_id: str,
        source_name: str,
    ) -> pd.DataFrame:
        """Return an enriched copy of cleaned order records."""

        if dataframe.empty:
            raise DataValidationError(
                "Cannot transform an empty order dataset"
            )

        if not batch_id.strip():
            raise DataValidationError(
                "Batch ID cannot be empty"
            )

        if not source_name.strip():
            raise DataValidationError(
                "Source name cannot be empty"
            )

        transformed = dataframe.copy(
            deep=True
        )

        transformed["batch_id"] = batch_id

        transformed["source_name"] = (
            source_name
        )

        transformed["processed_at"] = (
            datetime.now(
                timezone.utc
            )
        )

        return transformed