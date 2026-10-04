/*
Description:
Creates the product dimension table.

product_key:
    Warehouse-generated surrogate key.

product_id:
    Business key received from the source system.
*/

CREATE TABLE IF NOT EXISTS warehouse.dim_product (
    product_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    product_id BIGINT NOT NULL,

    product_name VARCHAR(255) NOT NULL,

    category VARCHAR(100) NOT NULL,

    unit_price NUMERIC(12, 2) NOT NULL,

    source_name VARCHAR(255) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dim_product_product_id
        UNIQUE (product_id),

    CONSTRAINT chk_dim_product_unit_price
        CHECK (unit_price >= 0)
);