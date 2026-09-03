"""Structural validation for pandas DataFrames."""

import pandas as pd

from enterprise_etl.exceptions import DataValidationError


class DataFrameSchemaValidator:
    """Validate the basic structure of a pandas DataFrame."""

    def __init__(
        self,
        required_columns: tuple[str, ...],
        allow_extra_columns: bool = True,
    ) -> None:
        """Initialize the validator with its expected columns."""
        self.required_columns = required_columns
        self.allow_extra_columns = allow_extra_columns

    def validate(self, dataframe: pd.DataFrame) -> None:
        """Validate dataset size and column structure."""
        if dataframe.empty:
            raise DataValidationError("Dataset is empty")

        required = set(self.required_columns)
        actual = set(dataframe.columns)

        missing_columns = sorted(required - actual)

        if missing_columns:
            missing = ", ".join(missing_columns)
            raise DataValidationError(
                f"Required columns are missing: {missing}"
            )

        if not self.allow_extra_columns:
            unexpected_columns = sorted(actual - required)

            if unexpected_columns:
                unexpected = ", ".join(unexpected_columns)
                raise DataValidationError(
                    f"Unexpected columns found: {unexpected}"
                )