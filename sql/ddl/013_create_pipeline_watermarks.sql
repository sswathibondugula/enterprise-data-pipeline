CREATE TABLE IF NOT EXISTS etl_control.pipeline_watermarks (
    pipeline_name VARCHAR(100) NOT NULL,
    watermark_name VARCHAR(100) NOT NULL,
    watermark_value TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_pipeline_watermarks
        PRIMARY KEY (
            pipeline_name,
            watermark_name
        )
);