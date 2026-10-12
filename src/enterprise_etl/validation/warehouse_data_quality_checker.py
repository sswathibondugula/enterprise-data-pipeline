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