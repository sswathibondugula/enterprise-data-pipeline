/*
Description:
Creates the warehouse date dimension.

Each row represents one calendar date.

The date dimension allows analytical queries to group sales by
year, quarter, month, week, weekday, and other calendar attributes.
*/

CREATE TABLE IF NOT EXISTS warehouse.dim_date (
    date_key INTEGER PRIMARY KEY,
    full_date DATE NOT NULL UNIQUE,

    year_number INTEGER NOT NULL,
    quarter_number INTEGER NOT NULL,
    month_number INTEGER NOT NULL,
    month_name VARCHAR(20) NOT NULL,

    day_of_month INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    day_name VARCHAR(20) NOT NULL,

    week_of_year INTEGER NOT NULL,
    is_weekend BOOLEAN NOT NULL
);