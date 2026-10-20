"""Run the order ETL pipeline against local PostgreSQL."""

from datetime import datetime, timezone
from pathlib import Path

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)
from enterprise_etl.database.connection import (
    DatabaseConfig,
    create_database_engine,
    test_database_connection,
)
from enterprise_etl.database.order_staging_loader import (
    OrderStagingLoader,
)
from enterprise_etl.database.pipeline_run_repository import (
    PipelineRunRepository,
)
from enterprise_etl.database.processed_source_repository import (
    ProcessedSourceRepository,
)
from enterprise_etl.ingestion.csv_reader import (
    CsvReader,
)
from enterprise_etl.ingestion.raw_landing import (
    RawLandingStore,
)
from enterprise_etl.observability.logging_config import (
    configure_logging,
)
from enterprise_etl.orchestration.order_pipeline import (
    OrderPipeline,
)
from enterprise_etl.transformation.order_transformer import (
    OrderTransformer,
)
from enterprise_etl.validation.order_record_validator import (
    OrderRecordValidator,
)
from enterprise_etl.validation.rejected_store import (
    RejectedRecordStore,
)
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]

PIPELINE_NAME = "order_pipeline"


def main() -> None:
    """Build, audit, and execute the order ETL pipeline."""

    logger = configure_logging(
        PROJECT_ROOT
    )

    source_path = (
        PROJECT_ROOT
        / "data"
        / "incoming"
        / "orders.csv"
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
        "order_batch_%Y%m%d_%H%M%S"
    )

    logger.info(
        "Order pipeline starting. "
        "Batch ID: %s | Source: %s",
        batch_id,
        source_path.name,
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

        # ---------------------------------------------------------
        # Source idempotency
        # ---------------------------------------------------------

        processed_source_repository = (
            ProcessedSourceRepository(
                engine
            )
        )

        fingerprint = (
            processed_source_repository
            .calculate_fingerprint(
                source_path
            )
        )

        logger.info(
            "Source fingerprint calculated. "
            "Source: %s | Size: %s bytes | SHA-256: %s",
            source_path.name,
            fingerprint.source_size_bytes,
            fingerprint.source_hash,
        )

        already_processed = (
            processed_source_repository
            .is_processed(
                pipeline_name=PIPELINE_NAME,
                source_hash=fingerprint.source_hash,
            )
        )

        if already_processed:
            logger.warning(
                "Order pipeline skipped because the exact "
                "source content was already processed. "
                "Source: %s | SHA-256: %s",
                source_path.name,
                fingerprint.source_hash,
            )

            return

        # ---------------------------------------------------------
        # Pipeline audit
        # ---------------------------------------------------------

        run_repository = PipelineRunRepository(
            engine
        )

        run_id = run_repository.start_run(
            batch_id=batch_id,
            pipeline_name=PIPELINE_NAME,
            source_name=source_path.name,
        )

        logger.info(
            "Pipeline audit record created. "
            "Run ID: %s",
            run_id,
        )

        # ---------------------------------------------------------
        # Build the Order pipeline
        # ---------------------------------------------------------

        pipeline = OrderPipeline(
            raw_store=RawLandingStore(
                raw_root
            ),
            csv_reader=CsvReader(),
            schema_validator=DataFrameSchemaValidator(
                required_columns=(
                    "order_id",
                    "customer_id",
                    "order_date",
                    "order_status",
                    "source_updated_at",
                )
            ),
            record_validator=OrderRecordValidator(
                allowed_statuses=(
                    "PENDING",
                    "COMPLETED",
                    "CANCELLED",
                )
            ),
            rejected_store=RejectedRecordStore(
                rejected_root
            ),
            cleaner=OrderDataCleaner(),
            transformer=OrderTransformer(),
            staging_loader=OrderStagingLoader(
                engine
            ),
        )

        # ---------------------------------------------------------
        # Execute pipeline
        # ---------------------------------------------------------

        try:
            result = pipeline.run(
                source_path=source_path,
                batch_id=batch_id,
            )

            total_records = (
                len(result.valid_records)
                + len(result.rejected_records)
            )

            # -----------------------------------------------------
            # Mark audit success
            # -----------------------------------------------------

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

            # -----------------------------------------------------
            # Register successful source
            # -----------------------------------------------------

            processed_source_repository.register_processed(
                pipeline_name=PIPELINE_NAME,
                source_name=source_path.name,
                fingerprint=fingerprint,
                batch_id=batch_id,
            )

            logger.info(
                "Order pipeline completed successfully. "
                "Run ID: %s | Batch ID: %s | "
                "Valid: %s | Rejected: %s | Loaded: %s",
                run_id,
                batch_id,
                len(result.valid_records),
                len(result.rejected_records),
                result.loaded_records,
            )

            logger.info(
                "Raw source archived at: %s",
                result.raw_path,
            )

            if result.rejected_path is not None:
                logger.warning(
                    "Rejected order records were written to: %s",
                    result.rejected_path,
                )

        except Exception as exc:
            run_repository.mark_failed(
                run_id=run_id,
                error_message=str(exc),
            )

            logger.exception(
                "Order pipeline failed. "
                "Run ID: %s | Batch ID: %s",
                run_id,
                batch_id,
            )

            raise

    except Exception:
        logger.exception(
            "Order pipeline terminated unexpectedly. "
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