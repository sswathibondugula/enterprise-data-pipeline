# Enterprise Data Pipeline

A production-style enterprise data engineering project built with Python and PostgreSQL.

The project demonstrates an end-to-end ETL architecture including:

- CSV source ingestion
- Raw data landing
- Schema validation
- Record-level validation
- Rejected-record quarantine
- Data cleaning and transformation
- PostgreSQL staging tables
- Dimension and fact loading
- Incremental processing using watermarks
- SHA-256 source-file idempotency
- Pipeline auditing
- Data-quality validation
- Centralized logging
- Automated testing with pytest
- CI/CD with GitHub Actions
- Docker-based deployment

## Technology Stack

- Python
- PostgreSQL
- SQLAlchemy
- pandas
- pytest
- Git / GitHub
- GitHub Actions
- Docker

## Project Status

The core ETL pipeline, warehouse loading, incremental processing, auditing, data-quality checks, testing, and CI/CD are implemented.

Dockerization and deployment configuration are currently being completed.