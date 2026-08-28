"""Raw landing storage for source files."""

from pathlib import Path
from shutil import copy2

from enterprise_etl.exceptions import DataIngestionError


class RawLandingStore:
    """Preserve source files in immutable raw batch folders."""

    def __init__(self, raw_root: Path) -> None:
        """Initialize the raw landing storage location."""
        self.raw_root = raw_root

    def store(self, source_path: Path, batch_id: str) -> Path:
        """Copy a source file into raw storage and return its new path."""
        if not source_path.exists():
            raise DataIngestionError(
                f"Source file does not exist: {source_path}"
            )

        if not source_path.is_file():
            raise DataIngestionError(
                f"Source path is not a file: {source_path}"
            )

        if not self.raw_root.is_dir():
            raise DataIngestionError(
                f"Raw landing directory does not exist: {self.raw_root}"
            )

        if not batch_id.strip():
            raise DataIngestionError("Batch ID cannot be empty")

        batch_directory = self.raw_root / batch_id
        batch_directory.mkdir(exist_ok=True)

        destination_path = batch_directory / source_path.name

        if destination_path.exists():
            raise DataIngestionError(
                f"Raw file already exists: {destination_path}"
            )

        try:
            copy2(source_path, destination_path)
        except OSError as exc:
            raise DataIngestionError(
                f"Unable to copy source file to raw storage: {source_path}"
            ) from exc

        return destination_path