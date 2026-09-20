"""Orchestration for the customer ETL pipeline."""

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from enterprise_etl.business_rules.customer_rules import (
    CustomerBusinessRules,
)
from enterprise_etl.cleaning.customer_cleaner import CustomerDataCleaner
from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
from enterprise_etl.transformation.customer_transformer import (
    CustomerTransformer,
)
from enterprise_etl.validation.record_validator import (
    CustomerRecordValidator,
)
from enterprise_etl.validation.rejected_store import RejectedRecordStore
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)
from enterprise_etl.database.customer_staging_loader import (
    CustomerStagingLoader,
)

@dataclass
class CustomerPipelineResult:
    """Store the outputs produced by a customer pipeline run."""

    raw_path: Path
    eligible_records: pd.DataFrame
    excluded_records: pd.DataFrame
    rejected_records: pd.DataFrame
    rejected_path: Path | None
    loaded_records: int


class CustomerPipeline:
    """Coordinate all stages of customer ETL processing."""

    def __init__(
    self,
    raw_store: RawLandingStore,
    csv_reader: CsvReader,
    schema_validator: DataFrameSchemaValidator,
    record_validator: CustomerRecordValidator,
    rejected_store: RejectedRecordStore,
    cleaner: CustomerDataCleaner,
    transformer: CustomerTransformer,
    business_rules: CustomerBusinessRules,
    staging_loader: CustomerStagingLoader,
) -> None:
        """Initialize the pipeline with its processing components."""
        self.raw_store = raw_store
        self.csv_reader = csv_reader
        self.schema_validator = schema_validator
        self.record_validator = record_validator
        self.rejected_store = rejected_store
        self.cleaner = cleaner
        self.transformer = transformer
        self.business_rules = business_rules
        self.staging_loader = staging_loader

    def run(
        self,
        source_path: Path,
        batch_id: str,
    ) -> CustomerPipelineResult:
        """Execute the customer ETL pipeline."""
        raw_path = self.raw_store.store(source_path, batch_id)

        dataframe = self.csv_reader.read(raw_path)

        self.schema_validator.validate(dataframe)

        validation_result = self.record_validator.validate(dataframe)

        rejected_path = None

        if not validation_result.rejected_records.empty:
            rejected_path = self.rejected_store.store(
                rejected_records=validation_result.rejected_records,
                batch_id=batch_id,
                source_name=source_path.name,
            )

        if validation_result.valid_records.empty:
            raise DataValidationError(
                "No valid customer records available for downstream processing"
            )

        cleaned_records = self.cleaner.clean(
            validation_result.valid_records
        )

        transformed_records = self.transformer.transform(
            dataframe=cleaned_records,
            batch_id=batch_id,
            source_name=source_path.name,
        )

        business_result = self.business_rules.apply(
            transformed_records
        )

        loaded_records = self.staging_loader.load(
    business_result.eligible_records
)

        return CustomerPipelineResult(
    raw_path=raw_path,
    eligible_records=business_result.eligible_records,
    excluded_records=business_result.excluded_records,
    rejected_records=validation_result.rejected_records,
    rejected_path=rejected_path,
    loaded_records=loaded_records,
)