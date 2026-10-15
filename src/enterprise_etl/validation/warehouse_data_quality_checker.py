"""Warehouse-level data-quality checks."""

from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import DataQualityCheckError


@dataclass(frozen=True)
class DataQualityCheckDefinition:
    """Define one database data-quality check."""

    check_name: str
    dataset_name: str
    check_type: str
    query: object


@dataclass(frozen=True)
class DataQualityCheckResult:
    """Store the result of one data-quality check."""

    check_name: str
    dataset_name: str
    check_type: str
    status: str
    checked_records: int
    failed_records: int
    failure_percentage: Decimal
    details: str


ORDERS_MISSING_CUSTOMERS_SQL = text(
    """
    WITH latest_orders AS (
        SELECT
            order_id,
            customer_id,
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
            customer_id
        FROM latest_orders
        WHERE row_number = 1
    )

    SELECT
        COUNT(*) AS checked_records,

        COUNT(*) FILTER (
            WHERE customer.customer_key IS NULL
        ) AS failed_records

    FROM current_orders AS orders

    LEFT JOIN warehouse.dim_customer AS customer
        ON customer.customer_id = orders.customer_id
    """
)


ORDER_ITEMS_MISSING_PRODUCTS_SQL = text(
    """
    WITH latest_items AS (
        SELECT
            order_item_id,
            product_id,
            ROW_NUMBER() OVER (
                PARTITION BY order_item_id
                ORDER BY
                    processed_at DESC,
                    loaded_at DESC,
                    staging_id DESC
            ) AS row_number
        FROM staging.stg_order_items
    ),

    current_items AS (
        SELECT
            order_item_id,
            product_id
        FROM latest_items
        WHERE row_number = 1
    )

    SELECT
        COUNT(*) AS checked_records,

        COUNT(*) FILTER (
            WHERE product.product_key IS NULL
        ) AS failed_records

    FROM current_items AS item

    LEFT JOIN warehouse.dim_product AS product
        ON product.product_id = item.product_id
    """
)


ORDER_ITEMS_MISSING_ORDERS_SQL = text(
    """
    WITH latest_orders AS (
        SELECT
            order_id,
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
            order_id
        FROM latest_orders
        WHERE row_number = 1
    ),

    latest_items AS (
        SELECT
            order_item_id,
            order_id,
            ROW_NUMBER() OVER (
                PARTITION BY order_item_id
                ORDER BY
                    processed_at DESC,
                    loaded_at DESC,
                    staging_id DESC
            ) AS row_number
        FROM staging.stg_order_items
    ),

    current_items AS (
        SELECT
            order_item_id,
            order_id
        FROM latest_items
        WHERE row_number = 1
    )

    SELECT
        COUNT(*) AS checked_records,

        COUNT(*) FILTER (
            WHERE orders.order_id IS NULL
        ) AS failed_records

    FROM current_items AS item

    LEFT JOIN current_orders AS orders
        ON orders.order_id = item.order_id
    """
)


ORDERS_MISSING_DATES_SQL = text(
    """
    WITH latest_orders AS (
        SELECT
            order_id,
            order_date,
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
            order_date
        FROM latest_orders
        WHERE row_number = 1
    )

    SELECT
        COUNT(*) AS checked_records,

        COUNT(*) FILTER (
            WHERE date_dimension.date_key IS NULL
        ) AS failed_records

    FROM current_orders AS orders

    LEFT JOIN warehouse.dim_date AS date_dimension
        ON date_dimension.full_date = orders.order_date
    """
)

DUPLICATE_ORDERS_WITHIN_BATCH_SQL = text(
    """
    WITH duplicate_groups AS (
        SELECT
            batch_id,
            order_id,
            COUNT(*) AS duplicate_count
        FROM staging.stg_orders
        GROUP BY
            batch_id,
            order_id
        HAVING COUNT(*) > 1
    )

    SELECT
        (
            SELECT COUNT(*)
            FROM staging.stg_orders
        ) AS checked_records,

        COALESCE(
            (
                SELECT SUM(
                    duplicate_count - 1
                )
                FROM duplicate_groups
            ),
            0
        ) AS failed_records
    """
)


DUPLICATE_ORDER_ITEMS_WITHIN_BATCH_SQL = text(
    """
    WITH duplicate_groups AS (
        SELECT
            batch_id,
            order_item_id,
            COUNT(*) AS duplicate_count
        FROM staging.stg_order_items
        GROUP BY
            batch_id,
            order_item_id
        HAVING COUNT(*) > 1
    )

    SELECT
        (
            SELECT COUNT(*)
            FROM staging.stg_order_items
        ) AS checked_records,

        COALESCE(
            (
                SELECT SUM(
                    duplicate_count - 1
                )
                FROM duplicate_groups
            ),
            0
        ) AS failed_records
    """
)


