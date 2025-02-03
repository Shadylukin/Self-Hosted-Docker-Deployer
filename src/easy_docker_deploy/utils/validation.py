"""
Validation utilities for Easy Docker Deploy.
"""
import re
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from .exceptions import ValidationError
from .logging import get_logger, log_with_context

logger = get_logger(__name__)

def validate_docker_url(url: str) -> Optional[str]:
    """
    Validate and normalize a Docker image URL.
    
    Args:
        url: URL to validate
        
    Returns:
        Normalized URL or None if invalid
    """
    if not url or not isinstance(url, str):
        return None
    url = url.strip()
    if not url:
        return None

    # Docker image name components regex patterns
    name_component = r'[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?'
    domain = fr'(?:{name_component}(?:\.{name_component})+)'  # Must have at least one dot
    path_component = fr'(?:/{name_component})'

    # Valid patterns:
    # 1. domain/path/image[:tag]
    # 2. user/image[:tag]
    # 3. image[:tag]
    if '/' in url:
        parts = url.split('/')
        if len(parts) > 3:
            return None
            
        # Check if first part is a domain (has dots)
        if len(parts) == 3 and '.' not in parts[0]:
            return None
            
        # Validate each part
        for part in parts[:-1]:  # All parts except the last one
            if not re.match(fr'^{name_component}$', part.lower()):
                return None
    
    # Extract and validate the image name and tag
    image_parts = parts[-1].split(':') if '/' in url else url.split(':')
    if len(image_parts) > 2:
        return None
        
    image = image_parts[0]
    tag = image_parts[1] if len(image_parts) == 2 else 'latest'
    
    # Validate image name
    if not re.match(fr'^{name_component}$', image.lower()):
        return None
        
    # Validate tag
    if not re.match(r'^[a-z0-9][\w.-]*$', tag.lower()):
        return None

    # Determine registry and namespace
    if '/' not in url:
        # Simple image name like "nginx"
        registry, namespace = "docker.io", "library"
    elif len(parts) == 2:
        # user/image format
        namespace = parts[0]
        registry = "docker.io"
    else:  # len(parts) == 3
        # registry/user/image format
        registry, namespace = parts[0], parts[1]

    return f"{registry}/{namespace}/{image}:{tag}"

def validate_port_mapping(port: Union[int, str, None]) -> Optional[str]:
    """
    Validate and normalize a port mapping.
    
    Args:
        port: Port mapping to validate (can be int, str like "80:8080", or None)
        
    Returns:
        Normalized port mapping or None if not provided
        
    Raises:
        ValidationError: If port mapping is invalid
    """
    if port is None:
        return None
        
    try:
        # Handle integer (simple host port)
        if isinstance(port, int):
            if not 1 <= port <= 65535:
                raise ValidationError(f"Port {port} out of valid range (1-65535)")
            return f"{port}:80"
        
        # Handle string (host:container format)
        if isinstance(port, str):
            parts = port.split(":")
            if len(parts) != 2:
                raise ValidationError(f"Invalid port mapping format: {port}")
            
            host_port, container_port = map(int, parts)
            if not (1 <= host_port <= 65535 and 1 <= container_port <= 65535):
                raise ValidationError(f"Port(s) out of valid range (1-65535): {port}")
            
            return f"{host_port}:{container_port}"
        
        raise ValidationError(f"Invalid port mapping type: {type(port)}")
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Port mapping validation failed",
            **log_with_context(
                port=port,
                error=str(e)
            )
        )
        raise ValidationError(f"Invalid port mapping: {port}") from e

def _validate_windows_path(path: str) -> None:
    """
    Validate a Windows path.
    
    Args:
        path: Path to validate
        
    Raises:
        ValidationError: If path is invalid
    """
    # Must have drive letter
    if not re.match(r'^[A-Za-z]:', path):
        raise ValidationError(f"Invalid Windows path: {path}")
    
    # Must have path separator after drive letter
    if not re.match(r'^[A-Za-z]:[/\\]', path):
        raise ValidationError(f"Invalid volume mapping format: {path}")

def _validate_windows_volume_path(path: str, is_container_path: bool = False) -> None:
    """
    Validate a Windows volume path.
    
    Args:
        path: Path to validate
        is_container_path: Whether this is a container path (which cannot be a Windows path)
        
    Raises:
        ValidationError: If path is invalid
    """
    # Check if path looks like a Windows path
    has_drive_letter = bool(re.match(r'^[A-Za-z]:', path))
    has_path_separator = bool(re.match(r'^[A-Za-z]:[/\\]', path))
    
    if is_container_path:
        if has_drive_letter or '\\' in path:
            raise ValidationError("Container path cannot be a Windows path")
        return
        
    # Host path validation
    if not has_drive_letter:
        raise ValidationError("Invalid Windows path")
    if not has_path_separator and len(path) > 2:  # Allow bare drive letter
        raise ValidationError("Invalid Windows path")

