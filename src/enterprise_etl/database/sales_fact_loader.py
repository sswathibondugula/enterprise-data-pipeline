"""Load current staged sales data into the warehouse sales fact."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import DatabaseLoadError


UPSERT_SALES_FACT_SQL = text(
    """
    WITH latest_orders AS (
        SELECT
            order_id,
            customer_id,
            order_date,
            order_status,
            batch_id,
            ROW_NUMBER() OVER (
                PARTITION BY order_id
                ORDER BY
                    processed_at DESC,
                    loaded_at DESC,
                    staging_id DESC
            ) AS row_number
        FROM staging.stg_orders
    ),

    current_orders AS (
        SELECT
            order_id,
            customer_id,
            order_date,
            order_status,
            batch_id
        FROM latest_orders
        WHERE row_number = 1
    ),

    latest_order_items AS (
        SELECT
            order_item_id,
            order_id,
            product_id,
            quantity,
            unit_price,
            batch_id,
            ROW_NUMBER() OVER (
                PARTITION BY order_item_id
                ORDER BY
                    processed_at DESC,
                    loaded_at DESC,
                    staging_id DESC
            ) AS row_number
        FROM staging.stg_order_items
    ),

    current_order_items AS (
        SELECT
            order_item_id,
            order_id,
            product_id,
            quantity,
            unit_price,
            batch_id
        FROM latest_order_items
        WHERE row_number = 1
    )

    INSERT INTO warehouse.fact_sales (
        order_item_id,
        order_id,
        date_key,
        customer_key,
        product_key,
        order_status,
        quantity,
        unit_price,
        sales_amount,
        order_batch_id,
        order_item_batch_id
    )

    SELECT
        item.order_item_id,
        item.order_id,
        date_dimension.date_key,
        customer.customer_key,
        product.product_key,
        orders.order_status,
        item.quantity,
        item.unit_price,
        ROUND(
            item.quantity * item.unit_price,
            2
        ) AS sales_amount,
        orders.batch_id,
        item.batch_id

    FROM current_order_items AS item

    INNER JOIN current_orders AS orders
        ON orders.order_id = item.order_id

    INNER JOIN warehouse.dim_customer AS customer
        ON customer.customer_id = orders.customer_id

    INNER JOIN warehouse.dim_product AS product
        ON product.product_id = item.product_id

    INNER JOIN warehouse.dim_date AS date_dimension
        ON date_dimension.full_date = orders.order_date

    ON CONFLICT (order_item_id)
    DO UPDATE SET
        order_id = EXCLUDED.order_id,
        date_key = EXCLUDED.date_key,
        customer_key = EXCLUDED.customer_key,
        product_key = EXCLUDED.product_key,
        order_status = EXCLUDED.order_status,
        quantity = EXCLUDED.quantity,
        unit_price = EXCLUDED.unit_price,
        sales_amount = EXCLUDED.sales_amount,
        order_batch_id = EXCLUDED.order_batch_id,
        order_item_batch_id = EXCLUDED.order_item_batch_id,
        loaded_at = CURRENT_TIMESTAMP
    """
)


class SalesFactLoader:
    """Upsert current sales records into the sales fact table."""

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the loader with a database engine."""

        self.engine = engine

    def load(self) -> int:
        """Load current staged sales into warehouse.fact_sales."""

        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    UPSERT_SALES_FACT_SQL
                )

                return result.rowcount

        except SQLAlchemyError as exc:
            raise DatabaseLoadError(
                "Unable to load sales into "
                "warehouse.fact_sales"
            ) from exc