FACT_SALES_RECORD_RECONCILIATION_SQL = text(
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

    latest_items AS (
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

    current_items AS (
        SELECT
            order_item_id,
            order_id,
            product_id,
            quantity,
            unit_price,
            batch_id
        FROM latest_items
        WHERE row_number = 1
    ),

    expected_sales AS (
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
                item.quantity
                * item.unit_price,
                2
            ) AS sales_amount,

            orders.batch_id
                AS order_batch_id,

            item.batch_id
                AS order_item_batch_id

        FROM current_items AS item

        INNER JOIN current_orders AS orders
            ON orders.order_id
            = item.order_id

        INNER JOIN warehouse.dim_customer AS customer
            ON customer.customer_id
            = orders.customer_id

        INNER JOIN warehouse.dim_product AS product
            ON product.product_id
            = item.product_id

        INNER JOIN warehouse.dim_date AS date_dimension
            ON date_dimension.full_date
            = orders.order_date
    ),

    comparison AS (
        SELECT
            COALESCE(
                expected.order_item_id,
                actual.order_item_id
            ) AS order_item_id,

            CASE
                WHEN expected.order_item_id IS NULL
                    THEN 1

                WHEN actual.order_item_id IS NULL
                    THEN 1

                WHEN actual.order_id
                    IS DISTINCT FROM expected.order_id
                    THEN 1

                WHEN actual.date_key
                    IS DISTINCT FROM expected.date_key
                    THEN 1

                WHEN actual.customer_key
                    IS DISTINCT FROM expected.customer_key
                    THEN 1

                WHEN actual.product_key
                    IS DISTINCT FROM expected.product_key
                    THEN 1

                WHEN actual.order_status
                    IS DISTINCT FROM expected.order_status
                    THEN 1

                WHEN actual.quantity
                    IS DISTINCT FROM expected.quantity
                    THEN 1

                WHEN actual.unit_price
                    IS DISTINCT FROM expected.unit_price
                    THEN 1

                WHEN actual.sales_amount
                    IS DISTINCT FROM expected.sales_amount
                    THEN 1

                WHEN actual.order_batch_id
                    IS DISTINCT FROM expected.order_batch_id
                    THEN 1

                WHEN actual.order_item_batch_id
                    IS DISTINCT FROM expected.order_item_batch_id
                    THEN 1

                ELSE 0
            END AS failed

        FROM expected_sales AS expected

        FULL OUTER JOIN warehouse.fact_sales AS actual
            ON actual.order_item_id
            = expected.order_item_id
    )

    SELECT
        COUNT(*) AS checked_records,

        COALESCE(
            SUM(failed),
            0
        ) AS failed_records

    FROM comparison
    """
)


FACT_SALES_TOTAL_RECONCILIATION_SQL = text(
    """
    WITH latest_orders AS (
        SELECT
            order_id,

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
            order_id
        FROM latest_orders
        WHERE row_number = 1
    ),

    latest_items AS (
        SELECT
            order_item_id,
            order_id,
            quantity,
            unit_price,

            ROW_NUMBER() OVER (
                PARTITION BY order_item_id
                ORDER BY
                    processed_at DESC,
                    loaded_at DESC,
                    staging_id DESC
            ) AS row_number

        FROM staging.stg_order_items
    ),

    current_items AS (
        SELECT
            order_item_id,
            order_id,
            quantity,
            unit_price
        FROM latest_items
        WHERE row_number = 1
    ),

    expected_total AS (
        SELECT
            COALESCE(
                ROUND(
                    SUM(
                        item.quantity
                        * item.unit_price
                    ),
                    2
                ),
                0
            ) AS total_sales

        FROM current_items AS item

        INNER JOIN current_orders AS orders
            ON orders.order_id
            = item.order_id
    ),

    actual_total AS (
        SELECT
            COALESCE(
                ROUND(
                    SUM(sales_amount),
                    2
                ),
                0
            ) AS total_sales

        FROM warehouse.fact_sales
    )

    SELECT
        1 AS checked_records,

        CASE
            WHEN expected.total_sales
                IS DISTINCT FROM actual.total_sales
                THEN 1
            ELSE 0
        END AS failed_records

    FROM expected_total AS expected

    CROSS JOIN actual_total AS actual
    """
)

INSERT_QUALITY_RESULT_SQL = text(
    """
    INSERT INTO etl_control.data_quality_results (
        check_name,
        dataset_name,
        check_type,
        status,
        checked_records,
        failed_records,
        failure_percentage,
        details,
        pipeline_name,
        batch_id
    )
    VALUES (
        :check_name,
        :dataset_name,
        :check_type,
        :status,
        :checked_records,
        :failed_records,
        :failure_percentage,
        :details,
        :pipeline_name,
        :batch_id
    )
    """
)


WAREHOUSE_CHECKS = (
    DataQualityCheckDefinition(
        check_name="Orders missing customer dimension reference",
        dataset_name="staging.stg_orders",
        check_type="REFERENTIAL_INTEGRITY",
        query=ORDERS_MISSING_CUSTOMERS_SQL,
    ),
    DataQualityCheckDefinition(
        check_name="Order items missing product dimension reference",
        dataset_name="staging.stg_order_items",
        check_type="REFERENTIAL_INTEGRITY",
        query=ORDER_ITEMS_MISSING_PRODUCTS_SQL,
    ),
    DataQualityCheckDefinition(
        check_name="Order items missing order reference",
        dataset_name="staging.stg_order_items",
        check_type="REFERENTIAL_INTEGRITY",
        query=ORDER_ITEMS_MISSING_ORDERS_SQL,
    ),
    DataQualityCheckDefinition(
        check_name="Orders missing date dimension reference",
        dataset_name="staging.stg_orders",
        check_type="REFERENTIAL_INTEGRITY",
        query=ORDERS_MISSING_DATES_SQL,
    ),
    DataQualityCheckDefinition(
        check_name="Duplicate orders within source batch",
        dataset_name="staging.stg_orders",
        check_type="DUPLICATE",
        query=DUPLICATE_ORDERS_WITHIN_BATCH_SQL,
    ),

    DataQualityCheckDefinition(
        check_name="Duplicate order items within source batch",
        dataset_name="staging.stg_order_items",
        check_type="DUPLICATE",
        query=DUPLICATE_ORDER_ITEMS_WITHIN_BATCH_SQL,
    ),

    DataQualityCheckDefinition(
        check_name="Sales fact records reconcile with staging",
        dataset_name="warehouse.fact_sales",
        check_type="RECONCILIATION",
        query=FACT_SALES_RECORD_RECONCILIATION_SQL,
    ),

    DataQualityCheckDefinition(
        check_name="Sales fact total reconciles with staging",
        dataset_name="warehouse.fact_sales",
        check_type="RECONCILIATION",
        query=FACT_SALES_TOTAL_RECONCILIATION_SQL,
    ),
)


class WarehouseDataQualityChecker:
    """Execute and persist warehouse data-quality checks."""

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the checker with a database engine."""

        self.engine = engine

    def run_all(
        self,
        pipeline_name: str = "warehouse_data_quality",
        batch_id: str | None = None,
    ) -> list[DataQualityCheckResult]:
        """Execute all configured warehouse data-quality checks."""

        results = []

        try:
            with self.engine.begin() as connection:

                for check in WAREHOUSE_CHECKS:
                    query_result = connection.execute(
                        check.query
                    )

                    counts = (
                        query_result
                        .mappings()
                        .one()
                    )

                    checked_records = int(
                        counts["checked_records"]
                        or 0
                    )

                    failed_records = int(
                        counts["failed_records"]
                        or 0
                    )

                    result = self._build_result(
                        check=check,
                        checked_records=checked_records,
                        failed_records=failed_records,
                    )

                    connection.execute(
                        INSERT_QUALITY_RESULT_SQL,
                        {
                            "check_name": result.check_name,
                            "dataset_name": result.dataset_name,
                            "check_type": result.check_type,
                            "status": result.status,
                            "checked_records": result.checked_records,
                            "failed_records": result.failed_records,
                            "failure_percentage": result.failure_percentage,
                            "details": result.details,
                            "pipeline_name": pipeline_name,
                            "batch_id": batch_id,
                        },
                    )

                    results.append(
                        result
                    )

        except SQLAlchemyError as exc:
            raise DataQualityCheckError(
                "Unable to execute warehouse "
                "data-quality checks"
            ) from exc

        return results

    @staticmethod
    def _build_result(
        check: DataQualityCheckDefinition,
        checked_records: int,
        failed_records: int,
    ) -> DataQualityCheckResult:
        """Create a standardized result for one quality check."""

        if checked_records == 0:
            failure_percentage = Decimal(
                "0.0000"
            )

        else:
            failure_percentage = (
                (
                    Decimal(failed_records)
                    / Decimal(checked_records)
                )
                * Decimal("100")
            ).quantize(
                Decimal("0.0001")
            )

        status = (
            "PASS"
            if failed_records == 0
            else "FAIL"
        )

        details = (
            f"{failed_records} of "
            f"{checked_records} records failed."
        )

        return DataQualityCheckResult(
            check_name=check.check_name,
            dataset_name=check.dataset_name,
            check_type=check.check_type,
            status=status,
            checked_records=checked_records,
            failed_records=failed_records,
            failure_percentage=failure_percentage,
            details=details,
        )