"""Transformation logic for cleaned product data."""

from datetime import datetime, timezone

import pandas as pd

from enterprise_etl.exceptions import DataValidationError


class ProductTransformer:
    """Enrich cleaned product records with ETL metadata."""

    def transform(
        self,
        dataframe: pd.DataFrame,
        batch_id: str,
        source_name: str,
    ) -> pd.DataFrame:
        """Return an enriched copy of cleaned product records."""

        if dataframe.empty:
            raise DataValidationError(
                "Cannot transform an empty product dataset"
            )

        if not batch_id.strip():
            raise DataValidationError(
                "Batch ID cannot be empty"
            )

        if not source_name.strip():
            raise DataValidationError(
                "Source name cannot be empty"
            )

        transformed = dataframe.copy(deep=True)

        transformed["batch_id"] = batch_id
        transformed["source_name"] = source_name
        transformed["processed_at"] = datetime.now(
            timezone.utc
        )

        return transformed