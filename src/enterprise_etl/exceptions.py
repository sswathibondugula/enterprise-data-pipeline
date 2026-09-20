"""Custom exceptions used throughout the ETL application."""


class EnterpriseETLError(Exception):
    """Base exception for all application-specific errors."""


class ConfigurationError(EnterpriseETLError):
    """Raised when application configuration is missing or invalid."""

class DataIngestionError(EnterpriseETLError):
    """Raised when data cannot be ingested from a source."""

class DataValidationError(EnterpriseETLError):
    """Raised when data fails validation rules."""

class DatabaseConnectionError(EnterpriseETLError):
    """Raised when the application cannot connect to the database."""

class DatabaseLoadError(EnterpriseETLError):
    """Raised when data cannot be loaded into the database."""

class DatabaseAuditError(EnterpriseETLError):
    """Raised when pipeline audit information cannot be stored."""