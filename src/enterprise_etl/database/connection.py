"""PostgreSQL connection configuration and engine creation."""

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, URL
from sqlalchemy.exc import SQLAlchemyError

from enterprise_etl.exceptions import (
    ConfigurationError,
    DatabaseConnectionError,
)


@dataclass(frozen=True)
class DatabaseConfig:
    """Database settings loaded from environment variables."""

    host: str
    port: int
    database: str
    username: str
    password: str = field(repr=False)

    @classmethod
    def from_environment(cls) -> "DatabaseConfig":
        """Create database configuration from environment variables."""
        load_dotenv()

        variables = {
            "DB_HOST": os.getenv("DB_HOST"),
            "DB_PORT": os.getenv("DB_PORT"),
            "DB_NAME": os.getenv("DB_NAME"),
            "DB_USER": os.getenv("DB_USER"),
            "DB_PASSWORD": os.getenv("DB_PASSWORD"),
        }

        missing_variables = [
            name
            for name, value in variables.items()
            if not value
        ]

        if missing_variables:
            missing = ", ".join(sorted(missing_variables))
            raise ConfigurationError(
                f"Missing database environment variables: {missing}"
            )

        try:
            port = int(variables["DB_PORT"])
        except ValueError as exc:
            raise ConfigurationError(
                "DB_PORT must be a valid integer"
            ) from exc

        return cls(
            host=variables["DB_HOST"],
            port=port,
            database=variables["DB_NAME"],
            username=variables["DB_USER"],
            password=variables["DB_PASSWORD"],
        )

    def create_url(self) -> URL:
        """Create a SQLAlchemy PostgreSQL connection URL."""
        return URL.create(
            drivername="postgresql+psycopg",
            username=self.username,
            password=self.password,
            host=self.host,
            port=self.port,
            database=self.database,
        )


def create_database_engine(config: DatabaseConfig) -> Engine:
    """Create the SQLAlchemy PostgreSQL engine."""
    return create_engine(
        config.create_url(),
        pool_pre_ping=True,
    )


def test_database_connection(engine: Engine) -> None:
    """Verify that PostgreSQL can execute a simple query."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise DatabaseConnectionError(
            "Unable to connect to PostgreSQL"
        ) from exc