/*
Description:
Creates the data-quality results table.

The table stores the outcome of automated data-quality checks
executed against staging and warehouse datasets.

Each row represents the result of one data-quality check
executed at a specific point in time.
*/

CREATE TABLE IF NOT EXISTS etl_control.data_quality_results (
    quality_result_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    check_name VARCHAR(150) NOT NULL,

    dataset_name VARCHAR(150) NOT NULL,

    check_type VARCHAR(50) NOT NULL,

    status VARCHAR(20) NOT NULL,

    checked_records INTEGER,

    failed_records INTEGER NOT NULL
        DEFAULT 0,

    failure_percentage NUMERIC(7, 4)
        NOT NULL
        DEFAULT 0,

    details TEXT,

    pipeline_name VARCHAR(100),

    batch_id VARCHAR(100),

    checked_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_data_quality_status
        CHECK (
            status IN (
                'PASS',
                'FAIL'
            )
        ),

    CONSTRAINT chk_data_quality_failed_records
        CHECK (
            failed_records >= 0
        ),

    CONSTRAINT chk_data_quality_checked_records
        CHECK (
            checked_records IS NULL
            OR checked_records >= 0
        ),

    CONSTRAINT chk_data_quality_failure_percentage
        CHECK (
            failure_percentage >= 0
            AND failure_percentage <= 100
        )
);