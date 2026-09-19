"""Load processed customer records into PostgreSQL staging."""

import pandas as pd

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    DatabaseLoadError,
    DataValidationError,
)


INSERT_CUSTOMERS_SQL = text(
    """
    INSERT INTO staging.stg_customers (
        customer_id,
        customer_name,
        country,
        batch_id,
        source_name,
        processed_at
    )
    VALUES (
        :customer_id,
        :customer_name,
        :country,
        :batch_id,
        :source_name,
        :processed_at
    )
    """
)


class CustomerStagingLoader:
    """Load eligible customer records into the staging table."""

    REQUIRED_COLUMNS = (
        "customer_id",
        "name",
        "country",
        "batch_id",
        "source_name",
        "processed_at",
    )

    def __init__(self, engine: Engine) -> None:
        """Initialize the loader with a SQLAlchemy engine."""
        self.engine = engine

    def load(self, dataframe: pd.DataFrame) -> int:
        """Load customer records and return the number of rows inserted."""
        if dataframe.empty:
            return 0

        missing_columns = [
            column
            for column in self.REQUIRED_COLUMNS
            if column not in dataframe.columns
        ]

        if missing_columns:
            missing = ", ".join(sorted(missing_columns))
            raise DataValidationError(
                f"Customer staging columns are missing: {missing}"
            )

        records_to_load = dataframe[
            list(self.REQUIRED_COLUMNS)
        ].copy()

        records_to_load = records_to_load.rename(
            columns={"name": "customer_name"}
        )

        records_to_load["customer_id"] = (
            records_to_load["customer_id"].astype("int64")
        )

        records = records_to_load.to_dict(orient="records")

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    INSERT_CUSTOMERS_SQL,
                    records,
                )
        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load customer records into "
                "staging.stg_customers"
            ) from exc

        return len(records)