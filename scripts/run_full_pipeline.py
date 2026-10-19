"""Run the complete enterprise ETL workflow."""

import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from enterprise_etl.observability.logging_config import (
    configure_logging,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class PipelineStep:
    """Define one executable step in the ETL workflow."""

    name: str
    script_name: str


PIPELINE_STEPS = (
    PipelineStep(
        name="Customer ingestion",
        script_name="run_customer_pipeline.py",
    ),
    PipelineStep(
        name="Product ingestion",
        script_name="run_product_pipeline.py",
    ),
    PipelineStep(
        name="Order ingestion",
        script_name="run_order_pipeline.py",
    ),
    PipelineStep(
        name="Order-item ingestion",
        script_name="run_order_item_pipeline.py",
    ),
    PipelineStep(
        name="Sales fact load",
        script_name="run_sales_fact_load.py",
    ),
    PipelineStep(
        name="Warehouse data-quality checks",
        script_name="run_data_quality_checks.py",
    ),
)


def run_step(
    step: PipelineStep,
) -> None:
    """Run one pipeline script and fail if the script fails."""

    script_path = (
        PROJECT_ROOT
        / "scripts"
        / step.script_name
    )

    if not script_path.exists():
        raise FileNotFoundError(
            f"Pipeline script does not exist: {script_path}"
        )

    subprocess.run(
        [
            sys.executable,
            str(script_path),
        ],
        cwd=PROJECT_ROOT,
        check=True,
    )


def main() -> None:
    """Execute the complete ETL workflow in dependency order."""

    logger = configure_logging(
        PROJECT_ROOT
    )

    logger.info(
        "Full enterprise ETL pipeline starting."
    )

    completed_steps = 0

    try:
        for step_number, step in enumerate(
            PIPELINE_STEPS,
            start=1,
        ):
            logger.info(
                "Starting pipeline step %s/%s: %s",
                step_number,
                len(PIPELINE_STEPS),
                step.name,
            )

            run_step(
                step
            )

            completed_steps += 1

            logger.info(
                "Completed pipeline step %s/%s: %s",
                step_number,
                len(PIPELINE_STEPS),
                step.name,
            )

    except subprocess.CalledProcessError as exc:
        logger.exception(
            "Full pipeline stopped because a child "
            "pipeline failed. Return code: %s",
            exc.returncode,
        )

        raise

    except Exception:
        logger.exception(
            "Full pipeline terminated unexpectedly."
        )

        raise

    logger.info(
        "Full enterprise ETL pipeline completed successfully. "
        "Completed steps: %s/%s",
        completed_steps,
        len(PIPELINE_STEPS),
    )


if __name__ == "__main__":
    main()