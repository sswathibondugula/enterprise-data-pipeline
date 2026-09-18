/*
Description:
Creates the customer staging table.

The table receives validated, cleaned, transformed, and business-eligible
customer records from the Python ETL pipeline before warehouse processing.
*/

CREATE TABLE IF NOT EXISTS staging.stg_customers (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL,

    customer_name VARCHAR(255) NOT NULL,

    country VARCHAR(100) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    source_name VARCHAR(255) NOT NULL,

    processed_at TIMESTAMPTZ NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);