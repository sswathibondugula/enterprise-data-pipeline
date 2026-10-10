"""Load staged transactional data into warehouse.fact_sales."""

from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.database.sales_fact_loader import (
    SalesFactLoader,
)


def main() -> None:
    """Execute the sales fact warehouse load."""

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

        loader = SalesFactLoader(
            engine
        )

        affected_rows = loader.load()

        print()
        print(
            "Sales fact load completed successfully."
        )

        print(
            f"Fact rows affected: "
            f"{affected_rows}"
        )

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()