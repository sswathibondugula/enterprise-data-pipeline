"""Track successfully processed source files."""

import hashlib
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    DataIngestionError,
    ProcessedSourceTrackingError,
)


CHECK_PROCESSED_SOURCE_SQL = text(
    """
    SELECT EXISTS (
        SELECT 1
        FROM etl_control.processed_sources
        WHERE pipeline_name = :pipeline_name
          AND source_hash = :source_hash
    )
    """
)


REGISTER_PROCESSED_SOURCE_SQL = text(
    """
    INSERT INTO etl_control.processed_sources (
        pipeline_name,
        source_name,
        source_hash,
        source_size_bytes,
        batch_id
    )
    VALUES (
        :pipeline_name,
        :source_name,
        :source_hash,
        :source_size_bytes,
        :batch_id
    )

    ON CONFLICT (
        pipeline_name,
        source_hash
    )
    DO NOTHING
    """
)


@dataclass(frozen=True)
class SourceFingerprint:
    """Store identifying information calculated from a source file."""

    source_hash: str
    source_size_bytes: int


class ProcessedSourceRepository:
    """Check and record successfully processed source files."""

    CHUNK_SIZE = 1024 * 1024

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the repository with a database engine."""

        self.engine = engine

    @classmethod
    def calculate_fingerprint(
        cls,
        file_path: Path,
    ) -> SourceFingerprint:
        """Calculate SHA-256 hash and file size for a source file."""

        if not file_path.exists():
            raise DataIngestionError(
                f"Source file does not exist: {file_path}"
            )

        if not file_path.is_file():
            raise DataIngestionError(
                f"Source path is not a file: {file_path}"
            )

        sha256 = hashlib.sha256()

        try:
            with file_path.open("rb") as source_file:
                while chunk := source_file.read(
                    cls.CHUNK_SIZE
                ):
                    sha256.update(
                        chunk
                    )

            source_size_bytes = (
                file_path.stat().st_size
            )

        except OSError as exc:
            raise DataIngestionError(
                f"Unable to calculate source fingerprint: "
                f"{file_path}"
            ) from exc

        return SourceFingerprint(
            source_hash=sha256.hexdigest(),
            source_size_bytes=source_size_bytes,
        )

    def is_processed(
        self,
        pipeline_name: str,
        source_hash: str,
    ) -> bool:
        """Return whether this source hash was processed already."""

        if not pipeline_name.strip():
            raise ValueError(
                "Pipeline name cannot be empty"
            )

        if not source_hash.strip():
            raise ValueError(
                "Source hash cannot be empty"
            )

        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    CHECK_PROCESSED_SOURCE_SQL,
                    {
                        "pipeline_name": pipeline_name,
                        "source_hash": source_hash,
                    },
                )

                return bool(
                    result.scalar_one()
                )

        except SQLAlchemyError as exc:
            raise ProcessedSourceTrackingError(
                "Unable to check processed-source history"
            ) from exc

    def register_processed(
        self,
        pipeline_name: str,
        source_name: str,
        fingerprint: SourceFingerprint,
        batch_id: str,
    ) -> None:
        """Register a source after successful pipeline completion."""

        if not pipeline_name.strip():
            raise ValueError(
                "Pipeline name cannot be empty"
            )

        if not source_name.strip():
            raise ValueError(
                "Source name cannot be empty"
            )

        if not batch_id.strip():
            raise ValueError(
                "Batch ID cannot be empty"
            )

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    REGISTER_PROCESSED_SOURCE_SQL,
                    {
                        "pipeline_name": pipeline_name,
                        "source_name": source_name,
                        "source_hash": (
                            fingerprint.source_hash
                        ),
                        "source_size_bytes": (
                            fingerprint.source_size_bytes
                        ),
                        "batch_id": batch_id,
                    },
                )

        except SQLAlchemyError as exc:
            raise ProcessedSourceTrackingError(
                "Unable to register processed source"
            ) from exc