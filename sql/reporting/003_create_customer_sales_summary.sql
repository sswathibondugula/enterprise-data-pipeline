/*
Description:
Creates a reporting view that summarizes sales performance by customer.

The view combines warehouse.fact_sales with warehouse.dim_customer
and warehouse.dim_date to provide customer-level metrics.

Grain:
One row per customer.
*/

CREATE OR REPLACE VIEW reporting.customer_sales_summary AS

WITH customer_metrics AS (
    SELECT
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.country,

        COUNT(
            DISTINCT f.order_id
        ) AS total_orders,

        COUNT(
            f.order_item_id
        ) AS total_order_items,

        SUM(
            f.quantity
        ) AS total_units_purchased,

        ROUND(
            SUM(f.sales_amount),
            2
        ) AS lifetime_sales,

        ROUND(
            SUM(
                CASE
                    WHEN f.order_status = 'COMPLETED'
                    THEN f.sales_amount
                    ELSE 0
                END
            ),
            2
        ) AS completed_sales,

        ROUND(
            SUM(
                CASE
                    WHEN f.order_status = 'PENDING'
                    THEN f.sales_amount
                    ELSE 0
                END
            ),
            2
        ) AS pending_sales,

        MIN(
            d.full_date
        ) AS first_purchase_date,

        MAX(
            d.full_date
        ) AS last_purchase_date

    FROM warehouse.fact_sales AS f

    INNER JOIN warehouse.dim_customer AS c
        ON c.customer_key = f.customer_key

    INNER JOIN warehouse.dim_date AS d
        ON d.date_key = f.date_key

    GROUP BY
        c.customer_key,
        c.customer_id,
        c.customer_name,
        c.country
)

SELECT
    customer_key,
    customer_id,
    customer_name,
    country,

    total_orders,
    total_order_items,
    total_units_purchased,

    lifetime_sales,
    completed_sales,
    pending_sales,

    ROUND(
        lifetime_sales
        / NULLIF(
            total_orders,
            0
        ),
        2
    ) AS average_order_value,

    first_purchase_date,
    last_purchase_date

FROM customer_metrics;