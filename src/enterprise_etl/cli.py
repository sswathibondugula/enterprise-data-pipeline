"""Command-line entry point for the ETL application."""

from .config import AppConfig
from .exceptions import EnterpriseETLError


def main() -> int:
    """Start the ETL application and validate its configuration."""
    try:
        config = AppConfig()
        config.validate()
    except EnterpriseETLError as exc:
        print(f"Application startup failed: {exc}")
        return 1

    print(f"ETL application is ready. Project root: {config.project_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())