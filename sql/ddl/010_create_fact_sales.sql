/*
Description:
Creates the sales fact table.

Grain:
One row represents one order item.

The fact table connects customer, product, and date dimensions
and stores measurable sales values such as quantity and sales amount.
*/

CREATE TABLE IF NOT EXISTS warehouse.fact_sales (
    sales_key BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    order_item_id BIGINT NOT NULL,
    order_id BIGINT NOT NULL,

    date_key INTEGER NOT NULL,
    customer_key BIGINT NOT NULL,
    product_key BIGINT NOT NULL,

    order_status VARCHAR(30) NOT NULL,

    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12, 2) NOT NULL,
    sales_amount NUMERIC(14, 2) NOT NULL,

    order_batch_id VARCHAR(100) NOT NULL,
    order_item_batch_id VARCHAR(100) NOT NULL,

    loaded_at TIMESTAMPTZ NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_fact_sales_order_item_id
        UNIQUE (order_item_id),

    CONSTRAINT fk_fact_sales_date
        FOREIGN KEY (date_key)
        REFERENCES warehouse.dim_date (date_key),

    CONSTRAINT fk_fact_sales_customer
        FOREIGN KEY (customer_key)
        REFERENCES warehouse.dim_customer (customer_key),

    CONSTRAINT fk_fact_sales_product
        FOREIGN KEY (product_key)
        REFERENCES warehouse.dim_product (product_key),

    CONSTRAINT chk_fact_sales_quantity
        CHECK (quantity > 0),

    CONSTRAINT chk_fact_sales_unit_price
        CHECK (unit_price >= 0),

    CONSTRAINT chk_fact_sales_sales_amount
        CHECK (sales_amount >= 0)
);