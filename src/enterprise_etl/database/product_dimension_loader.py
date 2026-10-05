"""Load staged product data into the warehouse product dimension."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import DatabaseLoadError


UPSERT_PRODUCT_DIMENSION_SQL = text(
    """
    INSERT INTO warehouse.dim_product (
        product_id,
        product_name,
        category,
        unit_price,
        source_name,
        batch_id
    )
    SELECT
        product_id,
        product_name,
        category,
        unit_price,
        source_name,
        batch_id
    FROM staging.stg_products
    WHERE batch_id = :batch_id

    ON CONFLICT (product_id)
    DO UPDATE SET
        product_name = EXCLUDED.product_name,
        category = EXCLUDED.category,
        unit_price = EXCLUDED.unit_price,
        source_name = EXCLUDED.source_name,
        batch_id = EXCLUDED.batch_id,
        last_updated_at = CURRENT_TIMESTAMP
    """
)


class ProductDimensionLoader:
    """Upsert staged products into the warehouse product dimension."""

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the loader with a SQLAlchemy engine."""
        self.engine = engine

    def load(
        self,
        batch_id: str,
    ) -> int:
        """Load one staging batch into the product dimension."""

        if not batch_id.strip():
            raise ValueError(
                "Batch ID cannot be empty"
            )

        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    UPSERT_PRODUCT_DIMENSION_SQL,
                    {
                        "batch_id": batch_id,
                    },
                )

                return result.rowcount

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load products into "
                "warehouse.dim_product"
            ) from exc