"""Orchestration for the product ETL pipeline."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from enterprise_etl.cleaning.product_cleaner import (
    ProductDataCleaner,
)
from enterprise_etl.database.product_dimension_loader import (
    ProductDimensionLoader,
)
from enterprise_etl.database.product_staging_loader import (
    ProductStagingLoader,
)
from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
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


@dataclass
class ProductPipelineResult:
    """Store outputs produced by a product pipeline run."""

    raw_path: Path
    valid_records: pd.DataFrame
    rejected_records: pd.DataFrame
    rejected_path: Path | None
    loaded_records: int
    warehouse_records: int


class ProductPipeline:
    """Coordinate all stages of product ETL processing."""

    def __init__(
        self,
        raw_store: RawLandingStore,
        csv_reader: CsvReader,
        schema_validator: DataFrameSchemaValidator,
        record_validator: ProductRecordValidator,
        rejected_store: RejectedRecordStore,
        cleaner: ProductDataCleaner,
        transformer: ProductTransformer,
        staging_loader: ProductStagingLoader,
        dimension_loader: ProductDimensionLoader,
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
        self.dimension_loader = dimension_loader

    def run(
        self,
        source_path: Path,
        batch_id: str,
    ) -> ProductPipelineResult:
        """Execute the complete product ETL pipeline."""

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
                "No valid product records available "
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

        warehouse_records = self.dimension_loader.load(
            batch_id
        )

        return ProductPipelineResult(
            raw_path=raw_path,
            valid_records=transformed_records,
            rejected_records=validation_result.rejected_records,
            rejected_path=rejected_path,
            loaded_records=loaded_records,
            warehouse_records=warehouse_records,
        )