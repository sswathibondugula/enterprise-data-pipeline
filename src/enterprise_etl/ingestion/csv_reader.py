"""CSV ingestion functionality for the ETL application."""

from pathlib import Path

import pandas as pd

from enterprise_etl.exceptions import DataIngestionError


class CsvReader:
    """Read CSV files into pandas DataFrames."""

    def read(self, file_path: Path) -> pd.DataFrame:
        """Read a CSV file and return its contents as a DataFrame."""
        if not file_path.exists():
            raise DataIngestionError(f"CSV file does not exist: {file_path}")

        if not file_path.is_file():
            raise DataIngestionError(f"CSV path is not a file: {file_path}")

        try:
            return pd.read_csv(file_path)
        except (OSError, UnicodeError, pd.errors.ParserError) as exc:
            raise DataIngestionError(
                f"Unable to read CSV file: {file_path}"
            ) from exc