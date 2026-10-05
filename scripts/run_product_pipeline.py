"""Run the product ETL pipeline against local PostgreSQL."""

from datetime import datetime, timezone
from pathlib import Path

from enterprise_etl.cleaning.product_cleaner import (
    ProductDataCleaner,
)
from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.database.pipeline_run_repository import (
    PipelineRunRepository,
)
from enterprise_etl.database.product_dimension_loader import (
    ProductDimensionLoader,
)
from enterprise_etl.database.product_staging_loader import (
    ProductStagingLoader,
)
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
from enterprise_etl.orchestration.product_pipeline import (
    ProductPipeline,
)
from enterprise_etl.transformation.product_transformer import (
    ProductTransformer,
)
from enterprise_etl.validation.product_record_validator import (
    ProductRecordValidator,
)
from enterprise_etl.validation.rejected_store import (
    RejectedRecordStore,
)
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    """Build, audit, and execute the product ETL pipeline."""

    source_path = (
        PROJECT_ROOT
        / "data"
        / "incoming"
        / "products.csv"
    )

    raw_root = (
        PROJECT_ROOT
        / "data"
        / "raw"
    )

    rejected_root = (
        PROJECT_ROOT
        / "data"
        / "rejected"
    )

    batch_id = datetime.now(
        timezone.utc
    ).strftime(
        "product_batch_%Y%m%d_%H%M%S"
    )

    database_config = (
        DatabaseConfig.from_environment()
    )

    engine = create_database_engine(
        database_config
    )

    test_database_connection(
        engine
    )

    run_repository = PipelineRunRepository(
        engine
    )

    run_id = run_repository.start_run(
        batch_id=batch_id,
        pipeline_name="product_pipeline",
        source_name=source_path.name,
    )

    pipeline = ProductPipeline(
        raw_store=RawLandingStore(
            raw_root
        ),
        csv_reader=CsvReader(),
        schema_validator=DataFrameSchemaValidator(
            required_columns=(
                "product_id",
                "product_name",
                "category",
                "unit_price",
            )
        ),
        record_validator=ProductRecordValidator(),
        rejected_store=RejectedRecordStore(
            rejected_root
        ),
        cleaner=ProductDataCleaner(),
        transformer=ProductTransformer(),
        staging_loader=ProductStagingLoader(
            engine
        ),
        dimension_loader=ProductDimensionLoader(
            engine
        ),
    )

    try:
        result = pipeline.run(
            source_path=source_path,
            batch_id=batch_id,
        )

        total_records = (
            len(result.valid_records)
            + len(result.rejected_records)
        )

        run_repository.mark_success(
            run_id=run_id,
            total_records=total_records,
            valid_records=len(
                result.valid_records
            ),
            rejected_records=len(
                result.rejected_records
            ),
            excluded_records=0,
        )

        print()
        print(
            "Product pipeline completed successfully."
        )

        print(
            f"Run ID: {run_id}"
        )

        print(
            f"Batch ID: {batch_id}"
        )

        print(
            f"Raw file: {result.raw_path}"
        )

        print(
            f"Valid records: "
            f"{len(result.valid_records)}"
        )

        print(
            f"Rejected records: "
            f"{len(result.rejected_records)}"
        )

        print(
            f"Loaded records: "
            f"{result.loaded_records}"
        )

        print(
            f"Warehouse records affected: "
            f"{result.warehouse_records}"
        )

        if result.rejected_path is not None:
            print(
                f"Rejected file: "
                f"{result.rejected_path}"
            )

    except Exception as exc:
        run_repository.mark_failed(
            run_id=run_id,
            error_message=str(exc),
        )

        raise

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()