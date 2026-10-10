/*
Description:
Populates the warehouse date dimension.

The script generates one row per calendar date from
January 1, 2020 through December 31, 2035.
*/

INSERT INTO warehouse.dim_date (
    date_key,
    full_date,
    year_number,
    quarter_number,
    month_number,
    month_name,
    day_of_month,
    day_of_week,
    day_name,
    week_of_year,
    is_weekend
)
SELECT
    TO_CHAR(calendar_date, 'YYYYMMDD')::INTEGER AS date_key,
    calendar_date::DATE AS full_date,
    EXTRACT(YEAR FROM calendar_date)::INTEGER AS year_number,
    EXTRACT(QUARTER FROM calendar_date)::INTEGER AS quarter_number,
    EXTRACT(MONTH FROM calendar_date)::INTEGER AS month_number,
    TO_CHAR(calendar_date, 'FMMonth') AS month_name,
    EXTRACT(DAY FROM calendar_date)::INTEGER AS day_of_month,
    EXTRACT(ISODOW FROM calendar_date)::INTEGER AS day_of_week,
    TO_CHAR(calendar_date, 'FMDay') AS day_name,
    EXTRACT(WEEK FROM calendar_date)::INTEGER AS week_of_year,
    EXTRACT(ISODOW FROM calendar_date) IN (6, 7) AS is_weekend
FROM generate_series(
    DATE '2020-01-01',
    DATE '2035-12-31',
    INTERVAL '1 day'
) AS calendar_date
ON CONFLICT (date_key)
DO NOTHING;