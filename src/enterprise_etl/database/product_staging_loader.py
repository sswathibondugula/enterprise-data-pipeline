"""Load processed product records into PostgreSQL staging."""

from decimal import Decimal

import pandas as pd

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    DatabaseLoadError,
    DataValidationError,
)


INSERT_PRODUCTS_SQL = text(
    """
    INSERT INTO staging.stg_products (
        product_id,
        product_name,
        category,
        unit_price,
        batch_id,
        source_name,
        processed_at
    )
    VALUES (
        :product_id,
        :product_name,
        :category,
        :unit_price,
        :batch_id,
        :source_name,
        :processed_at
    )
    """
)


class ProductStagingLoader:
    """Load processed product records into the staging table."""

    REQUIRED_COLUMNS = (
        "product_id",
        "product_name",
        "category",
        "unit_price",
        "batch_id",
        "source_name",
        "processed_at",
    )

    def __init__(self, engine: Engine) -> None:
        """Initialize the loader with a SQLAlchemy engine."""
        self.engine = engine

    def load(
        self,
        dataframe: pd.DataFrame,
    ) -> int:
        """Load product records and return the number inserted."""

        if dataframe.empty:
            return 0

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            missing = ", ".join(
                sorted(missing_columns)
            )

            raise DataValidationError(
                f"Product staging columns are missing: {missing}"
            )

        records_to_load = dataframe[
            list(self.REQUIRED_COLUMNS)
        ].copy()

        records_to_load["product_id"] = (
            records_to_load["product_id"]
            .astype("int64")
        )

        records_to_load["unit_price"] = (
            records_to_load["unit_price"]
            .apply(
                lambda value: Decimal(str(value))
            )
        )

        records = records_to_load.to_dict(
            orient="records"
        )

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    INSERT_PRODUCTS_SQL,
                    records,
                )

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load product records into "
                "staging.stg_products"
            ) from exc

        return len(records)