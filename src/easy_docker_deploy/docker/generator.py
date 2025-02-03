"""
Docker compose generator for creating docker-compose files.
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
import jinja2
import yaml

@dataclass
class DockerConfig:
    """Docker container configuration."""
    image: str
    ports: List[str]
    volumes: List[str]
    environment: Dict[str, str]
    container_name: Optional[str] = None

class DockerComposeGenerator:
    """Generates docker-compose.yml files."""
    
    def __init__(self, template_dir: Optional[Path] = None):
        self.template_dir = template_dir or Path(__file__).parent / "templates"
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            autoescape=True,
            trim_blocks=True,
            lstrip_blocks=True,
        )
    
    def generate_compose_file(self, service_name: str, config: DockerConfig) -> str:
        """Generate docker-compose.yml content."""
        compose_config = {
            'version': '3.8',
            'services': {
                service_name: {
                    'image': config.image,
                    'container_name': config.container_name or service_name,
                    'restart': 'unless-stopped',
                }
            }
        }
        
        service = compose_config['services'][service_name]
        
        # Add port mappings if any
        if config.ports:
            service['ports'] = config.ports
            
        # Add volume mappings if any
        if config.volumes:
            service['volumes'] = config.volumes
            
        # Add environment variables if any
        if config.environment:
            service['environment'] = config.environment
            
        return yaml.dump(compose_config, sort_keys=False, default_flow_style=False)
    
    def save_compose_file(self, output_path: Path, content: str) -> None:
        """Save docker-compose.yml file."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(content)
    
    def validate_config(self, config: DockerConfig) -> List[str]:
        """Validate the Docker configuration."""
        errors = []
        
        if not config.image:
            errors.append("Docker image is required")
        
        for port in config.ports:
            if ":" not in port:
                errors.append(f"Invalid port mapping: {port}")
        
        return errors 