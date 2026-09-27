"""Load customer data from staging into the warehouse dimension."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import DatabaseLoadError


UPSERT_CUSTOMER_DIMENSION_SQL = text(
    """
    INSERT INTO warehouse.dim_customer (
        customer_id,
        customer_name,
        country,
        source_name,
        batch_id
    )
    SELECT
        customer_id,
        customer_name,
        country,
        source_name,
        batch_id
    FROM staging.stg_customers
    WHERE batch_id = :batch_id

    ON CONFLICT (customer_id)
    DO UPDATE SET
        customer_name = EXCLUDED.customer_name,
        country = EXCLUDED.country,
        source_name = EXCLUDED.source_name,
        batch_id = EXCLUDED.batch_id,
        last_updated_at = CURRENT_TIMESTAMP
    """
)


class CustomerDimensionLoader:
    """Load staged customer records into the customer dimension."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the loader with a SQLAlchemy engine."""
        self.engine = engine

    def load(self, batch_id: str) -> int:
        """Upsert one customer batch into the warehouse dimension."""
        if not batch_id.strip():
            raise ValueError("Batch ID cannot be empty")

        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    UPSERT_CUSTOMER_DIMENSION_SQL,
                    {"batch_id": batch_id},
                )

                return result.rowcount

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load customers into "
                "warehouse.dim_customer"
            ) from exc