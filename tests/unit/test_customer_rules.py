"""Unit tests for customer business rules."""

import pandas as pd
import pytest

from enterprise_etl.business_rules.customer_rules import (
    CustomerBusinessRules,
)
from enterprise_etl.exceptions import DataValidationError


def test_customer_rules_keep_allowed_markets() -> None:
    """Customers from allowed markets remain eligible."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            },
            {
                "customer_id": 102,
                "name": "Ravi",
                "country": "India",
            },
        ]
    )

    rules = CustomerBusinessRules(
        allowed_countries=("Canada", "India")
    )

    result = rules.apply(dataframe)

    assert len(result.eligible_records) == 2
    assert result.excluded_records.empty


def test_customer_rules_exclude_unsupported_markets() -> None:
    """Customers outside allowed markets are separated."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "Canada",
            },
            {
                "customer_id": 102,
                "name": "Maria",
                "country": "Australia",
            },
        ]
    )

    rules = CustomerBusinessRules(
        allowed_countries=("Canada", "India")
    )

    result = rules.apply(dataframe)

    assert len(result.eligible_records) == 1
    assert len(result.excluded_records) == 1
    assert (
        result.excluded_records.loc[0, "exclusion_reason"]
        == "Country is not in an allowed market"
    )


def test_customer_rules_compare_countries_case_insensitively() -> None:
    """Market eligibility is independent of text casing."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Alice",
                "country": "CANADA",
            }
        ]
    )

    rules = CustomerBusinessRules(
        allowed_countries=("Canada",)
    )

    result = rules.apply(dataframe)

    assert len(result.eligible_records) == 1
    assert result.eligible_records.loc[0, "country"] == "CANADA"


def test_customer_rules_do_not_modify_input_dataframe() -> None:
    """Business-rule evaluation leaves input data unchanged."""
    dataframe = pd.DataFrame(
        [
            {
                "customer_id": 101,
                "name": "Maria",
                "country": "Australia",
            }
        ]
    )
    original_dataframe = dataframe.copy(deep=True)

    rules = CustomerBusinessRules(
        allowed_countries=("Canada",)
    )
    rules.apply(dataframe)

    pd.testing.assert_frame_equal(
        dataframe,
        original_dataframe,
    )


def test_customer_rules_require_allowed_country_configuration() -> None:
    """At least one allowed country must be configured."""
    with pytest.raises(DataValidationError) as error:
        CustomerBusinessRules(allowed_countries=())

    assert (
        "At least one allowed country must be configured"
        in str(error.value)
    )


def test_customer_rules_reject_empty_dataframe() -> None:
    """Business rules cannot operate on an empty dataset."""
    rules = CustomerBusinessRules(
        allowed_countries=("Canada",)
    )

    with pytest.raises(DataValidationError) as error:
        rules.apply(pd.DataFrame())

    assert (
        "Cannot apply business rules to an empty dataset"
        in str(error.value)
    )