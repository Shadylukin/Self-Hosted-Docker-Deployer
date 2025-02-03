"""
Deployment orchestrator for Easy Docker Deploy.
"""
from pathlib import Path
from typing import Dict, List, Optional
import docker
from docker.errors import DockerException
from ..docker.generator import DockerConfig

class DeploymentError(Exception):
    """Base exception for deployment errors."""
    pass

class Deployer:
    """Handles the deployment of Docker containers."""
    
    def __init__(self):
        try:
            self.client = docker.from_env()
        except DockerException as e:
            raise DeploymentError(f"Failed to connect to Docker daemon: {e}")
    
    def check_prerequisites(self) -> List[str]:
        """Check if all prerequisites are met."""
        issues = []
        
        try:
            version = self.client.version()
            if not version:
                issues.append("Unable to get Docker version")
        except DockerException as e:
            issues.append(f"Docker daemon not accessible: {e}")
        
        return issues
    
    def deploy_container(self, config: DockerConfig) -> str:
        """Deploy a container using the provided configuration."""
        try:
            # Pull the image
            self.client.images.pull(config.image)
            
            # Create and start the container
            container = self.client.containers.run(
                image=config.image,
                name=config.container_name,
                ports={p.split(':')[1]: p.split(':')[0] for p in config.ports},
                volumes={v.split(':')[0]: {'bind': v.split(':')[1], 'mode': 'rw'} 
                        for v in config.volumes},
                environment=config.environment,
                restart_policy={"Name": config.restart_policy},
                detach=True
            )
            
            return container.id
            
        except DockerException as e:
            raise DeploymentError(f"Failed to deploy container: {e}")
    
    def get_container_status(self, container_id: str) -> Dict[str, str]:
        """Get the status of a deployed container."""
        try:
            container = self.client.containers.get(container_id)
            return {
                "status": container.status,
                "name": container.name,
                "image": container.image.tags[0] if container.image.tags else "unknown",
                "created": container.attrs['Created'],
            }
        except DockerException as e:
            raise DeploymentError(f"Failed to get container status: {e}")
    
    def stop_container(self, container_id: str) -> None:
        """Stop a running container."""
        try:
            container = self.client.containers.get(container_id)
            container.stop()
        except DockerException as e:
            raise DeploymentError(f"Failed to stop container: {e}")
    
    def remove_container(self, container_id: str, force: bool = False) -> None:
        """Remove a container."""
        try:
            container = self.client.containers.get(container_id)
            container.remove(force=force)
        except DockerException as e:
            raise DeploymentError(f"Failed to remove container: {e}") 