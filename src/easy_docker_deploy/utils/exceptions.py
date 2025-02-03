"""
Custom exceptions for the application.
"""

class ValidationError(Exception):
    """Raised when validation fails."""
    pass

class DeploymentError(Exception):
    """Raised when deployment fails."""
    pass

class ConfigurationError(Exception):
    """Raised when configuration is invalid."""
    pass

class DockerError(Exception):
    """Raised when Docker operations fail."""
    pass

class NetworkError(Exception):
    """Raised when network operations fail."""
    pass

class StorageError(Exception):
    """Raised when storage operations fail."""
    pass 