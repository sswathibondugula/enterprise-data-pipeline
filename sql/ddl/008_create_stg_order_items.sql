/*
Description:
Creates the order-item staging table.

Each row represents one product line belonging to an order.

Order items will later become the grain of the sales fact table.
*/

CREATE TABLE IF NOT EXISTS staging.stg_order_items (
    staging_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_item_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,
    product_id BIGINT NOT NULL,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,

    batch_id VARCHAR(100) NOT NULL,
    source_name VARCHAR(255) NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_stg_order_items_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_stg_order_items_unit_price
        CHECK (unit_price >= 0)
);