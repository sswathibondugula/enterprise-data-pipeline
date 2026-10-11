/*
Description:
Creates a reporting view that summarizes sales performance by product.

The view combines warehouse.fact_sales with warehouse.dim_product
to provide product-level metrics for analytics and Power BI.

Grain:
One row per product.
*/

CREATE OR REPLACE VIEW reporting.product_sales_summary AS

WITH product_metrics AS (
    SELECT
        p.product_key,
        p.product_id,
        p.product_name,
        p.category,

        COUNT(
            DISTINCT f.order_id
        ) AS total_orders,

        COUNT(
            f.order_item_id
        ) AS total_order_items,

        SUM(
            f.quantity
        ) AS total_units_sold,

        ROUND(
            SUM(f.sales_amount),
            2
        ) AS total_sales,

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

        ROUND(
            SUM(f.sales_amount)
            / NULLIF(
                SUM(f.quantity),
                0
            ),
            2
        ) AS average_selling_price

    FROM warehouse.fact_sales AS f

    INNER JOIN warehouse.dim_product AS p
        ON p.product_key = f.product_key

    GROUP BY
        p.product_key,
        p.product_id,
        p.product_name,
        p.category
)

SELECT
    product_key,
    product_id,
    product_name,
    category,

    total_orders,
    total_order_items,
    total_units_sold,

    total_sales,
    completed_sales,
    pending_sales,

    average_selling_price,

    ROUND(
        (
            total_sales
            / NULLIF(
                SUM(total_sales) OVER (),
                0
            )
        ) * 100,
        2
    ) AS revenue_contribution_pct

FROM product_metrics;