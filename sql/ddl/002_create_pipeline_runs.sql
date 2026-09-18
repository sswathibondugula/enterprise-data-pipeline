/*
Description:
Creates the pipeline_runs control table.

This table stores operational information for each ETL pipeline execution,
including run status, batch information, record counts, timestamps,
and failure details.
*/

CREATE TABLE IF NOT EXISTS etl_control.pipeline_runs (
    run_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    batch_id VARCHAR(100) NOT NULL,

    pipeline_name VARCHAR(100) NOT NULL,

    source_name VARCHAR(255),

    status VARCHAR(20) NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    finished_at TIMESTAMPTZ,

    total_records INTEGER NOT NULL DEFAULT 0,

    valid_records INTEGER NOT NULL DEFAULT 0,

    rejected_records INTEGER NOT NULL DEFAULT 0,

    excluded_records INTEGER NOT NULL DEFAULT 0,

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT chk_pipeline_run_status
        CHECK (
            status IN (
                'RUNNING',
                'SUCCESS',
                'FAILED'
            )
        ),

    CONSTRAINT chk_pipeline_run_counts
        CHECK (
            total_records >= 0
            AND valid_records >= 0
            AND rejected_records >= 0
            AND excluded_records >= 0
        )
);