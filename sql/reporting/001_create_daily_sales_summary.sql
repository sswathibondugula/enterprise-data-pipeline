/*
Description:
Creates a reporting view that summarizes sales activity by date.

The view is built from warehouse.fact_sales and warehouse.dim_date
and is intended for reporting tools such as Power BI.

Grain:
One row per calendar date with sales activity.
*/

CREATE OR REPLACE VIEW reporting.daily_sales_summary AS

SELECT
    d.full_date,

    d.year_number,
    d.quarter_number,
    d.month_number,
    d.month_name,
    d.day_name,

    COUNT(DISTINCT f.order_id) AS total_orders,

    COUNT(f.order_item_id) AS total_order_items,

    SUM(f.quantity) AS total_units,

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
    ) AS pending_sales

FROM warehouse.fact_sales AS f

INNER JOIN warehouse.dim_date AS d
    ON d.date_key = f.date_key

GROUP BY
    d.full_date,
    d.year_number,
    d.quarter_number,
    d.month_number,
    d.month_name,
    d.day_name;