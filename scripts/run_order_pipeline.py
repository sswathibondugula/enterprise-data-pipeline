"""Run the incremental Order ETL pipeline against PostgreSQL."""

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
from enterprise_etl.database.watermark_repository import (
    WatermarkRepository,
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
from enterprise_etl.transformation.order_incremental_filter import (
    OrderIncrementalFilter,
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

WATERMARK_NAME = "source_updated_at"


def main() -> None:
    """Execute the incremental Order ETL pipeline."""

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
        # ---------------------------------------------------------
        # 1. Verify PostgreSQL connection
        # ---------------------------------------------------------

        test_database_connection(
            engine
        )

        logger.info(
            "Database connection verified."
        )

        # ---------------------------------------------------------
        # 2. Build repositories
        # ---------------------------------------------------------

        run_repository = PipelineRunRepository(
            engine
        )

        processed_source_repository = (
            ProcessedSourceRepository(
                engine
            )
        )

        watermark_repository = (
            WatermarkRepository(
                engine
            )
        )

        # ---------------------------------------------------------
        # 3. Calculate source fingerprint
        # ---------------------------------------------------------

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

        # ---------------------------------------------------------
        # 4. Read previous successful watermark
        # ---------------------------------------------------------

        previous_watermark = (
            watermark_repository
            .get_watermark(
                pipeline_name=PIPELINE_NAME,
                watermark_name=WATERMARK_NAME,
            )
        )

        if previous_watermark is None:
            logger.info(
                "No previous Order watermark found. "
                "This will be treated as the first "
                "incremental run."
            )

        else:
            logger.info(
                "Previous Order watermark: %s",
                previous_watermark,
            )

        # ---------------------------------------------------------
        # 5. Check whole-file idempotency
        # ---------------------------------------------------------
        #
        # File hashing remains useful as an optimization.
        #
        # IMPORTANT:
        # We only use the fast skip when a watermark already exists.
        #
        # This prevents a source that was processed before watermark
        # tracking was introduced from permanently blocking watermark
        # initialization.

        already_processed = (
            processed_source_repository
            .is_processed(
                pipeline_name=PIPELINE_NAME,
                source_hash=fingerprint.source_hash,
            )
        )

        if (
            already_processed
            and previous_watermark is not None
        ):
            logger.warning(
                "Order pipeline skipped because the exact "
                "source content has already been processed. "
                "Current watermark: %s | SHA-256: %s",
                previous_watermark,
                fingerprint.source_hash,
            )

            return

        if (
            already_processed
            and previous_watermark is None
        ):
            logger.warning(
                "Source hash was processed previously, but "
                "no watermark exists yet. The pipeline will "
                "continue so watermark tracking can be initialized."
            )

        # ---------------------------------------------------------
        # 6. Start audit record
        # ---------------------------------------------------------

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
        # 7. Build incremental Order pipeline
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
            incremental_filter=OrderIncrementalFilter(),
        )

        # ---------------------------------------------------------
        # 8. Execute pipeline using previous watermark
        # ---------------------------------------------------------

        try:
            result = pipeline.run(
                source_path=source_path,
                batch_id=batch_id,
                watermark=previous_watermark,
            )

            logger.info(
                "Incremental filtering complete. "
                "Incremental records: %s",
                len(
                    result.incremental_records
                ),
            )

            # -----------------------------------------------------
            # 9. Advance watermark ONLY after successful processing
            # -----------------------------------------------------
            #
            # If there were no new rows:
            #
            # next_watermark = None
            #
            # and we deliberately leave the existing watermark
            # unchanged.

            if result.next_watermark is not None:
                watermark_repository.update_watermark(
                    pipeline_name=PIPELINE_NAME,
                    watermark_name=WATERMARK_NAME,
                    watermark_value=(
                        result.next_watermark
                    ),
                )

                logger.info(
                    "Order watermark advanced. "
                    "Previous: %s | New: %s",
                    previous_watermark,
                    result.next_watermark,
                )

            else:
                logger.info(
                    "Order watermark unchanged because "
                    "no new incremental records were processed."
                )

            # -----------------------------------------------------
            # 10. Register successful file version
            # -----------------------------------------------------

            processed_source_repository.register_processed(
                pipeline_name=PIPELINE_NAME,
                source_name=source_path.name,
                fingerprint=fingerprint,
                batch_id=batch_id,
            )

            # -----------------------------------------------------
            # 11. Mark pipeline audit SUCCESS
            # -----------------------------------------------------

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

            logger.info(
                "Order pipeline completed successfully. "
                "Run ID: %s | Batch ID: %s | "
                "Source valid: %s | Rejected: %s | "
                "Incremental: %s | Loaded: %s",
                run_id,
                batch_id,
                len(result.valid_records),
                len(result.rejected_records),
                len(
                    result.incremental_records
                ),
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
            # -----------------------------------------------------
            # Watermark is NOT advanced on this failure path.
            # -----------------------------------------------------

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