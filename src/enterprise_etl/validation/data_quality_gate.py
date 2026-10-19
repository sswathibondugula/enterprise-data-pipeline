"""Decision gate for warehouse data-quality results."""

from dataclasses import dataclass
from typing import Iterable

from enterprise_etl.validation.warehouse_data_quality_checker import (
    DataQualityCheckResult,
)


CRITICAL_CHECK_NAMES = frozenset(
    {
        "Orders missing customer dimension ref",
        "Order items missing product dimension ref",
        "Order items missing order ref",
        "Orders missing date dimension ref",
        "Duplicate orders within source batch",
        "Duplicate order items within source batch",
        "Sales fact records reconcile with staging",
        "Sales fact total reconciles with staging",
    }
)


@dataclass(frozen=True)
class DataQualityGateResult:
    """Result of evaluating critical warehouse checks."""

    passed: bool
    failed_check_names: tuple[str, ...]


def evaluate_data_quality_gate(
    results: Iterable[DataQualityCheckResult],
) -> DataQualityGateResult:
    """Determine whether all critical data-quality checks passed."""

    failed_check_names = tuple(
        result.check_name
        for result in results
        if (
            result.check_name in CRITICAL_CHECK_NAMES
            and result.status == "FAIL"
        )
    )

    return DataQualityGateResult(
        passed=not failed_check_names,
        failed_check_names=failed_check_names,
    )