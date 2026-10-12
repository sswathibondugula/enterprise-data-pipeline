"""Execute warehouse data-quality checks against PostgreSQL."""

from datetime import datetime, timezone

from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.validation.warehouse_data_quality_checker import (
    WarehouseDataQualityChecker,
)


def main() -> None:
    """Run warehouse data-quality checks and display the results."""

    batch_id = datetime.now(
        timezone.utc
    ).strftime(
        "dq_batch_%Y%m%d_%H%M%S"
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

        checker = WarehouseDataQualityChecker(
            engine
        )

        results = checker.run_all(
            pipeline_name="warehouse_data_quality",
            batch_id=batch_id,
        )

        print()
        print(
            "Warehouse data-quality checks completed."
        )

        print(
            f"Batch ID: {batch_id}"
        )

        print()

        for result in results:
            print(
                f"{result.status}: "
                f"{result.check_name}"
            )

            print(
                f"  Dataset: "
                f"{result.dataset_name}"
            )

            print(
                f"  Checked: "
                f"{result.checked_records}"
            )

            print(
                f"  Failed: "
                f"{result.failed_records}"
            )

            print(
                f"  Failure %: "
                f"{result.failure_percentage}"
            )

            print()

        failed_checks = [
            result
            for result in results
            if result.status == "FAIL"
        ]

        print(
            f"Checks executed: {len(results)}"
        )

        print(
            f"Checks passed: "
            f"{len(results) - len(failed_checks)}"
        )

        print(
            f"Checks failed: "
            f"{len(failed_checks)}"
        )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()