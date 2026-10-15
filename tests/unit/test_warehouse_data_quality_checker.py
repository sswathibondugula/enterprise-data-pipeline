"""Unit tests for warehouse data-quality checks."""

from decimal import Decimal
from unittest.mock import MagicMock

from enterprise_etl.validation.warehouse_data_quality_checker import (
    DataQualityCheckDefinition,
    WAREHOUSE_CHECKS,
    WarehouseDataQualityChecker,
)


def create_check() -> DataQualityCheckDefinition:
    """Create a reusable quality-check definition for testing."""

    return DataQualityCheckDefinition(
        check_name="Test quality check",
        dataset_name="warehouse.test_table",
        check_type="REFERENTIAL_INTEGRITY",
        query=MagicMock(),
    )


def test_build_result_returns_pass_when_no_records_fail() -> None:
    """A check passes when no records fail."""

    result = (
        WarehouseDataQualityChecker._build_result(
            check=create_check(),
            checked_records=100,
            failed_records=0,
        )
    )

    assert result.status == "PASS"

    assert result.checked_records == 100

    assert result.failed_records == 0

    assert (
        result.failure_percentage
        == Decimal("0.0000")
    )


def test_build_result_returns_fail_with_percentage() -> None:
    """A failing check calculates its failure percentage."""

    result = (
        WarehouseDataQualityChecker._build_result(
            check=create_check(),
            checked_records=20,
            failed_records=5,
        )
    )

    assert result.status == "FAIL"

    assert result.checked_records == 20

    assert result.failed_records == 5

    assert (
        result.failure_percentage
        == Decimal("25.0000")
    )


def test_build_result_handles_zero_checked_records() -> None:
    """An empty dataset does not cause division by zero."""

    result = (
        WarehouseDataQualityChecker._build_result(
            check=create_check(),
            checked_records=0,
            failed_records=0,
        )
    )

    assert result.status == "PASS"

    assert result.checked_records == 0

    assert result.failed_records == 0

    assert (
        result.failure_percentage
        == Decimal("0.0000")
    )


def test_warehouse_quality_suite_contains_expected_checks() -> None:
    """Warehouse quality suite includes all configured checks."""

    check_names = {
        check.check_name
        for check in WAREHOUSE_CHECKS
    }

    assert len(WAREHOUSE_CHECKS) == 8

    assert (
        "Duplicate orders within source batch"
        in check_names
    )

    assert (
        "Duplicate order items within source batch"
        in check_names
    )

    assert (
        "Sales fact records reconcile with staging"
        in check_names
    )

    assert (
        "Sales fact total reconciles with staging"
        in check_names
    )