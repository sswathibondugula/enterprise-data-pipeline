"""Unit tests for incremental order filtering."""

from datetime import datetime, timezone

import pandas as pd
import pytest

from enterprise_etl.exceptions import (
    WatermarkTrackingError,
)
from enterprise_etl.transformation.order_incremental_filter import (
    OrderIncrementalFilter,
)


def create_orders() -> pd.DataFrame:
    """Create cleaned orders with source update timestamps."""

    return pd.DataFrame(
        [
            {
                "order_id": 1001,
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:15:00Z"
                ),
            },
            {
                "order_id": 1002,
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:20:00Z"
                ),
            },
            {
                "order_id": 1003,
                "source_updated_at": pd.Timestamp(
                    "2026-10-18T10:25:00Z"
                ),
            },
        ]
    )


def test_filter_returns_all_rows_without_watermark() -> None:
    """First incremental run processes every valid record."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = create_orders()

    result = incremental_filter.filter(
        dataframe=dataframe,
        watermark=None,
    )

    assert len(result) == 3

    assert result["order_id"].tolist() == [
        1001,
        1002,
        1003,
    ]


def test_filter_returns_only_rows_newer_than_watermark() -> None:
    """Previously processed timestamps are excluded."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = create_orders()

    watermark = datetime(
        2026,
        10,
        18,
        10,
        20,
        tzinfo=timezone.utc,
    )

    result = incremental_filter.filter(
        dataframe=dataframe,
        watermark=watermark,
    )

    assert len(result) == 1

    assert (
        result.iloc[0]["order_id"]
        == 1003
    )


def test_filter_excludes_row_equal_to_watermark() -> None:
    """A row equal to the watermark is already processed."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = create_orders()

    watermark = datetime(
        2026,
        10,
        18,
        10,
        25,
        tzinfo=timezone.utc,
    )

    result = incremental_filter.filter(
        dataframe=dataframe,
        watermark=watermark,
    )

    assert result.empty


def test_filter_accepts_naive_watermark_as_utc() -> None:
    """Naive watermark values are normalized to UTC."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = create_orders()

    watermark = datetime(
        2026,
        10,
        18,
        10,
        20,
    )

    result = incremental_filter.filter(
        dataframe=dataframe,
        watermark=watermark,
    )

    assert len(result) == 1
    assert result.iloc[0]["order_id"] == 1003


def test_filter_rejects_missing_source_updated_at() -> None:
    """Incremental filtering requires its cursor column."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001,
            }
        ]
    )

    with pytest.raises(
        WatermarkTrackingError,
        match="source_updated_at is required",
    ):
        incremental_filter.filter(
            dataframe=dataframe,
            watermark=None,
        )


def test_get_next_watermark_returns_maximum_timestamp() -> None:
    """Next watermark comes from the latest processed source row."""

    incremental_filter = OrderIncrementalFilter()

    dataframe = create_orders()

    result = incremental_filter.get_next_watermark(
        dataframe
    )

    assert result == datetime(
        2026,
        10,
        18,
        10,
        25,
        tzinfo=timezone.utc,
    )


def test_get_next_watermark_returns_none_for_empty_data() -> None:
    """No processed records means the watermark must not advance."""

    incremental_filter = OrderIncrementalFilter()

    result = incremental_filter.get_next_watermark(
        pd.DataFrame()
    )

    assert result is None