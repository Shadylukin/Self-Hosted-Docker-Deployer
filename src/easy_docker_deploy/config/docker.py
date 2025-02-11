"""
Docker configuration classes and utilities.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import yaml

@dataclass
class DockerConfig:
    """Configuration for a Docker deployment."""
    
    image: str
    container_name: str
    ports: List[str] = field(default_factory=list)
    volumes: List[str] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)
    restart_policy: str = "unless-stopped"
    networks: List[str] = field(default_factory=lambda: ["default"])
    depends_on: List[str] = field(default_factory=list)
    command: Optional[str] = None
    entrypoint: Optional[str] = None
    
    def to_compose_dict(self) -> Dict:
        """Convert configuration to docker-compose format dictionary."""
        compose_config = {
            "version": "3.8",
            "services": {
                self.container_name: {
                    "image": self.image,
                    "container_name": self.container_name,
                    "restart": self.restart_policy,
                    "networks": self.networks
                }
            },
            "networks": {
                network: {"external": True} for network in self.networks
            }
        }
        
        service = compose_config["services"][self.container_name]
        
        # Add optional configurations
        if self.ports:
            service["ports"] = self.ports
        if self.volumes:
            service["volumes"] = self.volumes
        if self.environment:
            service["environment"] = self.environment
        if self.depends_on:
            service["depends_on"] = self.depends_on
        if self.command:
            service["command"] = self.command
        if self.entrypoint:
            service["entrypoint"] = self.entrypoint
            
        return compose_config
    
    def to_compose_yaml(self) -> str:
        """Convert configuration to docker-compose.yml format."""
        return yaml.dump(self.to_compose_dict(), default_flow_style=False, sort_keys=False)
    
    @classmethod
    def from_compose_dict(cls, compose_dict: Dict) -> "DockerConfig":
        """Create configuration from docker-compose format dictionary."""
        if "services" not in compose_dict:
            raise ValueError("Invalid docker-compose format: missing services section")
            
        if len(compose_dict["services"]) != 1:
            raise ValueError("Expected exactly one service in compose file")
            
        service_name = next(iter(compose_dict["services"]))
        service = compose_dict["services"][service_name]
        
        return cls(
            image=service["image"],
            container_name=service.get("container_name", service_name),
            ports=service.get("ports", []),
            volumes=service.get("volumes", []),
            environment=service.get("environment", {}),
            restart_policy=service.get("restart", "unless-stopped"),
            networks=service.get("networks", ["default"]),
            depends_on=service.get("depends_on", []),
            command=service.get("command"),
            entrypoint=service.get("entrypoint")
        )
    
    @classmethod
    def from_compose_yaml(cls, compose_yaml: str) -> "DockerConfig":
        """Create configuration from docker-compose.yml format string."""
        compose_dict = yaml.safe_load(compose_yaml)
        return cls.from_compose_dict(compose_dict)
