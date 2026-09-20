"""Database operations for ETL pipeline run auditing."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import DatabaseAuditError


START_PIPELINE_RUN_SQL = text(
    """
    INSERT INTO etl_control.pipeline_runs (
        batch_id,
        pipeline_name,
        source_name,
        status
    )
    VALUES (
        :batch_id,
        :pipeline_name,
        :source_name,
        'RUNNING'
    )
    RETURNING run_id
    """
)


MARK_PIPELINE_SUCCESS_SQL = text(
    """
    UPDATE etl_control.pipeline_runs
    SET
        status = 'SUCCESS',
        finished_at = CURRENT_TIMESTAMP,
        total_records = :total_records,
        valid_records = :valid_records,
        rejected_records = :rejected_records,
        excluded_records = :excluded_records,
        error_message = NULL
    WHERE run_id = :run_id
    """
)


MARK_PIPELINE_FAILED_SQL = text(
    """
    UPDATE etl_control.pipeline_runs
    SET
        status = 'FAILED',
        finished_at = CURRENT_TIMESTAMP,
        error_message = :error_message
    WHERE run_id = :run_id
    """
)


class PipelineRunRepository:
    """Store and update ETL pipeline execution information."""

    def __init__(self, engine: Engine) -> None:
        """Initialize the repository with a database engine."""
        self.engine = engine

    def start_run(
        self,
        batch_id: str,
        pipeline_name: str,
        source_name: str,
    ) -> int:
        """Create a RUNNING pipeline record and return its run ID."""
        try:
            with self.engine.begin() as connection:
                result = connection.execute(
                    START_PIPELINE_RUN_SQL,
                    {
                        "batch_id": batch_id,
                        "pipeline_name": pipeline_name,
                        "source_name": source_name,
                    },
                )

                return result.scalar_one()

        except SQLAlchemyError as exc:
            raise DatabaseAuditError(
                "Unable to create pipeline run audit record"
            ) from exc

    def mark_success(
        self,
        run_id: int,
        total_records: int,
        valid_records: int,
        rejected_records: int,
        excluded_records: int,
    ) -> None:
        """Mark a pipeline execution as successfully completed."""
        try:
            with self.engine.begin() as connection:
                connection.execute(
                    MARK_PIPELINE_SUCCESS_SQL,
                    {
                        "run_id": run_id,
                        "total_records": total_records,
                        "valid_records": valid_records,
                        "rejected_records": rejected_records,
                        "excluded_records": excluded_records,
                    },
                )

        except SQLAlchemyError as exc:
            raise DatabaseAuditError(
                "Unable to mark pipeline run as successful"
            ) from exc

    def mark_failed(
        self,
        run_id: int,
        error_message: str,
    ) -> None:
        """Mark a pipeline execution as failed."""
        try:
            with self.engine.begin() as connection:
                connection.execute(
                    MARK_PIPELINE_FAILED_SQL,
                    {
                        "run_id": run_id,
                        "error_message": error_message,
                    },
                )

        except SQLAlchemyError as exc:
            raise DatabaseAuditError(
                "Unable to mark pipeline run as failed"
            ) from exc