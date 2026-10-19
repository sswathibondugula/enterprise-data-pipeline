"""Store and retrieve incremental pipeline watermarks."""

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    WatermarkTrackingError,
)


GET_WATERMARK_SQL = text(
    """
    SELECT watermark_value
    FROM etl_control.pipeline_watermarks
    WHERE pipeline_name = :pipeline_name
      AND watermark_name = :watermark_name
    """
)


UPSERT_WATERMARK_SQL = text(
    """
    INSERT INTO etl_control.pipeline_watermarks (
        pipeline_name,
        watermark_name,
        watermark_value
    )
    VALUES (
        :pipeline_name,
        :watermark_name,
        :watermark_value
    )
    ON CONFLICT (
        pipeline_name,
        watermark_name
    )
    DO UPDATE
    SET
        watermark_value = EXCLUDED.watermark_value,
        updated_at = CURRENT_TIMESTAMP
    """
)


class WatermarkRepository:
    """Persist high-water marks for incremental ETL pipelines."""

    def __init__(
        self,
        engine: Engine,
    ) -> None:
        """Initialize the repository."""

        self.engine = engine

    def get_watermark(
        self,
        pipeline_name: str,
        watermark_name: str,
    ) -> datetime | None:
        """Return the current watermark or None when none exists."""

        self._validate_name(
            pipeline_name,
            "pipeline_name",
        )

        self._validate_name(
            watermark_name,
            "watermark_name",
        )

        try:
            with self.engine.connect() as connection:
                result = connection.execute(
                    GET_WATERMARK_SQL,
                    {
                        "pipeline_name": pipeline_name,
                        "watermark_name": watermark_name,
                    },
                )

                return result.scalar_one_or_none()

        except SQLAlchemyError as exc:
            raise WatermarkTrackingError(
                "Unable to retrieve pipeline watermark."
            ) from exc

    def update_watermark(
        self,
        pipeline_name: str,
        watermark_name: str,
        watermark_value: datetime,
    ) -> None:
        """Insert or update a pipeline watermark."""

        self._validate_name(
            pipeline_name,
            "pipeline_name",
        )

        self._validate_name(
            watermark_name,
            "watermark_name",
        )

        if not isinstance(
            watermark_value,
            datetime,
        ):
            raise WatermarkTrackingError(
                "watermark_value must be a datetime."
            )

        try:
            with self.engine.begin() as connection:
                connection.execute(
                    UPSERT_WATERMARK_SQL,
                    {
                        "pipeline_name": pipeline_name,
                        "watermark_name": watermark_name,
                        "watermark_value": watermark_value,
                    },
                )

        except SQLAlchemyError as exc:
            raise WatermarkTrackingError(
                "Unable to update pipeline watermark."
            ) from exc

    @staticmethod
    def _validate_name(
        value: str,
        field_name: str,
    ) -> None:
        """Validate required repository name values."""

        if (
            not isinstance(value, str)
            or not value.strip()
        ):
            raise WatermarkTrackingError(
                f"{field_name} must not be blank."
            )