"""Record-level validation for order data."""

import pandas as pd

from enterprise_etl.exceptions import DataValidationError
from enterprise_etl.validation.record_validator import (
    ValidationResult,
)


class OrderRecordValidator:
    """Validate individual order records."""

    def __init__(
        self,
        allowed_statuses: tuple[str, ...],
    ) -> None:
        """Initialize validation with supported order statuses."""

        if not allowed_statuses:
            raise DataValidationError(
                "At least one allowed order status "
                "must be configured"
            )

        self.allowed_statuses = {
            status.strip().upper()
            for status in allowed_statuses
        }

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> ValidationResult:
        """Separate valid order records from rejected records."""

        rejection_reasons = pd.Series(
            "",
            index=dataframe.index,
            dtype="string",
        )

        order_id_missing = self._missing_mask(
            dataframe["order_id"]
        )

        self._append_reason(
            rejection_reasons,
            order_id_missing,
            "order_id is required",
        )

        order_id_numeric = pd.to_numeric(
            dataframe["order_id"],
            errors="coerce",
        )

        order_id_not_numeric = (
            ~order_id_missing
            & order_id_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            order_id_not_numeric,
            "order_id must be numeric",
        )

        order_id_not_positive = (
            ~order_id_missing
            & order_id_numeric.notna()
            & (order_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            order_id_not_positive,
            "order_id must be greater than zero",
        )

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

        customer_id_not_positive = (
            ~customer_id_missing
            & customer_id_numeric.notna()
            & (customer_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            customer_id_not_positive,
            "customer_id must be greater than zero",
        )

        order_date_missing = self._missing_mask(
            dataframe["order_date"]
        )

        self._append_reason(
            rejection_reasons,
            order_date_missing,
            "order_date is required",
        )

        parsed_dates = pd.to_datetime(
            dataframe["order_date"],
            format="%Y-%m-%d",
            errors="coerce",
        )

        order_date_invalid = (
            ~order_date_missing
            & parsed_dates.isna()
        )

        self._append_reason(
            rejection_reasons,
            order_date_invalid,
            "order_date must be a valid YYYY-MM-DD date",
        )

        order_status_missing = self._missing_mask(
            dataframe["order_status"]
        )

        self._append_reason(
            rejection_reasons,
            order_status_missing,
            "order_status is required",
        )

        normalized_status = (
            dataframe["order_status"]
            .astype("string")
            .str.strip()
            .str.upper()
        )

        order_status_invalid = (
            ~order_status_missing
            & ~normalized_status.isin(
                self.allowed_statuses
            )
        )

        self._append_reason(
            rejection_reasons,
            order_status_invalid,
            "order_status is not allowed",
        )

        rejected_mask = rejection_reasons.ne("")

        valid_records = dataframe.loc[
            ~rejected_mask
        ].copy()

        rejected_records = dataframe.loc[
            rejected_mask
        ].copy()

        rejected_records["rejection_reason"] = (
            rejection_reasons.loc[
                rejected_mask
            ]
        )

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
        """Identify null, empty, or whitespace-only values."""

        blank_mask = (
            series.astype("string")
            .str.strip()
            .eq("")
            .fillna(False)
        )

        return series.isna() | blank_mask

    @staticmethod
    def _append_reason(
        rejection_reasons: pd.Series,
        mask: pd.Series,
        message: str,
    ) -> None:
        """Append a validation message to matching records."""

        already_has_reason = (
            mask
            & rejection_reasons.ne("")
        )

        rejection_reasons.loc[
            already_has_reason
        ] += "; "

        rejection_reasons.loc[
            mask
        ] += message