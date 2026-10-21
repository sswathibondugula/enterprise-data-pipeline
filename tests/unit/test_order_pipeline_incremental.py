"""Tests for incremental behavior in the Order pipeline."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pandas as pd

from enterprise_etl.orchestration.order_pipeline import (
    OrderPipeline,
)
from enterprise_etl.transformation.order_incremental_filter import (
    OrderIncrementalFilter,
)
from enterprise_etl.validation.record_validator import (
    ValidationResult,
)


def create_cleaned_orders() -> pd.DataFrame:
    """Create valid cleaned Order records."""

    return pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": datetime(
                    2026,
                    10,
                    1,
                ).date(),
                "order_status": "COMPLETED",
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:15:00Z"
                ),
            },
            {
                "order_id": 1002,
                "customer_id": 101,
                "order_date": datetime(
                    2026,
                    10,
                    2,
                ).date(),
                "order_status": "COMPLETED",
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:20:00Z"
                ),
            },
            {
                "order_id": 1003,
                "customer_id": 101,
                "order_date": datetime(
                    2026,
                    10,
                    3,
                ).date(),
                "order_status": "PENDING",
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:25:00Z"
                ),
            },
        ]
    )


def build_pipeline() -> tuple[
    OrderPipeline,
    MagicMock,
    MagicMock,
]:
    """Build an Order pipeline with mocked I/O dependencies."""

    raw_store = MagicMock()
    csv_reader = MagicMock()
    schema_validator = MagicMock()
    record_validator = MagicMock()
    rejected_store = MagicMock()
    cleaner = MagicMock()
    transformer = MagicMock()
    staging_loader = MagicMock()

    raw_path = Path(
        "data/raw/order_batch_test/orders.csv"
    )

    raw_store.store.return_value = (
        raw_path
    )

    source_dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
                "source_updated_at": (
                    "2026-10-18T10:15:00Z"
                ),
            }
        ]
    )

    csv_reader.read.return_value = (
        source_dataframe
    )

    cleaned_orders = (
        create_cleaned_orders()
    )

    record_validator.validate.return_value = (
        ValidationResult(
            valid_records=cleaned_orders.copy(),
            rejected_records=pd.DataFrame(),
        )
    )

    cleaner.clean.return_value = (
        cleaned_orders.copy()
    )

    transformer.transform.side_effect = (
        lambda dataframe, batch_id, source_name: (
            dataframe.assign(
                batch_id=batch_id,
                source_name=source_name,
                processed_at=datetime.now(
                    timezone.utc
                ),
            )
        )
    )

    staging_loader.load.return_value = 1

    pipeline = OrderPipeline(
        raw_store=raw_store,
        csv_reader=csv_reader,
        schema_validator=schema_validator,
        record_validator=record_validator,
        rejected_store=rejected_store,
        cleaner=cleaner,
        transformer=transformer,
        staging_loader=staging_loader,
        incremental_filter=(
            OrderIncrementalFilter()
        ),
    )

    return (
        pipeline,
        transformer,
        staging_loader,
    )


def test_pipeline_loads_only_rows_newer_than_watermark() -> None:
    """Only records newer than the saved watermark reach staging."""

    (
        pipeline,
        transformer,
        staging_loader,
    ) = build_pipeline()

    watermark = datetime(
        2026,
        10,
        18,
        10,
        20,
        tzinfo=timezone.utc,
    )

    result = pipeline.run(
        source_path=Path(
            "data/incoming/orders.csv"
        ),
        batch_id="order_batch_test",
        watermark=watermark,
    )

    assert result.loaded_records == 1

    assert (
        result.incremental_records[
            "order_id"
        ].tolist()
        == [1003]
    )

    assert result.next_watermark == datetime(
        2026,
        10,
        18,
        10,
        25,
        tzinfo=timezone.utc,
    )

    transformer.transform.assert_called_once()

    transformed_input = (
        transformer.transform.call_args.kwargs[
            "dataframe"
        ]
    )

    assert (
        transformed_input["order_id"].tolist()
        == [1003]
    )

    staging_loader.load.assert_called_once()


def test_pipeline_returns_success_when_no_new_rows_exist() -> None:
    """An up-to-date source results in zero incremental rows."""

    (
        pipeline,
        transformer,
        staging_loader,
    ) = build_pipeline()

    watermark = datetime(
        2026,
        10,
        18,
        10,
        25,
        tzinfo=timezone.utc,
    )

    result = pipeline.run(
        source_path=Path(
            "data/incoming/orders.csv"
        ),
        batch_id="order_batch_test",
        watermark=watermark,
    )

    assert result.loaded_records == 0
    assert result.incremental_records.empty
    assert result.next_watermark is None

    transformer.transform.assert_not_called()
    staging_loader.load.assert_not_called()


def test_pipeline_processes_all_rows_on_first_incremental_run() -> None:
    """No existing watermark means every valid row is processed."""

    (
        pipeline,
        transformer,
        staging_loader,
    ) = build_pipeline()

    staging_loader.load.return_value = 3

    result = pipeline.run(
        source_path=Path(
            "data/incoming/orders.csv"
        ),
        batch_id="order_batch_test",
        watermark=None,
    )

    assert result.loaded_records == 3

    assert (
        result.incremental_records[
            "order_id"
        ].tolist()
        == [
            1001,
            1002,
            1003,
        ]
    )

    assert result.next_watermark == datetime(
        2026,
        10,
        18,
        10,
        25,
        tzinfo=timezone.utc,
    )