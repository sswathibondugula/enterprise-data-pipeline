/*
Description:
Creates the customer dimension table in the warehouse schema.

The table stores the trusted current representation of each customer.

customer_key:
    Warehouse-generated surrogate key.

customer_id:
    Business key received from the source system.
*/

CREATE TABLE IF NOT EXISTS warehouse.dim_customer (
    customer_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    customer_id BIGINT NOT NULL,

    customer_name VARCHAR(255) NOT NULL,

    country VARCHAR(100) NOT NULL,

    source_name VARCHAR(255) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    last_updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_dim_customer_customer_id
        UNIQUE (customer_id)
);