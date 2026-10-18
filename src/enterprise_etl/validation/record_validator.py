"""Record-level validation for customer data."""

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class ValidationResult:
    """Result of record-level validation."""

    valid_records: pd.DataFrame
    rejected_records: pd.DataFrame


class CustomerRecordValidator:
    """Validate individual customer records."""

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> ValidationResult:
        """Validate customers and separate valid and rejected rows."""

        rejection_reasons = pd.Series(
            "",
            index=dataframe.index,
            dtype="object",
        )

        # ---------------------------------------------------------
        # customer_id validation
        # ---------------------------------------------------------

        customer_id_missing = self._missing_mask(
            dataframe["customer_id"]
        )

        self._append_reason(
            rejection_reasons,
            customer_id_missing,
            "customer_id is required",
        )

        customer_id_numeric = pd.to_numeric(
            dataframe["customer_id"],
            errors="coerce",
        )

        customer_id_not_numeric = (
            ~customer_id_missing
            & customer_id_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            customer_id_not_numeric,
            "customer_id must be numeric",
        )

        # NEW:
        # Customer IDs must represent whole numbers.
        #
        # 101     -> valid
        # 101.0   -> valid
        # 101.5   -> rejected
        customer_id_not_whole = (
            ~customer_id_missing
            & ~customer_id_not_numeric
            & (customer_id_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            customer_id_not_whole,
            "customer_id must be a whole number",
        )

        customer_id_not_positive = (
            ~customer_id_missing
            & ~customer_id_not_numeric
            & (customer_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            customer_id_not_positive,
            "customer_id must be greater than zero",
        )

        # ---------------------------------------------------------
        # name validation
        # ---------------------------------------------------------

        name_missing = self._missing_mask(
            dataframe["name"]
        )

        self._append_reason(
            rejection_reasons,
            name_missing,
            "name is required",
        )

        # ---------------------------------------------------------
        # country validation
        # ---------------------------------------------------------

        country_missing = self._missing_mask(
            dataframe["country"]
        )

        self._append_reason(
            rejection_reasons,
            country_missing,
            "country is required",
        )

        # ---------------------------------------------------------
        # Separate valid and rejected records
        # ---------------------------------------------------------

        rejected_mask = (
            rejection_reasons != ""
        )

        valid_records = dataframe.loc[
            ~rejected_mask
        ].copy()

        rejected_records = dataframe.loc[
            rejected_mask
        ].copy()

        rejected_records[
            "rejection_reason"
        ] = rejection_reasons.loc[
            rejected_mask
        ]

        return ValidationResult(
            valid_records=valid_records.reset_index(
                drop=True
            ),
            rejected_records=rejected_records.reset_index(
                drop=True
            ),
        )

    @staticmethod
    def _missing_mask(
        series: pd.Series,
    ) -> pd.Series:
        """Identify null, empty, and whitespace-only values."""

        blank_values = (
            series.astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )

        return (
            series.isna()
            | blank_values
        )

    @staticmethod
    def _append_reason(
        rejection_reasons: pd.Series,
        condition: pd.Series,
        message: str,
    ) -> None:
        """Append a validation message to matching records."""

        rows_with_existing_reason = (
            condition
            & rejection_reasons.ne("")
        )

        rejection_reasons.loc[
            rows_with_existing_reason
        ] += "; "

        rejection_reasons.loc[
            condition
        ] += message