"""Integration tests for the product ETL pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

from enterprise_etl.cleaning.product_cleaner import (
    ProductDataCleaner,
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


def test_product_pipeline_processes_source_end_to_end(
    tmp_path: Path,
) -> None:
    """Product pipeline coordinates all ETL stages successfully."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "products.csv"

    source_path.write_text(
        "product_id,product_name,category,unit_price\n"
        "501, Laptop Pro , Laptops ,1299.99\n"
        "502, Wireless Mouse , Accessories ,-10\n"
        "503, Mechanical Keyboard , Accessories ,89.99\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 2

    dimension_loader = MagicMock()
    dimension_loader.load.return_value = 2

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
        staging_loader=staging_loader,
        dimension_loader=dimension_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="batch_001",
    )

    assert result.raw_path == (
        raw_root
        / "batch_001"
        / "products.csv"
    )

    assert result.raw_path.exists()

    # Wireless Mouse should be rejected
    # because its price is negative.
    assert len(result.rejected_records) == 1

    assert result.rejected_path is not None
    assert result.rejected_path.exists()

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "unit_price cannot be negative"
    )

    # Laptop and Keyboard should remain valid.
    assert len(result.valid_records) == 2

    assert (
        result.valid_records.loc[
            0,
            "product_name",
        ]
        == "Laptop Pro"
    )

    assert (
        result.valid_records.loc[
            1,
            "product_name",
        ]
        == "Mechanical Keyboard"
    )

    # Two valid products should go to staging.
    assert result.loaded_records == 2

    staging_loader.load.assert_called_once()

    loaded_dataframe = (
        staging_loader.load.call_args.args[0]
    )

    assert len(loaded_dataframe) == 2

    assert (
        loaded_dataframe.loc[
            0,
            "product_id",
        ]
        == 501
    )

    assert (
        loaded_dataframe.loc[
            1,
            "product_id",
        ]
        == 503
    )

    # The same batch should then move
    # from staging into the warehouse.
    assert result.warehouse_records == 2

    dimension_loader.load.assert_called_once_with(
        "batch_001"
    )


def test_product_pipeline_processes_all_valid_products(
    tmp_path: Path,
) -> None:
    """All valid products continue to staging and warehouse."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "products.csv"

    source_path.write_text(
        "product_id,product_name,category,unit_price\n"
        "501,Laptop Pro,Laptops,1299.99\n"
        "502,Wireless Mouse,Accessories,29.99\n"
        "503,Mechanical Keyboard,Accessories,89.99\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 3

    dimension_loader = MagicMock()
    dimension_loader.load.return_value = 3

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
        staging_loader=staging_loader,
        dimension_loader=dimension_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="batch_001",
    )

    assert len(result.valid_records) == 3

    assert result.rejected_records.empty

    assert result.rejected_path is None

    assert result.loaded_records == 3

    staging_loader.load.assert_called_once()

    assert result.warehouse_records == 3

    dimension_loader.load.assert_called_once_with(
        "batch_001"
    )