/*
Description:
Creates the product staging table.

The table receives validated, cleaned, transformed, and eligible
product records before warehouse processing.
*/

CREATE TABLE IF NOT EXISTS staging.stg_products (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    product_id BIGINT NOT NULL,

    product_name VARCHAR(255) NOT NULL,

    category VARCHAR(100) NOT NULL,

    unit_price NUMERIC(12, 2) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    source_name VARCHAR(255) NOT NULL,

    processed_at TIMESTAMPTZ NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_stg_products_unit_price
        CHECK (unit_price >= 0)
);