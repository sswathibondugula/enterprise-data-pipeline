"""Unit tests for CSV ingestion."""

from pathlib import Path

import pandas as pd
import pytest

from enterprise_etl.exceptions import DataIngestionError
from enterprise_etl.ingestion.csv_reader import CsvReader


def test_csv_reader_reads_valid_file(tmp_path: Path) -> None:
    """CSV reader returns a DataFrame for a valid CSV file."""
    csv_path = tmp_path / "customers.csv"
    csv_path.write_text(
        "customer_id,name,country\n"
        "101,Alice,Canada\n"
        "102,Ravi,India\n",
        encoding="utf-8",
    )

    reader = CsvReader()
    dataframe = reader.read(csv_path)

    assert isinstance(dataframe, pd.DataFrame)
    assert len(dataframe) == 2
    assert list(dataframe.columns) == ["customer_id", "name", "country"]
    assert dataframe.loc[0, "name"] == "Alice"


def test_csv_reader_fails_when_file_is_missing(tmp_path: Path) -> None:
    """CSV reader raises an ingestion error when the file is missing."""
    csv_path = tmp_path / "missing.csv"

    reader = CsvReader()

    with pytest.raises(DataIngestionError) as error:
        reader.read(csv_path)

    assert "CSV file does not exist:" in str(error.value)


def test_csv_reader_fails_when_path_is_directory(tmp_path: Path) -> None:
    """CSV reader raises an ingestion error when the path is a directory."""
    directory_path = tmp_path / "customers.csv"
    directory_path.mkdir()

    reader = CsvReader()

    with pytest.raises(DataIngestionError) as error:
        reader.read(directory_path)

    assert "CSV path is not a file:" in str(error.value)