"""Load processed order-item records into PostgreSQL staging."""

from decimal import Decimal

import pandas as pd

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    DatabaseLoadError,
    DataValidationError,
)


INSERT_ORDER_ITEMS_SQL = text(
    """
    INSERT INTO staging.stg_order_items (
        order_item_id,
        order_id,
        product_id,
        quantity,
        unit_price,
        batch_id,
        source_name,
        processed_at
    )
    VALUES (
        :order_item_id,
        :order_id,
        :product_id,
        :quantity,
        :unit_price,
        :batch_id,
        :source_name,
        :processed_at
    )
    """
)


class OrderItemStagingLoader:
    """Load transformed order-item records into PostgreSQL staging."""

    REQUIRED_COLUMNS = (
        "order_item_id",
        "order_id",
        "product_id",
        "quantity",
        "unit_price",
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
        """Load order-item records and return the number inserted."""

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
                f"Order-item staging columns are missing: {missing}"
            )

        records_to_load = dataframe[
            list(self.REQUIRED_COLUMNS)
        ].copy()

        integer_columns = (
            "order_item_id",
            "order_id",
            "product_id",
            "quantity",
        )

        for column in integer_columns:
            records_to_load[column] = (
                records_to_load[column]
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
                    INSERT_ORDER_ITEMS_SQL,
                    records,
                )

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load order-item records into "
                "staging.stg_order_items"
            ) from exc

        return len(records)