def _validate_windows_volume_mapping(volume: str) -> Optional[str]:
    """
    Validate and normalize a Windows volume mapping.
    
    Args:
        volume: Volume mapping to validate
        
    Returns:
        Normalized volume mapping
        
    Raises:
        ValidationError: If volume mapping is invalid
    """
    # Convert backslashes to forward slashes
    volume = volume.replace('\\', '/')
    
    # Handle bare drive letter case (e.g., "C:")
    if re.match(r'^[A-Za-z]:$', volume):
        raise ValidationError("Invalid volume mapping format")
    
    # Must start with a drive letter (e.g., "C:/...")
    if not re.match(r'^[A-Za-z]:', volume):
        raise ValidationError("Invalid Windows path")
    
    drive = volume[:2]  # e.g., "C:"
    rest = volume[2:]   # e.g., "/folder" or "/folder:container"
    
    # Split the host path from container path on the first colon
    host_part, sep, container_part = rest.partition(':')
    
    # If no colon, there's no container path -> default to "/data"
    if not sep:
        host_path = drive + host_part
        _validate_windows_volume_path(host_path)
        host_path = str(Path(host_path).resolve())
        return f"{host_path}:/data"
    
    # Validate the host path
    host_path = drive + host_part
    _validate_windows_volume_path(host_path)
    host_path = str(Path(host_path).resolve())
    
    # Now handle the container_part. We need to match the test expectations:
    # 1. If there's more than one colon in container_part -> "Invalid container path"
    # 2. If there's exactly one colon and it looks like a Windows path -> "Container path cannot be a Windows path"
    # 3. Otherwise, container_part is valid
    colon_count = container_part.count(':')
    if colon_count >= 1:
        # Example: "C:/path2" has 1 colon => container_part looks like a Windows path
        # Example: "C:/path2:path3" has 2 colons => "Invalid container path"
        if colon_count == 1 and re.match(r'^[A-Za-z]:', container_part):
            raise ValidationError("Container path cannot be a Windows path")
        else:
            raise ValidationError("Invalid container path")
    
    # Finally, if no extra colon and it's not a Windows path, we accept it
    if re.match(r'^[A-Za-z]:', container_part):
        # e.g., "C:/another" (single colon, but definitely Windows)
        raise ValidationError("Container path cannot be a Windows path")
    
    return f"{host_path}:{container_part}"

def _validate_unix_volume_mapping(volume: str) -> str:
    """
    Validate and normalize a Unix volume mapping.
    
    Args:
        volume: Volume mapping to validate
        
    Returns:
        Normalized volume mapping
        
    Raises:
        ValidationError: If volume mapping is invalid
    """
    if volume.count(':') != 1:
        raise ValidationError(f"Invalid volume mapping format: {volume}")
    
    host_path, container_path = volume.split(':')
    
    # Normalize and validate host path
    try:
        host_path = str(Path(host_path).resolve())
    except Exception as e:
        raise ValidationError(f"Invalid host path: {host_path}") from e
    
    # Normalize and validate container path
    container_path = container_path.lstrip('/')
    if not container_path:
        container_path = "data"
    if ':' in container_path:
        raise ValidationError(f"Invalid container path: {container_path}")
    
    return f"{host_path}:/{container_path}"

def validate_volume_mapping(volume: Union[str, Path, None]) -> Optional[str]:
    """
    Validate and normalize a volume mapping.
    
    Args:
        volume: Volume mapping to validate
        
    Returns:
        Normalized volume mapping or None if not provided
        
    Raises:
        ValidationError: If volume mapping is invalid
    """
    if volume is None:
        return None
    
    try:
        # Convert Path object to string
        if isinstance(volume, Path):
            volume = str(volume)
            return f"{volume}:/data"
        
        # Handle string
        if isinstance(volume, str):
            if os.name == "nt":
                return _validate_windows_volume_mapping(volume)
            else:
                return _validate_unix_volume_mapping(volume)
        
        raise ValidationError(f"Invalid volume mapping type: {type(volume)}")
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Volume mapping validation failed",
            **log_with_context(
                volume=volume,
                error=str(e)
            )
        )
        raise ValidationError(f"Invalid volume mapping: {volume}") from e

def validate_environment_vars(env_vars: Optional[Dict[str, str]]) -> Optional[Dict[str, str]]:
    """
    Validate environment variables.
    
    Args:
        env_vars: Dictionary of environment variables to validate
        
    Returns:
        Validated environment variables or None if not provided
        
    Raises:
        ValidationError: If environment variables are invalid
    """
    if env_vars is None:
        return None
        
    try:
        # Validate each key-value pair
        validated = {}
        for key, value in env_vars.items():
            # Validate key format
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValidationError(f"Invalid environment variable name: {key}")
            
            # Convert value to string
            validated[key] = str(value)
        
        return validated
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Environment variables validation failed",
            **log_with_context(error=str(e))
        )
        raise ValidationError("Invalid environment variables") from e

def validate_application_name(name: str) -> str:
    """
    Validate and normalize an application name.
    
    Args:
        name: Application name to validate
        
    Returns:
        Normalized application name
        
    Raises:
        ValidationError: If name is invalid
    """
    try:
        # Remove unwanted characters and normalize
        normalized = name.strip().lower()
        normalized = re.sub(r'[^a-z0-9-_.]', '-', normalized)
        normalized = re.sub(r'[-_]+', '-', normalized)  # Replace multiple dashes/underscores
        normalized = normalized.strip('-')  # Remove leading/trailing dashes
        
        if not normalized:
            raise ValidationError("Application name cannot be empty")
            
        return normalized
        
    except ValidationError:
        raise
    except Exception as e:
        logger.error(
            "Application name validation failed",
            **log_with_context(
                name=name,
                error=str(e)
            )
        )
        raise ValidationError(f"Invalid application name: {name}") from e 