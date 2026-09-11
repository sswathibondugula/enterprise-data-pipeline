"""Storage for records rejected during data validation."""

from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from enterprise_etl.exceptions import DataValidationError


class RejectedRecordStore:
    """Persist rejected records for investigation and reprocessing."""

    def __init__(self, rejected_root: Path) -> None:
        """Initialize the rejected-record storage location."""
        self.rejected_root = rejected_root

    def store(
        self,
        rejected_records: pd.DataFrame,
        batch_id: str,
        source_name: str,
    ) -> Path:
        """Store rejected records as a CSV file and return its path."""
        if rejected_records.empty:
            raise DataValidationError("No rejected records to store")

        if not self.rejected_root.is_dir():
            raise DataValidationError(
                f"Rejected-record directory does not exist: "
                f"{self.rejected_root}"
            )

        if not batch_id.strip():
            raise DataValidationError("Batch ID cannot be empty")

        if not source_name.strip():
            raise DataValidationError("Source name cannot be empty")

        records_to_store = rejected_records.copy()

        records_to_store["batch_id"] = batch_id
        records_to_store["source_name"] = source_name
        records_to_store["rejected_at"] = datetime.now(timezone.utc)

        batch_directory = self.rejected_root / batch_id
        batch_directory.mkdir(exist_ok=True)

        source_stem = Path(source_name).stem
        destination_path = (
            batch_directory / f"{source_stem}_rejected.csv"
        )

        if destination_path.exists():
            raise DataValidationError(
                f"Rejected-record file already exists: {destination_path}"
            )

        try:
            records_to_store.to_csv(destination_path, index=False)
        except OSError as exc:
            raise DataValidationError(
                f"Unable to store rejected records: {destination_path}"
            ) from exc

        return destination_path