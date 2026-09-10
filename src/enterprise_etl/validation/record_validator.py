"""Record-level validation for customer data."""

from dataclasses import dataclass

import pandas as pd


@dataclass
class ValidationResult:
    """Store valid and rejected records produced by validation."""

    valid_records: pd.DataFrame
    rejected_records: pd.DataFrame


class CustomerRecordValidator:
    """Validate required values in customer records."""

    REQUIRED_FIELDS = ("customer_id", "name", "country")

    def validate(self, dataframe: pd.DataFrame) -> ValidationResult:
        """Separate valid customer records from rejected records."""
        rejection_reasons = pd.Series(
            "",
            index=dataframe.index,
            dtype="string",
        )

        for column in self.REQUIRED_FIELDS:
            missing_mask = self._missing_mask(dataframe[column])
            message = f"{column} is required"

            has_existing_reason = missing_mask & rejection_reasons.ne("")
            rejection_reasons.loc[has_existing_reason] += "; "
            rejection_reasons.loc[missing_mask] += message

        rejected_mask = rejection_reasons.ne("")

        valid_records = dataframe.loc[~rejected_mask].copy()
        rejected_records = dataframe.loc[rejected_mask].copy()

        rejected_records["rejection_reason"] = rejection_reasons.loc[
            rejected_mask
        ]

        return ValidationResult(
            valid_records=valid_records.reset_index(drop=True),
            rejected_records=rejected_records.reset_index(drop=True),
        )

    @staticmethod
    def _missing_mask(series: pd.Series) -> pd.Series:
        """Identify null, empty, or whitespace-only values."""
        blank_mask = (
            series.astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )

        return series.isna() | blank_mask