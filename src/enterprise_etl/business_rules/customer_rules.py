"""Business rules for customer processing."""

from dataclasses import dataclass

import pandas as pd

from enterprise_etl.exceptions import DataValidationError


@dataclass
class BusinessRuleResult:
    """Store records included and excluded by business rules."""

    eligible_records: pd.DataFrame
    excluded_records: pd.DataFrame


class CustomerBusinessRules:
    """Apply customer eligibility rules for downstream processing."""

    def __init__(self, allowed_countries: tuple[str, ...]) -> None:
        """Initialize customer rules with supported countries."""
        if not allowed_countries:
            raise DataValidationError(
                "At least one allowed country must be configured"
            )

        self.allowed_countries = allowed_countries

    def apply(self, dataframe: pd.DataFrame) -> BusinessRuleResult:
        """Separate customers by supported-market eligibility."""
        if dataframe.empty:
            raise DataValidationError(
                "Cannot apply business rules to an empty dataset"
            )

        allowed = {
            country.casefold()
            for country in self.allowed_countries
        }

        country_values = (
            dataframe["country"]
            .astype("string")
            .str.strip()
            .str.casefold()
        )

        eligible_mask = country_values.isin(allowed)

        eligible_records = dataframe.loc[eligible_mask].copy()
        excluded_records = dataframe.loc[~eligible_mask].copy()

        excluded_records["exclusion_reason"] = (
            "Country is not in an allowed market"
        )

        return BusinessRuleResult(
            eligible_records=eligible_records.reset_index(drop=True),
            excluded_records=excluded_records.reset_index(drop=True),
        )