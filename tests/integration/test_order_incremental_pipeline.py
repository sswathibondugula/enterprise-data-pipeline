"""Integration tests for incremental Order pipeline behavior."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from enterprise_etl.cleaning.order_cleaner import (
    OrderDataCleaner,
)
from enterprise_etl.ingestion.csv_reader import (
    CsvReader,
)
from enterprise_etl.ingestion.raw_landing import (
    RawLandingStore,
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


class RecordingOrderStagingLoader:
    """Record staged rows instead of writing to PostgreSQL."""

    def __init__(
        self,
    ) -> None:
        """Initialize recorded load batches."""

        self.loaded_batches: list[
            pd.DataFrame
        ] = []

    def load(
        self,
        dataframe: pd.DataFrame,
    ) -> int:
        """Record staged rows and return their count."""

        self.loaded_batches.append(
            dataframe.copy()
        )

        return len(
            dataframe
        )


def write_orders_file(
    file_path: Path,
    order_1003_status: str = "PENDING",
    order_1003_updated_at: str = (
        "2026-10-18T10:25:00Z"
    ),
) -> None:
    """Write a realistic Orders source CSV."""

    file_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    file_path.write_text(
        (
            "order_id,customer_id,order_date,"
            "order_status,source_updated_at\n"
            "1001,101,2026-10-01,COMPLETED,"
            "2026-10-18T10:15:00Z\n"
            "1002,101,2026-10-02,COMPLETED,"
            "2026-10-18T10:20:00Z\n"
            f"1003,101,2026-10-03,"
            f"{order_1003_status},"
            f"{order_1003_updated_at}\n"
        ),
        encoding="utf-8",
    )


def build_pipeline(
    tmp_path: Path,
    staging_loader: RecordingOrderStagingLoader,
) -> OrderPipeline:
    """Build the Order pipeline using temporary test storage."""

    raw_root = (
        tmp_path
        / "raw"
    )

    rejected_root = (
        tmp_path
        / "rejected"
    )

    # RawLandingStore and RejectedRecordStore expect
    # their root directories to exist already.
    raw_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    rejected_root.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        staging_loader=staging_loader,
        incremental_filter=OrderIncrementalFilter(),
    )


def test_order_pipeline_incremental_end_to_end(
    tmp_path: Path,
) -> None:
    """Prove first-load, no-change, and changed-record behavior."""

    source_path = (
        tmp_path
        / "incoming"
        / "orders.csv"
    )

    staging_loader = (
        RecordingOrderStagingLoader()
    )

    pipeline = build_pipeline(
        tmp_path=tmp_path,
        staging_loader=staging_loader,
    )

    # ============================================================
    # RUN 1
    # No watermark exists yet.
    # All valid rows should be processed.
    # ============================================================

    write_orders_file(
        source_path
    )

    first_result = pipeline.run(
        source_path=source_path,
        batch_id="order_batch_001",
        watermark=None,
    )

    assert (
        first_result.loaded_records
        == 3
    )

    assert (
        first_result.incremental_records[
            "order_id"
        ].tolist()
        == [
            1001,
            1002,
            1003,
        ]
    )

    assert (
        first_result.next_watermark
        == datetime(
            2026,
            10,
            18,
            10,
            25,
            tzinfo=timezone.utc,
        )
    )

    assert len(
        staging_loader.loaded_batches
    ) == 1

    first_loaded_batch = (
        staging_loader.loaded_batches[0]
    )

    assert (
        first_loaded_batch[
            "order_id"
        ].tolist()
        == [
            1001,
            1002,
            1003,
        ]
    )

    # ============================================================
    # RUN 2
    # Same source data.
    # Nothing should be newer than the watermark.
    # ============================================================

    second_result = pipeline.run(
        source_path=source_path,
        batch_id="order_batch_002",
        watermark=(
            first_result.next_watermark
        ),
    )

    assert (
        second_result.loaded_records
        == 0
    )

    assert (
        second_result.incremental_records.empty
    )

    assert (
        second_result.next_watermark
        is None
    )

    # No additional staging load should occur.
    assert len(
        staging_loader.loaded_batches
    ) == 1

    # ============================================================
    # RUN 3
    # Update Order 1003.
    # Only that record should pass the watermark.
    # ============================================================

    write_orders_file(
        file_path=source_path,
        order_1003_status="COMPLETED",
        order_1003_updated_at=(
            "2026-10-21T12:00:00Z"
        ),
    )

    third_result = pipeline.run(
        source_path=source_path,
        batch_id="order_batch_003",
        watermark=(
            first_result.next_watermark
        ),
    )

    assert (
        third_result.loaded_records
        == 1
    )

    assert (
        third_result.incremental_records[
            "order_id"
        ].tolist()
        == [
            1003,
        ]
    )

    assert (
        third_result.incremental_records.iloc[
            0
        ]["order_status"]
        == "COMPLETED"
    )

    assert (
        third_result.next_watermark
        == datetime(
            2026,
            10,
            21,
            12,
            0,
            tzinfo=timezone.utc,
        )
    )

    # Run 1 loaded once.
    # Run 2 loaded nothing.
    # Run 3 loaded once.
    assert len(
        staging_loader.loaded_batches
    ) == 2

    third_loaded_batch = (
        staging_loader.loaded_batches[1]
    )

    assert len(
        third_loaded_batch
    ) == 1

    assert (
        third_loaded_batch.iloc[
            0
        ]["order_id"]
        == 1003
    )

    assert (
        third_loaded_batch.iloc[
            0
        ]["order_status"]
        == "COMPLETED"
    )