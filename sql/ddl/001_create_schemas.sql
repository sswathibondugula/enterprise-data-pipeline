/*
Description:
Creates the PostgreSQL schemas used by the enterprise ETL system.

Schemas:
- etl_control : Pipeline execution, auditing, and operational metadata
- staging     : Intermediate data loaded by ETL pipelines
- warehouse   : Trusted analytical dimension and fact tables
- reporting   : Reporting-ready views and summary objects
*/

CREATE SCHEMA IF NOT EXISTS etl_control;

CREATE SCHEMA IF NOT EXISTS staging;

CREATE SCHEMA IF NOT EXISTS warehouse;

CREATE SCHEMA IF NOT EXISTS reporting;