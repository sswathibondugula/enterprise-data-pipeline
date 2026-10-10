"""Orchestration for the order ETL pipeline."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)
from enterprise_etl.database.order_staging_loader import (
    OrderStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
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


@dataclass
class OrderPipelineResult:
    """Store outputs produced by an order pipeline run."""

    raw_path: Path
    valid_records: pd.DataFrame
    rejected_records: pd.DataFrame
    rejected_path: Path | None
    loaded_records: int


class OrderPipeline:
    """Coordinate all stages of order ETL processing."""

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
    ) -> None:
        """Initialize the pipeline with its processing components."""

        self.raw_store = raw_store
        self.csv_reader = csv_reader
        self.schema_validator = schema_validator
        self.record_validator = record_validator
        self.rejected_store = rejected_store
        self.cleaner = cleaner
        self.transformer = transformer
        self.staging_loader = staging_loader

    def run(
        self,
        source_path: Path,
        batch_id: str,
    ) -> OrderPipelineResult:
        """Execute the complete order ETL pipeline."""

        raw_path = self.raw_store.store(
            source_path,
            batch_id,
        )

        dataframe = self.csv_reader.read(
            raw_path
        )

        self.schema_validator.validate(
            dataframe
        )

        validation_result = self.record_validator.validate(
            dataframe
        )

        rejected_path = None

        if not validation_result.rejected_records.empty:
            rejected_path = self.rejected_store.store(
                rejected_records=validation_result.rejected_records,
                batch_id=batch_id,
                source_name=source_path.name,
            )

        if validation_result.valid_records.empty:
            raise DataValidationError(
                "No valid order records available "
                "for downstream processing"
            )

        cleaned_records = self.cleaner.clean(
            validation_result.valid_records
        )

        transformed_records = self.transformer.transform(
            dataframe=cleaned_records,
            batch_id=batch_id,
            source_name=source_path.name,
        )

        loaded_records = self.staging_loader.load(
            transformed_records
        )

        return OrderPipelineResult(
            raw_path=raw_path,
            valid_records=transformed_records,
            rejected_records=validation_result.rejected_records,
            rejected_path=rejected_path,
            loaded_records=loaded_records,
        )