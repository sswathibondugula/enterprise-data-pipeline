"""Orchestrate the end-to-end order ETL pipeline."""

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)
from enterprise_etl.database.order_staging_loader import (
    OrderStagingLoader,
)
from enterprise_etl.exceptions import (
    DataValidationError,
)
from enterprise_etl.ingestion.csv_reader import (
    CsvReader,
)
from enterprise_etl.ingestion.raw_landing import (
    RawLandingStore,
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


@dataclass(frozen=True)
class OrderPipelineResult:
    """Result returned after an Order pipeline execution."""

    raw_path: Path
    valid_records: pd.DataFrame
    rejected_records: pd.DataFrame
    rejected_path: Path | None
    loaded_records: int

    # Incremental-processing metadata.
    #
    # These fields are added at the end with defaults so the
    # existing OrderPipelineResult contract remains compatible.
    incremental_records: pd.DataFrame = field(
        default_factory=pd.DataFrame
    )

    next_watermark: datetime | None = None


class OrderPipeline:
    """Coordinate ingestion, validation, cleaning, and staging."""

    def __init__(
        self,
        raw_store: RawLandingStore,
        csv_reader: CsvReader,
        schema_validator: DataFrameSchemaValidator,
        record_validator: OrderRecordValidator,
        rejected_store: RejectedRecordStore,
        cleaner: OrderDataCleaner,
        transformer: OrderTransformer,
        staging_loader: OrderStagingLoader,
        incremental_filter: OrderIncrementalFilter | None = None,
    ) -> None:
        """Initialize the Order pipeline dependencies."""

        self.raw_store = raw_store
        self.csv_reader = csv_reader
        self.schema_validator = schema_validator
        self.record_validator = record_validator
        self.rejected_store = rejected_store
        self.cleaner = cleaner
        self.transformer = transformer
        self.staging_loader = staging_loader
        self.incremental_filter = incremental_filter

    def run(
        self,
        source_path: Path,
        batch_id: str,
        watermark: datetime | None = None,
    ) -> OrderPipelineResult:
        """Execute the Order ETL pipeline."""

        # ---------------------------------------------------------
        # 1. Raw landing
        # ---------------------------------------------------------

        raw_path = self.raw_store.store(
            source_path,
            batch_id,
        )

        # ---------------------------------------------------------
        # 2. Read landed source
        # ---------------------------------------------------------

        dataframe = self.csv_reader.read(
            raw_path
        )

        # ---------------------------------------------------------
        # 3. Structural validation
        # ---------------------------------------------------------

        self.schema_validator.validate(
            dataframe
        )

        # ---------------------------------------------------------
        # 4. Record-level validation
        # ---------------------------------------------------------

        validation_result = (
            self.record_validator.validate(
                dataframe
            )
        )

        # ---------------------------------------------------------
        # 5. Quarantine rejected records
        # ---------------------------------------------------------

        rejected_path = None

        if not validation_result.rejected_records.empty:
            rejected_path = self.rejected_store.store(
                rejected_records=(
                    validation_result.rejected_records
                ),
                batch_id=batch_id,
                source_name=source_path.name,
            )

        # ---------------------------------------------------------
        # 6. Protect downstream processing
        # ---------------------------------------------------------

        if validation_result.valid_records.empty:
            raise DataValidationError(
                "No valid order records available "
                "for downstream processing"
            )

        # ---------------------------------------------------------
        # 7. Clean valid records
        # ---------------------------------------------------------

        cleaned_records = self.cleaner.clean(
            validation_result.valid_records
        )

        # ---------------------------------------------------------
        # 8. Incremental filtering
        # ---------------------------------------------------------
        #
        # Existing tests / callers that do not provide an
        # incremental_filter continue to process every valid row.
        #
        # The real Order runner will provide the incremental filter.

        if self.incremental_filter is None:
            incremental_records = (
                cleaned_records.copy()
            )

            next_watermark = None

        else:
            incremental_records = (
                self.incremental_filter.filter(
                    dataframe=cleaned_records,
                    watermark=watermark,
                )
            )

            next_watermark = (
                self.incremental_filter
                .get_next_watermark(
                    incremental_records
                )
            )

        # ---------------------------------------------------------
        # 9. Nothing new to process
        # ---------------------------------------------------------
        #
        # This is NOT an error.
        #
        # Example:
        # previous watermark = 10:25
        # latest incoming row = 10:25
        #
        # There is simply no new work.

        if incremental_records.empty:
            return OrderPipelineResult(
                raw_path=raw_path,
                valid_records=(
                    validation_result.valid_records
                ),
                rejected_records=(
                    validation_result.rejected_records
                ),
                rejected_path=rejected_path,
                loaded_records=0,
                incremental_records=(
                    incremental_records
                ),
                next_watermark=None,
            )

        # ---------------------------------------------------------
        # 10. Transformation
        # ---------------------------------------------------------

        transformed_records = (
            self.transformer.transform(
                dataframe=incremental_records,
                batch_id=batch_id,
                source_name=source_path.name,
            )
        )

        # ---------------------------------------------------------
        # 11. PostgreSQL staging load
        # ---------------------------------------------------------

        loaded_records = (
            self.staging_loader.load(
                transformed_records
            )
        )

        # ---------------------------------------------------------
        # 12. Return execution result
        # ---------------------------------------------------------

        return OrderPipelineResult(
            raw_path=raw_path,
            valid_records=(
                validation_result.valid_records
            ),
            rejected_records=(
                validation_result.rejected_records
            ),
            rejected_path=rejected_path,
            loaded_records=loaded_records,
            incremental_records=(
                incremental_records
            ),
            next_watermark=next_watermark,
        )