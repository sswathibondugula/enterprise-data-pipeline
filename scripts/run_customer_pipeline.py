"""Run the customer ETL pipeline against local PostgreSQL."""

from datetime import datetime, timezone
from pathlib import Path

from enterprise_etl.business_rules.customer_rules import (
    CustomerBusinessRules,
)
from enterprise_etl.cleaning.customer_cleaner import CustomerDataCleaner
from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.database.customer_staging_loader import (
    CustomerStagingLoader,
)
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
from enterprise_etl.orchestration.customer_pipeline import (
    CustomerPipeline,
)
from enterprise_etl.transformation.customer_transformer import (
    CustomerTransformer,
)
from enterprise_etl.validation.record_validator import (
    CustomerRecordValidator,
)
from enterprise_etl.validation.rejected_store import (
    RejectedRecordStore,
)
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Build and execute the customer pipeline."""
    source_path = (
        PROJECT_ROOT
        / "data"
        / "incoming"
        / "customers.csv"
    )

    raw_root = PROJECT_ROOT / "data" / "raw"
    rejected_root = PROJECT_ROOT / "data" / "rejected"

    batch_id = datetime.now(timezone.utc).strftime(
        "batch_%Y%m%d_%H%M%S"
    )

    database_config = DatabaseConfig.from_environment()

    engine = create_database_engine(database_config)

    test_database_connection(engine)

    pipeline = CustomerPipeline(
        raw_store=RawLandingStore(raw_root),
        csv_reader=CsvReader(),
        schema_validator=DataFrameSchemaValidator(
            required_columns=(
                "customer_id",
                "name",
                "country",
            )
        ),
        record_validator=CustomerRecordValidator(),
        rejected_store=RejectedRecordStore(
            rejected_root
        ),
        cleaner=CustomerDataCleaner(),
        transformer=CustomerTransformer(),
        business_rules=CustomerBusinessRules(
            allowed_countries=(
                "Canada",
                "India",
            )
        ),
        staging_loader=CustomerStagingLoader(engine),
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id=batch_id,
    )

    print()
    print("Customer pipeline completed successfully.")
    print(f"Batch ID: {batch_id}")
    print(f"Raw file: {result.raw_path}")
    print(f"Eligible records: {len(result.eligible_records)}")
    print(f"Rejected records: {len(result.rejected_records)}")
    print(f"Excluded records: {len(result.excluded_records)}")
    print(f"Loaded records: {result.loaded_records}")

    if result.rejected_path is not None:
        print(f"Rejected file: {result.rejected_path}")


if __name__ == "__main__":
    main()