"""Integration tests for the customer ETL pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

from enterprise_etl.business_rules.customer_rules import (
    CustomerBusinessRules,
)
from enterprise_etl.cleaning.customer_cleaner import CustomerDataCleaner
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
from enterprise_etl.validation.rejected_store import RejectedRecordStore
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


def test_customer_pipeline_processes_source_end_to_end(
    tmp_path: Path,
) -> None:
    """Customer pipeline coordinates all ETL stages successfully."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "customers.csv"

    source_path.write_text(
        "customer_id,name,country\n"
        "101, Alice , Canada \n"
        ",Ravi,India\n"
        "103, Maria ,Australia\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 1

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
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="batch_001",
    )

    assert result.raw_path == (
        raw_root / "batch_001" / "customers.csv"
    )

    assert result.raw_path.exists()

    assert len(result.rejected_records) == 1

    assert result.rejected_path is not None
    assert result.rejected_path.exists()

    assert len(result.eligible_records) == 1

    assert result.eligible_records.loc[0, "name"] == "Alice"

    assert result.eligible_records.loc[0, "country"] == "Canada"

    assert result.eligible_records.loc[0, "batch_id"] == "batch_001"

    assert len(result.excluded_records) == 1

    assert result.excluded_records.loc[0, "name"] == "Maria"

    assert (
        result.excluded_records.loc[0, "exclusion_reason"]
        == "Country is not in an allowed market"
    )

    assert result.loaded_records == 1

    staging_loader.load.assert_called_once()

    loaded_dataframe = staging_loader.load.call_args.args[0]

    assert len(loaded_dataframe) == 1
    assert loaded_dataframe.loc[0, "customer_id"] == 101
    assert loaded_dataframe.loc[0, "name"] == "Alice"
    assert loaded_dataframe.loc[0, "country"] == "Canada"


def test_customer_pipeline_skips_quarantine_when_all_records_are_valid(
    tmp_path: Path,
) -> None:
    """No quarantine file is created when validation has no failures."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "customers.csv"

    source_path.write_text(
        "customer_id,name,country\n"
        "101,Alice,Canada\n"
        "102,Ravi,India\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 2

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
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="batch_001",
    )

    assert len(result.eligible_records) == 2

    assert result.rejected_records.empty

    assert result.rejected_path is None

    assert result.loaded_records == 2

    staging_loader.load.assert_called_once()

    loaded_dataframe = staging_loader.load.call_args.args[0]

    assert len(loaded_dataframe) == 2