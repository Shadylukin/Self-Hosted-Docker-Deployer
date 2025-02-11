"""
Docker operations manager.
"""
import json
import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

class DockerError(Exception):
    """Base class for Docker-related errors."""
    pass

class CommandError(DockerError):
    """Raised when a Docker command fails."""
    pass

class NetworkError(DockerError):
    """Raised when there's an error with Docker networks."""
    pass

class DockerManager:
    """Manager for Docker operations."""
    
    def __init__(self):
        self._verify_docker_installed()
        self._verify_compose_installed()
    
    def _verify_docker_installed(self) -> None:
        """Verify that Docker is installed and running."""
        try:
            result = subprocess.run(
                ["docker", "info"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug("Docker is installed and running")
        except subprocess.CalledProcessError as e:
            logger.error(
                "Docker verification failed",
                **log_with_context(error=str(e))
            )
            raise DockerError("Docker is not installed or not running") from e
    
    def _verify_compose_installed(self) -> None:
        """Verify that Docker Compose is installed."""
        try:
            result = subprocess.run(
                ["docker", "compose", "version"],
                capture_output=True,
                text=True,
                check=True
            )
            logger.debug("Docker Compose is installed")
        except subprocess.CalledProcessError as e:
            logger.error(
                "Docker Compose verification failed",
                **log_with_context(error=str(e))
            )
            raise DockerError("Docker Compose is not installed") from e
    
    def start_container(self, deploy_dir: Path) -> None:
        """
        Start a container using docker-compose.
        
        Args:
            deploy_dir: Directory containing docker-compose.yml
            
        Raises:
            CommandError: If the command fails
        """
        try:
            # Check if docker-compose is installed
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise CommandError("docker-compose command not found. Please install docker-compose.")
            
            logger.info(
                "Starting container",
                **log_with_context(directory=str(deploy_dir))
            )
            
            result = subprocess.run(
                ["docker", "compose", "up", "-d"],
                cwd=deploy_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(
                "Container started successfully",
                **log_with_context(directory=str(deploy_dir))
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to start container",
                **log_with_context(
                    directory=str(deploy_dir),
                    error=str(e),
                    output=e.output
                )
            )
            raise CommandError(f"Failed to start container: {e.output}") from e
    
    def stop_container(self, deploy_dir: Path) -> None:
        """
        Stop a container using docker-compose.
        
        Args:
            deploy_dir: Directory containing docker-compose.yml
            
        Raises:
            CommandError: If the command fails
        """
        try:
            # Check if docker-compose is installed
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                raise CommandError("docker-compose command not found. Please install docker-compose.")
            
            logger.info(
                "Stopping container",
                **log_with_context(directory=str(deploy_dir))
            )
            
            result = subprocess.run(
                ["docker", "compose", "down"],
                cwd=deploy_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(
                "Container stopped successfully",
                **log_with_context(directory=str(deploy_dir))
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to stop container",
                **log_with_context(
                    directory=str(deploy_dir),
                    error=str(e),
                    output=e.output
                )
            )
            raise CommandError(f"Failed to stop container: {e.output}") from e
    
    def get_container_status(self, deploy_dir: Path) -> Dict[str, str]:
        """
        Get status of containers in a docker-compose project.
        
        Args:
            deploy_dir: Directory containing docker-compose.yml
            
        Returns:
            Dictionary mapping container names to their status
            
        Raises:
            CommandError: If the command fails
        """
        try:
            result = subprocess.run(
                ["docker", "compose", "ps", "--format", "json"],
                cwd=deploy_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Parse JSON output
            containers = json.loads(result.stdout)
            return {
                container["Name"]: container["State"]
                for container in containers
            }
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to get container status",
                **log_with_context(
                    directory=str(deploy_dir),
                    error=str(e),
                    output=e.output
                )
            )
            raise CommandError(f"Failed to get container status: {e.output}") from e
        except json.JSONDecodeError as e:
            logger.error(
                "Failed to parse container status",
                **log_with_context(
                    directory=str(deploy_dir),
                    error=str(e)
                )
            )
            raise CommandError(f"Failed to parse container status: {str(e)}") from e
    
    def get_container_logs(self, deploy_dir: Path, tail: Optional[int] = None) -> str:
        """
        Get logs from containers in a docker-compose project.
        
        Args:
            deploy_dir: Directory containing docker-compose.yml
            tail: Number of lines to tail from the end
            
        Returns:
            Container logs as a string
            
        Raises:
            CommandError: If the command fails
        """
        try:
            cmd = ["docker", "compose", "logs"]
            if tail is not None:
                cmd.extend(["--tail", str(tail)])
            
            result = subprocess.run(
                cmd,
                cwd=deploy_dir,
                capture_output=True,
                text=True,
                check=True
            )
            
            return result.stdout
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to get container logs",
                **log_with_context(
                    directory=str(deploy_dir),
                    error=str(e),
                    output=e.output
                )
            )
            raise CommandError(f"Failed to get container logs: {e.output}") from e
    
    def ensure_network_exists(self, network: str) -> None:
        """
        Ensure a Docker network exists, creating it if necessary.
        
        Args:
            network: Name of the network
            
        Raises:
            NetworkError: If network creation fails
        """
        try:
            # Check if network exists
            result = subprocess.run(
                ["docker", "network", "inspect", network],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                logger.debug(f"Network {network} already exists")
                return
            
            # Create network if it doesn't exist
            logger.info(
                "Creating network",
                **log_with_context(network=network)
            )
            
            result = subprocess.run(
                ["docker", "network", "create", network],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(
                "Network created successfully",
                **log_with_context(network=network)
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to create network",
                **log_with_context(
                    network=network,
                    error=str(e),
                    output=e.output
                )
            )
            raise NetworkError(f"Failed to create network {network}: {e.output}") from e
    
    def pull_image(self, image: str) -> None:
        """
        Pull a Docker image.
        
        Args:
            image: Image to pull (e.g. 'nginx:latest')
            
        Raises:
            CommandError: If the pull fails
        """
        try:
            logger.info(
                "Pulling image",
                **log_with_context(image=image)
            )
            
            result = subprocess.run(
                ["docker", "pull", image],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(
                "Image pulled successfully",
                **log_with_context(image=image)
            )
            
        except subprocess.CalledProcessError as e:
            logger.error(
                "Failed to pull image",
                **log_with_context(
                    image=image,
                    error=str(e),
                    output=e.output
                )
            )
            raise CommandError(f"Failed to pull image {image}: {e.output}") from e

# Global manager instance
_manager: Optional[DockerManager] = None

def get_docker_manager() -> DockerManager:
    """Get the global Docker manager instance."""
    global _manager
    if _manager is None:
        _manager = DockerManager()
    return _manager 
