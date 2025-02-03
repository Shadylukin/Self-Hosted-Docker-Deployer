"""
Custom exceptions for Easy Docker Deploy.
"""
from typing import Optional

class EasyDockerDeployError(Exception):
    """Base exception class for Easy Docker Deploy."""
    
    def __init__(self, message: str, details: Optional[str] = None):
        """
        Initialize the exception.
        
        Args:
            message: Main error message
            details: Optional additional details about the error
        """
        self.message = message
        self.details = details
        super().__init__(message)

class ParserError(EasyDockerDeployError):
    """Raised when there's an error parsing application data."""
    pass

class ContentFetchError(ParserError):
    """Raised when there's an error fetching content from GitHub."""
    pass

class ParseError(ParserError):
    """Raised when there's an error parsing markdown content."""
    pass

class DockerError(EasyDockerDeployError):
    """Base class for Docker-related errors."""
    pass

class CommandError(DockerError):
    """Raised when a Docker command fails."""
    pass

class NetworkError(DockerError):
    """Raised when there's an error with Docker networks."""
    pass

class DeploymentError(EasyDockerDeployError):
    """Base class for deployment-related errors."""
    pass

class PortAllocationError(DeploymentError):
    """Raised when a port cannot be allocated."""
    pass

class VolumeError(DeploymentError):
    """Raised when there's an error with volume management."""
    pass

class ConfigurationError(EasyDockerDeployError):
    """Raised when there's an error in the configuration."""
    pass

class ValidationError(EasyDockerDeployError):
    """Raised when validation fails."""
    pass

class CacheError(EasyDockerDeployError):
    """Raised when there's an error with caching."""
    pass 