"""
Service layer for handling Docker deployments.
"""
import os
import socket
import subprocess
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..config.settings import get_config
from ..config.docker import DockerConfig
from ..config.yaml_manager import YAMLManager
from ..parser.github_parser import Application
from ..utils.logging import get_logger, log_with_context
from ..utils.exceptions import DeploymentError

logger = get_logger(__name__)

class PortAllocationError(DeploymentError):
    """Raised when a port cannot be allocated."""
    pass

class VolumeError(DeploymentError):
    """Raised when there's an error with volume management."""
    pass

class ConfigurationError(DeploymentError):
    """Raised when there's an error in the deployment configuration."""
    pass

class DeploymentService:
    """Service for handling Docker deployments."""
    
    def __init__(self):
        self.config = get_config()
        self.base_dir = Path(self.config.default_volume_base).resolve()
        self.yaml_manager = YAMLManager(self.config.base_dir)
        
        # Common port mappings for well-known applications
        self.PORT_MAPPINGS = {
            "wiki.js": [(3000, 3000)],
            "gitea": [(3000, 3000), (22, 22)],
            "gitlab": [(80, 80), (22, 22)],
            "wordpress": [(80, 80)],
            "nextcloud": [(80, 80)],
            "jellyfin": [(8096, 8096)],
            "heimdall": [(80, 80), (443, 443)],
        }
        
        # Common volume mappings for well-known applications
        self.VOLUME_MAPPINGS = {
            "wiki.js": [("/data", "data"), ("/config", "config")],
            "gitea": [("/data", "data")],
            "gitlab": [("/etc/gitlab", "config"), ("/var/opt/gitlab", "data")],
            "wordpress": [("/var/www/html", "data")],
            "nextcloud": [("/var/www/html", "data")],
        }
        
        # Common environment variables for well-known applications
        self.ENV_VARS = {
            "wordpress": {
                "WORDPRESS_DB_HOST": "db",
                "WORDPRESS_DB_USER": "wordpress",
                "WORDPRESS_DB_PASSWORD": "wordpress",
                "WORDPRESS_DB_NAME": "wordpress"
            },
            "nextcloud": {
                "MYSQL_HOST": "db",
                "MYSQL_DATABASE": "nextcloud",
                "MYSQL_USER": "nextcloud",
                "MYSQL_PASSWORD": "nextcloud"
            },
        }
    
    def deploy(self, config: dict) -> None:
        """
        Deploy services using Docker Compose.
        
        Args:
            config: Dictionary containing service configurations
            
        Raises:
            DeploymentError: If deployment fails
        """
        try:
            # Create Docker network if it doesn't exist
            network_name = self.config.default_network
            logger.info(f"Creating Docker network: {network_name}")
            result = subprocess.run(
                ["docker", "network", "create", network_name],
                capture_output=True,
                text=True
            )
            if result.returncode != 0 and "already exists" not in result.stderr:
                raise DeploymentError(
                    f"Failed to create Docker network: {result.stderr}"
                )
            
            # Update configuration
            logger.info("Updating service configuration")
            self.yaml_manager.update_config(config)
            
            # Deploy using docker-compose
            logger.info("Starting Docker Compose deployment")
            result = subprocess.run(
                ["docker-compose", "-f", str(self.yaml_manager.compose_file), "up", "-d"],
                cwd=str(self.yaml_manager.base_dir),
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                raise DeploymentError(
                    f"Docker Compose deployment failed: {result.stderr}"
                )
                
            logger.info("Docker Compose deployment completed successfully")
            
        except Exception as e:
            logger.error(f"Deployment failed: {str(e)}")
            if not isinstance(e, DeploymentError):
                raise DeploymentError(f"Failed to deploy services: {str(e)}")
            raise
    
    def deploy_application(self, app: Application) -> bool:
        """
        Deploy a Docker application.
        
        Args:
            app: Application to deploy
            
        Returns:
            True if deployment was successful
            
        Raises:
            DeploymentError: If deployment fails
        """
        try:
            logger.info(
                "Starting deployment",
                **log_with_context(
                    application=app.name,
                    category=app.category
                )
            )
            
            # Create deployment configuration
            config = self._create_deployment_config(app)
            
            # Create deployment directory
            deploy_dir = self._create_deployment_directory(app)
            
            # Generate docker-compose.yml
            self._generate_compose_file(deploy_dir, config)
            
            # Generate .env file if needed
            if config.environment:
                self._generate_env_file(deploy_dir, config.environment)
            
            logger.info(
                "Deployment prepared successfully",
                **log_with_context(
                    application=app.name,
                    directory=str(deploy_dir)
                )
            )
            return True
            
        except Exception as e:
            logger.error(
                "Deployment failed",
                **log_with_context(
                    application=app.name,
                    error=str(e)
                )
            )
            raise DeploymentError(f"Failed to deploy {app.name}: {str(e)}") from e
    
    def _create_deployment_config(self, app: Application) -> DockerConfig:
        """Create deployment configuration for an application."""
        try:
            # Get container name
            container_name = self._sanitize_name(app.name)
            
            # Get port mappings
            port_mappings = []
            default_ports = self._get_default_ports(app.name)
            for container_port, suggested_host_port in default_ports:
                host_port = self._get_available_port(suggested_host_port)
                port_mappings.append(f"{host_port}:{container_port}")
            
            # Get volume mappings
            volume_mappings = []
            default_volumes = self._get_default_volumes(app.name)
            for container_path, relative_host_path in default_volumes:
                host_path = self.base_dir / container_name / relative_host_path
                volume_mappings.append(f"{host_path}:{container_path}")
            
            # Get environment variables
            env_vars = self._get_default_env_vars(app.name)
            
            return DockerConfig(
                image=app.docker_url or f"docker.io/{container_name}:latest",
                container_name=container_name,
                ports=port_mappings,
                volumes=volume_mappings,
                environment=env_vars
            )
            
        except Exception as e:
            logger.error(
                "Failed to create deployment configuration",
                **log_with_context(
                    application=app.name,
                    error=str(e)
                )
            )
            raise ConfigurationError(f"Failed to create configuration: {str(e)}") from e
    
    def _create_deployment_directory(self, app: Application) -> Path:
        """Create and prepare deployment directory."""
        try:
            deploy_dir = self.base_dir / self._sanitize_name(app.name)
            deploy_dir.mkdir(parents=True, exist_ok=True)
            return deploy_dir
        except Exception as e:
            raise VolumeError(f"Failed to create deployment directory: {str(e)}") from e
    
    def _generate_compose_file(self, deploy_dir: Path, config: DockerConfig) -> None:
        """Generate docker-compose.yml file."""
        compose_file = deploy_dir / "docker-compose.yml"
        try:
            with open(compose_file, 'w') as f:
                f.write(config.to_compose_yaml())
        except Exception as e:
            raise ConfigurationError(f"Failed to generate docker-compose.yml: {str(e)}") from e
    
    def _generate_env_file(self, deploy_dir: Path, env_vars: Dict[str, str]) -> None:
        """Generate .env file."""
        env_file = deploy_dir / ".env"
        try:
            with open(env_file, 'w') as f:
                for key, value in env_vars.items():
                    f.write(f"{key}={value}\n")
        except Exception as e:
            raise ConfigurationError(f"Failed to generate .env file: {str(e)}") from e
    
    def _get_available_port(self, start_port: int) -> int:
        """Find the next available port starting from start_port."""
        port = start_port
        max_port = self.config.default_port_range[1]
        
        while port <= max_port:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('', port))
                    return port
            except OSError:
                port += 1
        
        raise PortAllocationError(f"No available ports found in range {start_port}-{max_port}")
    
    def _get_default_ports(self, app_name: str) -> List[Tuple[int, int]]:
        """Get default port mappings for an application."""
        lookup_name = self._sanitize_name(app_name)
        return self.PORT_MAPPINGS.get(lookup_name, [(80, 8080)])
    
    def _get_default_volumes(self, app_name: str) -> List[Tuple[str, str]]:
        """Get default volume mappings for an application."""
        lookup_name = self._sanitize_name(app_name)
        return self.VOLUME_MAPPINGS.get(lookup_name, [("/data", "data")])
    
    def _get_default_env_vars(self, app_name: str) -> Dict[str, str]:
        """Get default environment variables for an application."""
        lookup_name = self._sanitize_name(app_name)
        return self.ENV_VARS.get(lookup_name, {})
    
    @staticmethod
    def _sanitize_name(name: str) -> str:
        """Sanitize a name for use in Docker and filesystem."""
        return name.lower().replace(" ", "-").replace(".", "").replace("_", "-")

# Global service instance
_service: Optional[DeploymentService] = None

def get_deployment_service() -> DeploymentService:
    """Get the global deployment service instance."""
    global _service
    if _service is None:
        _service = DeploymentService()
    return _service 