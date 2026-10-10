"""Integration tests for the order ETL pipeline."""

from pathlib import Path
from unittest.mock import MagicMock

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)
from enterprise_etl.ingestion.csv_reader import CsvReader
from enterprise_etl.ingestion.raw_landing import RawLandingStore
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


def create_order_pipeline(
    raw_root: Path,
    rejected_root: Path,
    staging_loader: MagicMock,
) -> OrderPipeline:
    """Create the standard order pipeline used by tests."""

    return OrderPipeline(
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
        staging_loader=staging_loader,
    )


def test_order_pipeline_processes_valid_and_invalid_orders(
    tmp_path: Path,
) -> None:
    """Order pipeline separates invalid records and loads valid orders."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "orders.csv"

    source_path.write_text(
        "order_id,customer_id,order_date,order_status\n"
        "1001,101,2026-10-01,COMPLETED\n"
        "1002,101,2026-02-30,COMPLETED\n"
        "1003,101,2026-10-03,PENDING\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 2

    pipeline = create_order_pipeline(
        raw_root=raw_root,
        rejected_root=rejected_root,
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="order_batch_001",
    )

    assert result.raw_path == (
        raw_root
        / "order_batch_001"
        / "orders.csv"
    )

    assert result.raw_path.exists()

    assert len(result.valid_records) == 2

    assert len(result.rejected_records) == 1

    assert result.rejected_path is not None
    assert result.rejected_path.exists()

    assert (
        result.rejected_records.loc[
            0,
            "order_id",
        ]
        == 1002
    )

    assert (
        "order_date must be a valid"
        in result.rejected_records.loc[
            0,
            "rejection_reason",
        ]
    )

    assert result.loaded_records == 2

    staging_loader.load.assert_called_once()

    loaded_dataframe = (
        staging_loader.load.call_args.args[0]
    )

    assert len(loaded_dataframe) == 2

    assert loaded_dataframe[
        "order_id"
    ].tolist() == [
        1001,
        1003,
    ]

    assert (
        loaded_dataframe.loc[
            0,
            "order_status",
        ]
        == "COMPLETED"
    )

    assert (
        loaded_dataframe.loc[
            1,
            "order_status",
        ]
        == "PENDING"
    )


def test_order_pipeline_processes_all_valid_orders(
    tmp_path: Path,
) -> None:
    """All valid orders continue to PostgreSQL staging."""

    incoming_root = tmp_path / "incoming"
    raw_root = tmp_path / "raw"
    rejected_root = tmp_path / "rejected"

    incoming_root.mkdir()
    raw_root.mkdir()
    rejected_root.mkdir()

    source_path = incoming_root / "orders.csv"

    source_path.write_text(
        "order_id,customer_id,order_date,order_status\n"
        "1001,101,2026-10-01,COMPLETED\n"
        "1002,101,2026-10-02,COMPLETED\n"
        "1003,101,2026-10-03,PENDING\n",
        encoding="utf-8",
    )

    staging_loader = MagicMock()
    staging_loader.load.return_value = 3

    pipeline = create_order_pipeline(
        raw_root=raw_root,
        rejected_root=rejected_root,
        staging_loader=staging_loader,
    )

    result = pipeline.run(
        source_path=source_path,
        batch_id="order_batch_001",
    )

    assert len(result.valid_records) == 3

    assert result.rejected_records.empty

    assert result.rejected_path is None

    assert result.loaded_records == 3

    staging_loader.load.assert_called_once()