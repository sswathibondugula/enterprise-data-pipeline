"""Unit tests for order record validation."""

import pandas as pd

from enterprise_etl.validation.order_record_validator import (
    OrderRecordValidator,
)

def test_order_validator_rejects_decimal_identifiers() -> None:
    """Order and customer identifiers must be whole numbers."""

    validator = OrderRecordValidator(
        allowed_statuses=(
            "PENDING",
            "COMPLETED",
            "CANCELLED",
        )
    )

    dataframe = pd.DataFrame(
        [
            {
                "order_id": 1001.5,
                "customer_id": 101,
                "order_date": "2026-10-01",
                "order_status": "COMPLETED",
            },
            {
                "order_id": 1002,
                "customer_id": 101.25,
                "order_date": "2026-10-02",
                "order_status": "PENDING",
            },
        ]
    )

    result = validator.validate(
        dataframe
    )

    assert result.valid_records.empty

    assert len(
        result.rejected_records
    ) == 2

    assert (
        result.rejected_records.iloc[0][
            "rejection_reason"
        ]
        == "order_id must be a whole number"
    )

    assert (
        result.rejected_records.iloc[1][
            "rejection_reason"
        ]
        == "customer_id must be a whole number"
    )