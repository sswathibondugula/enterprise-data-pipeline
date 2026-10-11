/*
Description:
Creates a reporting view that summarizes ETL pipeline health.

The view is built from etl_control.pipeline_runs and provides
operational metrics for monitoring pipeline executions.

Grain:
One row per pipeline.
*/

CREATE OR REPLACE VIEW reporting.pipeline_health_summary AS

WITH ranked_runs AS (
    SELECT
        run_id,
        pipeline_name,
        batch_id,
        source_name,
        status,
        total_records,
        valid_records,
        rejected_records,
        excluded_records,
        started_at,
        finished_at,
        error_message,

        ROW_NUMBER() OVER (
            PARTITION BY pipeline_name
            ORDER BY started_at DESC, run_id DESC
        ) AS run_rank

    FROM etl_control.pipeline_runs
),

pipeline_metrics AS (
    SELECT
        pipeline_name,

        COUNT(*) AS total_runs,

        COUNT(*) FILTER (
            WHERE status = 'SUCCESS'
        ) AS successful_runs,

        COUNT(*) FILTER (
            WHERE status = 'FAILED'
        ) AS failed_runs,

        SUM(total_records) AS total_records_processed,

        SUM(valid_records) AS total_valid_records,

        SUM(rejected_records) AS total_rejected_records,

        SUM(excluded_records) AS total_excluded_records,

        MAX(started_at) AS last_run_at

    FROM etl_control.pipeline_runs

    GROUP BY
        pipeline_name
)

SELECT
    metrics.pipeline_name,

    metrics.total_runs,
    metrics.successful_runs,
    metrics.failed_runs,

    metrics.total_records_processed,
    metrics.total_valid_records,
    metrics.total_rejected_records,
    metrics.total_excluded_records,

    ROUND(
        (
            metrics.successful_runs::NUMERIC
            / NULLIF(
                metrics.total_runs,
                0
            )
        ) * 100,
        2
    ) AS success_rate_pct,

    latest.status AS latest_status,

    latest.batch_id AS latest_batch_id,

    latest.source_name AS latest_source_name,

    latest.started_at AS latest_started_at,

    latest.finished_at AS latest_finished_at,

    latest.error_message AS latest_error_message

FROM pipeline_metrics AS metrics

INNER JOIN ranked_runs AS latest
    ON latest.pipeline_name = metrics.pipeline_name
    AND latest.run_rank = 1;