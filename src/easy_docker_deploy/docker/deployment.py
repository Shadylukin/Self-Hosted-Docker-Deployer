"""
Docker deployment manager for Easy Docker Deploy.
"""
import os
from pathlib import Path
import re
import yaml
from typing import Dict, List, Optional
from ..config.docker import DockerConfig
from ..generator.compose import DockerComposeGenerator

class DeploymentManager:
    """Manages Docker deployments."""
    
    def __init__(self):
        """Initialize the deployment manager."""
        self.base_dir = Path.home() / ".easy-docker-deploy" / "deployments"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.generator = DockerComposeGenerator()
    
    def _sanitize_name(self, name: str) -> str:
        """Sanitize a name for use in paths and Docker."""
        # Remove URL components and special characters
        name = re.sub(r'https?://|www\.|\.com/?|\.org/?|\.io/?', '', name)
        name = re.sub(r'[^\w\-]', '_', name)
        return name.lower().strip('_')
    
    def _validate_port(self, port: str) -> Optional[int]:
        """Validate a port number."""
        try:
            port_num = int(port)
            if 1 <= port_num <= 65535:
                return port_num
            return None
        except (ValueError, TypeError):
            return None
    
    def _normalize_path(self, path: str) -> str:
        """Normalize a file system path."""
        # Convert Windows paths to proper format
        path = path.replace('\\', '/')
        # Remove any trailing slashes
        path = path.rstrip('/')
        return path
    
    def deploy(self, app_name: str, config: DockerConfig) -> bool:
        """
        Deploy a Docker application.
        
        Args:
            app_name: Name of the application
            config: Docker configuration
            
        Returns:
            bool: True if deployment was successful
        """
        try:
            # Sanitize the application name for the deployment directory
            safe_name = self._sanitize_name(app_name)
            deploy_dir = self.base_dir / safe_name
            deploy_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate docker-compose.yml
            compose_content = self.generator.generate_compose_file(config)
            
            # Write docker-compose.yml
            compose_file = deploy_dir / "docker-compose.yml"
            compose_file.write_text(compose_content)
            
            return True
            
        except Exception as e:
            print(f"Error during deployment: {str(e)}")
            return False
    
    def get_port_mapping(self, prompt: str = "Enter port") -> Optional[tuple[int, int]]:
        """
        Get a validated port mapping from user input.
        
        Args:
            prompt: Custom prompt for the port input
            
        Returns:
            Optional[tuple[int, int]]: Tuple of (container_port, host_port) or None if invalid
        """
        container_port = input(f"{prompt} (container): ")
        if not container_port:
            return None
            
        container_port_num = self._validate_port(container_port)
        if not container_port_num:
            print("Invalid port number. Please enter a number between 1 and 65535.")
            return None
            
        host_port = input(f"Enter host port for {container_port_num}: ")
        host_port_num = self._validate_port(host_port)
        if not host_port_num:
            print("Invalid port number. Please enter a number between 1 and 65535.")
            return None
            
        return (container_port_num, host_port_num)
    
    def get_volume_mapping(self) -> Optional[tuple[str, str]]:
        """
        Get a validated volume mapping from user input.
        
        Returns:
            Optional[tuple[str, str]]: Tuple of (container_path, host_path) or None if invalid
        """
        container_path = input("Enter container path: ")
        if not container_path:
            return None
            
        container_path = self._normalize_path(container_path)
        
        host_path = input(f"Enter host path: ")
        if not host_path:
            return None
            
        host_path = self._normalize_path(host_path)
        
        return (container_path, host_path)
    
    def get_env_variable(self) -> Optional[tuple[str, str]]:
        """
        Get an environment variable from user input.
        
        Returns:
            Optional[tuple[str, str]]: Tuple of (name, value) or None if invalid
        """
        name = input("Enter variable name: ")
        if not name or not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            print("Invalid variable name. Use letters, numbers, and underscores only.")
            return None
            
        value = input(f"Enter value for {name}: ")
        if not value:
            return None
            
        return (name, value) 