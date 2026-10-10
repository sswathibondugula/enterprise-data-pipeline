"""Integration tests for the order-item ETL pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

from enterprise_etl.cleaning.order_item_cleaner import (
    OrderItemDataCleaner,
)
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
from enterprise_etl.orchestration.order_item_pipeline import (
    OrderItemPipeline,
)
from enterprise_etl.transformation.order_item_transformer import (
    OrderItemTransformer,
)
from enterprise_etl.validation.order_item_record_validator import (
    OrderItemRecordValidator,
)
from enterprise_etl.validation.rejected_store import (
    RejectedRecordStore,
)
from enterprise_etl.validation.schema_validator import (
    DataFrameSchemaValidator,
)


def create_order_item_pipeline(
    raw_root: Path,
    rejected_root: Path,
    staging_loader: MagicMock,
) -> OrderItemPipeline:
    """Create the standard order-item pipeline used by tests."""

    return OrderItemPipeline(
        raw_store=RawLandingStore(
            raw_root
        ),
        csv_reader=CsvReader(),
        schema_validator=DataFrameSchemaValidator(
            required_columns=(
                "order_item_id",
                "order_id",
                "product_id",
                "quantity",
                "unit_price",
            )
        ),
        record_validator=OrderItemRecordValidator(),
        rejected_store=RejectedRecordStore(
            rejected_root
        ),
        cleaner=OrderItemDataCleaner(),
        transformer=OrderItemTransformer(),
        staging_loader=staging_loader,
    )


def test_order_item_pipeline_processes_valid_and_invalid_records(
    tmp_path: Path,
) -> None:
    """Invalid items are quarantined while valid items continue."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = (
        incoming_root
        / "order_items.csv"
    )

    source_path.write_text(
        "order_item_id,order_id,product_id,quantity,unit_price\n"
        "1,1001,501,1,1299.99\n"
        "2,1001,502,0,29.99\n"
        "3,1002,503,1,89.99\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 2

    pipeline = create_order_item_pipeline(
        raw_root=raw_root,
        rejected_root=rejected_root,
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="order_item_batch_001",
    )

    assert result.raw_path == (
        raw_root
        / "order_item_batch_001"
        / "order_items.csv"
    )

    assert result.raw_path.exists()

    assert len(result.valid_records) == 2

    assert len(result.rejected_records) == 1

    assert result.rejected_path is not None
    assert result.rejected_path.exists()

    assert (
        result.rejected_records.loc[
            0,
            "order_item_id",
        ]
        == 2
    )

    assert (
        result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
        == "quantity must be greater than zero"
    )

    assert result.loaded_records == 2

    staging_loader.load.assert_called_once()

    loaded_dataframe = (
        staging_loader.load.call_args.args[0]
    )

    assert len(loaded_dataframe) == 2

    assert loaded_dataframe[
        "order_item_id"
    ].tolist() == [
        1,
        3,
    ]

    assert loaded_dataframe[
        "product_id"
    ].tolist() == [
        501,
        503,
    ]


def test_order_item_pipeline_processes_all_valid_records(
    tmp_path: Path,
) -> None:
    """All valid order items continue to staging."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = (
        incoming_root
        / "order_items.csv"
    )

    source_path.write_text(
        "order_item_id,order_id,product_id,quantity,unit_price\n"
        "1,1001,501,1,1299.99\n"
        "2,1001,502,2,29.99\n"
        "3,1002,503,1,89.99\n"
        "4,1003,502,1,29.99\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 4

    pipeline = create_order_item_pipeline(
        raw_root=raw_root,
        rejected_root=rejected_root,
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="order_item_batch_001",
    )

    assert len(result.valid_records) == 4

    assert result.rejected_records.empty

    assert result.rejected_path is None

    assert result.loaded_records == 4

    staging_loader.load.assert_called_once()

    loaded_dataframe = (
        staging_loader.load.call_args.args[0]
    )

    assert len(loaded_dataframe) == 4