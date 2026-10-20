"""Load processed order records into PostgreSQL staging."""

import pandas as pd

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    DatabaseLoadError,
    DataValidationError,
)


INSERT_ORDERS_SQL = text(
    """
    INSERT INTO staging.stg_orders (
        order_id,
        customer_id,
        order_date,
        order_status,
        source_updated_at,
        batch_id,
        source_name,
        processed_at
    )
    VALUES (
        :order_id,
        :customer_id,
        :order_date,
        :order_status,
        :source_updated_at,
        :batch_id,
        :source_name,
        :processed_at
    )
    """
)


class OrderStagingLoader:
    """Load transformed order records into PostgreSQL staging."""

    REQUIRED_COLUMNS = (
        "order_id",
        "customer_id",
        "order_date",
        "order_status",
        "source_updated_at",
        "batch_id",
        "source_name",
        "processed_at",
    )

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the loader with a SQLAlchemy engine."""

        self.engine = engine

    def load(
        self,
        dataframe: pd.DataFrame,
    ) -> int:
        """Load order records and return the number of inserted rows."""

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
                f"Order staging columns are missing: {missing}"
            )

        records_to_load = dataframe[
            list(self.REQUIRED_COLUMNS)
        ].copy()

        records_to_load["order_id"] = (
            records_to_load["order_id"]
            .astype("int64")
        )

        records_to_load["customer_id"] = (
            records_to_load["customer_id"]
            .astype("int64")
        )

        records_to_load[
            "source_updated_at"
        ] = pd.to_datetime(
            records_to_load[
                "source_updated_at"
            ],
            utc=True,
        )

        records = records_to_load.to_dict(
            orient="records"
        )

        for record in records:
            source_updated_at = record[
                "source_updated_at"
            ]

            if hasattr(
                source_updated_at,
                "to_pydatetime",
            ):
                record[
                    "source_updated_at"
                ] = source_updated_at.to_pydatetime()

            processed_at = record[
                "processed_at"
            ]

            if hasattr(
                processed_at,
                "to_pydatetime",
            ):
                record[
                    "processed_at"
                ] = processed_at.to_pydatetime()

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    INSERT_ORDERS_SQL,
                    records,
                )

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load order records into staging.stg_orders"
            ) from exc

        return len(records)