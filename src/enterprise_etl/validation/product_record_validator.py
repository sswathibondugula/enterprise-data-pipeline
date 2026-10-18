"""Record-level validation for product data."""

import pandas as pd

from enterprise_etl.validation.record_validator import (
    ValidationResult,
)


class ProductRecordValidator:
    """Validate individual product records."""

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> ValidationResult:
        """Validate product records and separate valid and rejected rows."""

        rejection_reasons = pd.Series(
            "",
            index=dataframe.index,
            dtype="object",
        )

        # ---------------------------------------------------------
        # product_id validation
        # ---------------------------------------------------------

        product_id_missing = self._missing_mask(
            dataframe["product_id"]
        )

        self._append_reason(
            rejection_reasons,
            product_id_missing,
            "product_id is required",
        )

        product_id_numeric = pd.to_numeric(
            dataframe["product_id"],
            errors="coerce",
        )

        product_id_not_numeric = (
            ~product_id_missing
            & product_id_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            product_id_not_numeric,
            "product_id must be numeric",
        )

        # Product IDs must represent whole numbers.
        #
        # 501     -> valid
        # 501.0   -> valid
        # 501.5   -> rejected
        product_id_not_whole = (
            ~product_id_missing
            & ~product_id_not_numeric
            & (product_id_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            product_id_not_whole,
            "product_id must be a whole number",
        )

        product_id_not_positive = (
            ~product_id_missing
            & ~product_id_not_numeric
            & (product_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            product_id_not_positive,
            "product_id must be greater than zero",
        )

        # ---------------------------------------------------------
        # product_name validation
        # ---------------------------------------------------------

        product_name_missing = self._missing_mask(
            dataframe["product_name"]
        )

        self._append_reason(
            rejection_reasons,
            product_name_missing,
            "product_name is required",
        )

        # ---------------------------------------------------------
        # category validation
        # ---------------------------------------------------------

        category_missing = self._missing_mask(
            dataframe["category"]
        )

        self._append_reason(
            rejection_reasons,
            category_missing,
            "category is required",
        )

        # ---------------------------------------------------------
        # unit_price validation
        # ---------------------------------------------------------

        unit_price_missing = self._missing_mask(
            dataframe["unit_price"]
        )

        self._append_reason(
            rejection_reasons,
            unit_price_missing,
            "unit_price is required",
        )

        unit_price_numeric = pd.to_numeric(
            dataframe["unit_price"],
            errors="coerce",
        )

        unit_price_not_numeric = (
            ~unit_price_missing
            & unit_price_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            unit_price_not_numeric,
            "unit_price must be numeric",
        )

        unit_price_negative = (
            ~unit_price_missing
            & ~unit_price_not_numeric
            & (unit_price_numeric < 0)
        )

        self._append_reason(
            rejection_reasons,
            unit_price_negative,
            "unit_price cannot be negative",
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