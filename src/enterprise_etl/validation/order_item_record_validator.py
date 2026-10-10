"""Record-level validation for order-item data."""

import pandas as pd

from enterprise_etl.validation.record_validator import (
    ValidationResult,
)


class OrderItemRecordValidator:
    """Validate individual order-item records."""

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> ValidationResult:
        """Separate valid order items from rejected records."""

        rejection_reasons = pd.Series(
            "",
            index=dataframe.index,
            dtype="string",
        )

        # ---------------------------------------------------------
        # order_item_id validation
        # ---------------------------------------------------------

        order_item_id_missing = self._missing_mask(
            dataframe["order_item_id"]
        )

        self._append_reason(
            rejection_reasons,
            order_item_id_missing,
            "order_item_id is required",
        )

        order_item_id_numeric = pd.to_numeric(
            dataframe["order_item_id"],
            errors="coerce",
        )

        order_item_id_not_numeric = (
            ~order_item_id_missing
            & order_item_id_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            order_item_id_not_numeric,
            "order_item_id must be numeric",
        )

        order_item_id_not_integer = (
            ~order_item_id_missing
            & order_item_id_numeric.notna()
            & (order_item_id_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            order_item_id_not_integer,
            "order_item_id must be a whole number",
        )

        order_item_id_not_positive = (
            ~order_item_id_missing
            & order_item_id_numeric.notna()
            & (order_item_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            order_item_id_not_positive,
            "order_item_id must be greater than zero",
        )

        # ---------------------------------------------------------
        # order_id validation
        # ---------------------------------------------------------

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

        order_id_not_integer = (
            ~order_id_missing
            & order_id_numeric.notna()
            & (order_id_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            order_id_not_integer,
            "order_id must be a whole number",
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

        product_id_not_integer = (
            ~product_id_missing
            & product_id_numeric.notna()
            & (product_id_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            product_id_not_integer,
            "product_id must be a whole number",
        )

        product_id_not_positive = (
            ~product_id_missing
            & product_id_numeric.notna()
            & (product_id_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            product_id_not_positive,
            "product_id must be greater than zero",
        )

        # ---------------------------------------------------------
        # quantity validation
        # ---------------------------------------------------------

        quantity_missing = self._missing_mask(
            dataframe["quantity"]
        )

        self._append_reason(
            rejection_reasons,
            quantity_missing,
            "quantity is required",
        )

        quantity_numeric = pd.to_numeric(
            dataframe["quantity"],
            errors="coerce",
        )

        quantity_not_numeric = (
            ~quantity_missing
            & quantity_numeric.isna()
        )

        self._append_reason(
            rejection_reasons,
            quantity_not_numeric,
            "quantity must be numeric",
        )

        quantity_not_integer = (
            ~quantity_missing
            & quantity_numeric.notna()
            & (quantity_numeric % 1 != 0)
        )

        self._append_reason(
            rejection_reasons,
            quantity_not_integer,
            "quantity must be a whole number",
        )

        quantity_not_positive = (
            ~quantity_missing
            & quantity_numeric.notna()
            & (quantity_numeric <= 0)
        )

        self._append_reason(
            rejection_reasons,
            quantity_not_positive,
            "quantity must be greater than zero",
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
            & unit_price_numeric.notna()
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
        """Append a validation reason to matching records."""

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