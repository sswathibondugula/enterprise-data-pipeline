"""Run warehouse data-quality checks and enforce the quality gate."""

from datetime import datetime, timezone
from pathlib import Path

from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.observability.logging_config import (
    configure_logging,
)
from enterprise_etl.validation.data_quality_gate import (
    evaluate_data_quality_gate,
)
from enterprise_etl.validation.warehouse_data_quality_checker import (
    WarehouseDataQualityChecker,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_NAME = "warehouse_data_quality"


def main() -> None:
    """Execute warehouse checks and fail when critical checks fail."""

    logger = configure_logging(
        PROJECT_ROOT
    )

    batch_id = datetime.now(
        timezone.utc
    ).strftime(
        "dq_batch_%Y%m%d_%H%M%S"
    )

    logger.info(
        "Warehouse data-quality checks starting. "
        "Batch ID: %s",
        batch_id,
    )

    database_config = (
        DatabaseConfig.from_environment()
    )

    engine = create_database_engine(
        database_config
    )

    try:
        test_database_connection(
            engine
        )

        logger.info(
            "Database connection verified."
        )

        checker = WarehouseDataQualityChecker(
            engine
        )

        results = checker.run_all(
            pipeline_name=PIPELINE_NAME,
            batch_id=batch_id,
        )

        print()
        print(
            "Warehouse Data Quality Results"
        )
        print(
            "=" * 70
        )

        for result in results:
            print(
                f"{result.status:<5} | "
                f"{result.check_name} | "
                f"Checked: {result.checked_records} | "
                f"Failed: {result.failed_records} | "
                f"Failure %: {result.failure_percentage}"
            )

        print(
            "=" * 70
        )

        total_checks = len(
            results
        )

        passed_checks = sum(
            1
            for result in results
            if result.status == "PASS"
        )

        failed_checks = sum(
            1
            for result in results
            if result.status == "FAIL"
        )

        print(
            f"Total checks: {total_checks}"
        )

        print(
            f"Passed: {passed_checks}"
        )

        print(
            f"Failed: {failed_checks}"
        )

        gate_result = evaluate_data_quality_gate(
            results
        )

        if not gate_result.passed:
            logger.error(
                "Warehouse data-quality gate FAILED. "
                "Batch ID: %s | Failed critical checks: %s",
                batch_id,
                ", ".join(
                    gate_result.failed_check_names
                ),
            )

            print()
            print(
                "DATA QUALITY GATE: FAILED"
            )

            print(
                "The full ETL workflow must not "
                "continue with inconsistent warehouse data."
            )

            print(
                "Failed critical checks:"
            )

            for check_name in (
                gate_result.failed_check_names
            ):
                print(
                    f" - {check_name}"
                )

            raise SystemExit(1)

        logger.info(
            "Warehouse data-quality gate PASSED. "
            "Batch ID: %s | Checks passed: %s/%s",
            batch_id,
            passed_checks,
            total_checks,
        )

        print()
        print(
            "DATA QUALITY GATE: PASSED"
        )

    except SystemExit:
        raise

    except Exception:
        logger.exception(
            "Warehouse data-quality execution failed. "
            "Batch ID: %s",
            batch_id,
        )

        raise

    finally:
        engine.dispose()

        logger.info(
            "Database engine disposed. "
            "Batch ID: %s",
            batch_id,
        )


if __name__ == "__main__":
    main()