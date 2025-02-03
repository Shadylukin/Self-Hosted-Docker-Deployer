"""
Docker Compose file generator for Easy Docker Deploy.
"""
import yaml
from ..config.docker import DockerConfig

class DockerComposeGenerator:
    """Generates docker-compose.yml files."""
    
    def generate_compose_file(self, config: DockerConfig) -> str:
        """
        Generate docker-compose.yml content.
        
        Args:
            config: Docker configuration
            
        Returns:
            str: Generated docker-compose.yml content
        """
        compose_config = {
            "version": "3",
            "services": {
                config.container_name: {
                    "image": config.image,
                    "container_name": config.container_name,
                    "restart": config.restart_policy
                }
            }
        }
        
        service = compose_config["services"][config.container_name]
        
        # Add port mappings
        if config.ports:
            service["ports"] = config.ports
            
        # Add volume mappings
        if config.volumes:
            service["volumes"] = config.volumes
            
        # Add environment variables
        if config.environment:
            service["environment"] = config.environment
            
        # Generate YAML with proper formatting
        return yaml.dump(compose_config, default_flow_style=False, sort_keys=False) 