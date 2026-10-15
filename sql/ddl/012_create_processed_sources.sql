/*
Description:
Creates the processed_sources control table.

The table records source files that have already been processed
successfully by an ETL pipeline.

A SHA-256 hash of the source file is stored so the ETL system can
identify the same file content even if the filename is unchanged.

This supports idempotent source processing.
*/

CREATE TABLE IF NOT EXISTS etl_control.processed_sources (
    processed_source_id BIGINT
        GENERATED ALWAYS AS IDENTITY
        PRIMARY KEY,

    pipeline_name VARCHAR(100) NOT NULL,

    source_name VARCHAR(255) NOT NULL,

    source_hash VARCHAR(64) NOT NULL,

    source_size_bytes BIGINT NOT NULL,

    batch_id VARCHAR(100) NOT NULL,

    processed_at TIMESTAMPTZ
        NOT NULL
        DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_processed_source_hash
        UNIQUE (
            pipeline_name,
            source_hash
        ),

    CONSTRAINT chk_processed_source_size
        CHECK (
            source_size_bytes >= 0
        )
);