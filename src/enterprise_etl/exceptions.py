"""Custom exceptions used throughout the ETL application."""


class EnterpriseETLError(Exception):
    """Base exception for all application-specific errors."""


class ConfigurationError(EnterpriseETLError):
    """Raised when application configuration is missing or invalid."""