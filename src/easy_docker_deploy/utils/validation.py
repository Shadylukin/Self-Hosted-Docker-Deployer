"""
Validation utilities for Docker deployments.
"""
import os
import re
from pathlib import Path
from typing import Optional, Union

from .exceptions import ValidationError

def validate_path(path: Union[str, Path]) -> Path:
    """
    Validate a filesystem path.
    
    Args:
        path: Path to validate
        
    Returns:
        Validated Path object
        
    Raises:
        ValidationError: If path is invalid
    """
    try:
        path_obj = Path(path).resolve()
        
        # Create directory if it doesn't exist
        path_obj.mkdir(parents=True, exist_ok=True)
        
        # Check if path is writable
        if not os.access(str(path_obj), os.W_OK):
            raise ValidationError(f"Path {path} is not writable")
            
        return path_obj
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid path {path}: {str(e)}")

def validate_port(port: Union[int, str]) -> str:
    """
    Validate a port number or mapping.
    
    Args:
        port: Port number or mapping (e.g. "8080" or "8080:80")
        
    Returns:
        Validated port mapping
        
    Raises:
        ValidationError: If port is invalid
    """
    try:
        # Handle port number
        if isinstance(port, int):
            if not 1 <= port <= 65535:
                raise ValidationError(f"Port {port} is out of range (1-65535)")
            return f"{port}:{port}"
            
        # Handle port mapping
        if isinstance(port, str):
            if ":" in port:
                host_port, container_port = port.split(":")
                if not (host_port.isdigit() and container_port.isdigit()):
                    raise ValidationError(f"Invalid port mapping format: {port}")
                if not (1 <= int(host_port) <= 65535 and 1 <= int(container_port) <= 65535):
                    raise ValidationError(f"Port numbers out of range in mapping: {port}")
                return port
            elif port.isdigit():
                port_num = int(port)
                if not 1 <= port_num <= 65535:
                    raise ValidationError(f"Port {port} is out of range (1-65535)")
                return f"{port}:{port}"
                
        raise ValidationError(f"Invalid port specification: {port}")
        
    except Exception as e:
        if isinstance(e, ValidationError):
            raise
        raise ValidationError(f"Invalid port {port}: {str(e)}")

def validate_network_name(name: str) -> str:
    """
    Validate a Docker network name.
    
    Args:
        name: Network name to validate
        
    Returns:
        Validated network name
        
    Raises:
        ValidationError: If name is invalid
    """
    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_.-]*$', name):
        raise ValidationError(
            f"Invalid network name: {name}. "
            "Network names must start with an alphanumeric character "
            "and can only contain alphanumeric characters, underscores, periods, and hyphens."
        )
    return name

def validate_environment_vars(env_vars: dict) -> dict:
    """
    Validate environment variables.
    
    Args:
        env_vars: Dictionary of environment variables
        
    Returns:
        Validated environment variables
        
    Raises:
        ValidationError: If environment variables are invalid
    """
    validated = {}
    for key, value in env_vars.items():
        # Validate key
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
            raise ValidationError(
                f"Invalid environment variable name: {key}. "
                "Names must start with a letter or underscore "
                "and can only contain alphanumeric characters and underscores."
            )
            
        # Convert value to string
        validated[key] = str(value)
        
    return validated 