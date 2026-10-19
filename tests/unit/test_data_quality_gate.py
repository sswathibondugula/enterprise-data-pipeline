"""Unit tests for the warehouse data-quality gate."""

from decimal import Decimal

from enterprise_etl.validation.data_quality_gate import (
    evaluate_data_quality_gate,
)
from enterprise_etl.validation.warehouse_data_quality_checker import (
    DataQualityCheckResult,
)


def build_result(
    check_name: str,
    status: str,
) -> DataQualityCheckResult:
    """Build a minimal data-quality result for gate tests."""

    return DataQualityCheckResult(
        check_name=check_name,
        dataset_name="test_dataset",
        check_type="TEST",
        status=status,
        checked_records=10,
        failed_records=0 if status == "PASS" else 1,
        failure_percentage=(
            Decimal("0.0000")
            if status == "PASS"
            else Decimal("10.0000")
        ),
        details="Test result.",
    )


def test_gate_passes_when_all_critical_checks_pass() -> None:
    """Gate passes when there are no critical failures."""

    results = [
        build_result(
            "Orders missing customer dimension ref",
            "PASS",
        ),
        build_result(
            "Sales fact records reconcile with staging",
            "PASS",
        ),
    ]

    gate_result = evaluate_data_quality_gate(
        results
    )

    assert gate_result.passed is True
    assert gate_result.failed_check_names == ()


def test_gate_fails_when_critical_check_fails() -> None:
    """Gate fails when a critical check returns FAIL."""

    results = [
        build_result(
            "Orders missing customer dimension ref",
            "PASS",
        ),
        build_result(
            "Sales fact total reconciles with staging",
            "FAIL",
        ),
    ]

    gate_result = evaluate_data_quality_gate(
        results
    )

    assert gate_result.passed is False

    assert gate_result.failed_check_names == (
        "Sales fact total reconciles with staging",
    )


def test_gate_reports_multiple_critical_failures() -> None:
    """Gate returns every failed critical check."""

    results = [
        build_result(
            "Order items missing product dimension ref",
            "FAIL",
        ),
        build_result(
            "Duplicate order items within source batch",
            "FAIL",
        ),
    ]

    gate_result = evaluate_data_quality_gate(
        results
    )

    assert gate_result.passed is False

    assert gate_result.failed_check_names == (
        "Order items missing product dimension ref",
        "Duplicate order items within source batch",
    )


def test_gate_ignores_noncritical_check_names() -> None:
    """Unknown noncritical checks do not fail the warehouse gate."""

    results = [
        build_result(
            "Informational warehouse check",
            "FAIL",
        )
    ]

    gate_result = evaluate_data_quality_gate(
        results
    )

    assert gate_result.passed is True
    assert gate_result.failed_check_names == ()