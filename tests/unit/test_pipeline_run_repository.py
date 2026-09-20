"""Unit tests for pipeline run database auditing."""

from unittest.mock import MagicMock

from enterprise_etl.database.pipeline_run_repository import (
    PipelineRunRepository,
)


def test_pipeline_run_repository_starts_run() -> None:
    """Starting a pipeline creates a RUNNING audit record."""
    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    connection.execute.return_value.scalar_one.return_value = 42

    repository = PipelineRunRepository(engine)

    run_id = repository.start_run(
        batch_id="batch_001",
        pipeline_name="customer_pipeline",
        source_name="customers.csv",
    )

    assert run_id == 42

    parameters = connection.execute.call_args.args[1]

    assert parameters["batch_id"] == "batch_001"
    assert parameters["pipeline_name"] == "customer_pipeline"
    assert parameters["source_name"] == "customers.csv"


def test_pipeline_run_repository_marks_success() -> None:
    """Successful runs store processing counts."""
    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    repository = PipelineRunRepository(engine)

    repository.mark_success(
        run_id=42,
        total_records=100,
        valid_records=95,
        rejected_records=5,
        excluded_records=10,
    )

    parameters = connection.execute.call_args.args[1]

    assert parameters["run_id"] == 42
    assert parameters["total_records"] == 100
    assert parameters["valid_records"] == 95
    assert parameters["rejected_records"] == 5
    assert parameters["excluded_records"] == 10


def test_pipeline_run_repository_marks_failure() -> None:
    """Failed runs store the failure message."""
    engine = MagicMock()

    connection = (
        engine.begin.return_value
        .__enter__.return_value
    )

    repository = PipelineRunRepository(engine)

    repository.mark_failed(
        run_id=42,
        error_message="Required columns are missing: country",
    )

    parameters = connection.execute.call_args.args[1]

    assert parameters["run_id"] == 42

    assert (
        parameters["error_message"]
        == "Required columns are missing: country"
    )