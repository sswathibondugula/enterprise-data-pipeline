/*
Description:
Creates the order staging table.

Each row represents one customer order received from the source system.

The table stores validated and transformed order records before
they are used to build warehouse sales facts.
*/

CREATE TABLE IF NOT EXISTS staging.stg_orders (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_id BIGINT NOT NULL,
    customer_id BIGINT NOT NULL,
    order_date DATE NOT NULL,
    order_status VARCHAR(30) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP
);