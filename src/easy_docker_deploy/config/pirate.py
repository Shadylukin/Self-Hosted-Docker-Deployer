"""
Configuration module for Pirate mode services and settings.
This module provides preset configurations for media automation services.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..utils.logging import get_logger

logger = get_logger(__name__)

@dataclass
class ServiceConfig:
    """Configuration for a single service."""
    name: str
    description: str
    image: str
    ports: List[str]
    volumes: List[str]
    environment: Dict[str, str]

@dataclass
class PirateConfig:
    """Complete configuration for Pirate mode."""
    services: List[ServiceConfig]
    base_path: Path
    network_name: str = "pirate_network"
    compose_version: str = "3.8"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to Docker Compose format."""
        return {
            "version": self.compose_version,
            "services": {
                service.name: self._format_service_config(service)
                for service in self.services
            },
            "volumes": self._generate_volume_config(),
            "networks": {
                self.network_name: {
                    "driver": "bridge"
                }
            }
        }
    
    def _format_service_config(self, service: ServiceConfig) -> Dict[str, Any]:
        """Format a service configuration with proper paths."""
        paths = self._get_path_mappings()
        
        return {
            "image": service.image,
            "ports": service.ports,
            "volumes": [vol.format(**paths) for vol in service.volumes],
            "environment": service.environment,
            "networks": [self.network_name],
            "restart": "unless-stopped"
        }
    
    def _get_path_mappings(self) -> Dict[str, str]:
        """Get path mappings for volume configuration."""
        return {
            "downloads": str(self.base_path / "downloads"),
            "media": str(self.base_path / "media"),
            "config": str(self.base_path / "config")
        }
    
    def _generate_volume_config(self) -> Dict[str, Dict[str, str]]:
        """Generate volume configuration."""
        return {
            name: {"driver": "local"}
            for name in ["downloads", "media", "config"]
        }

class PirateConfigFactory:
    """Factory for creating Pirate mode configurations."""
    
    @staticmethod
    def create_media_server() -> ServiceConfig:
        """Create media server configuration."""
        return ServiceConfig(
            name="media-server",
            description="Media streaming and organization service",
            image="linuxserver/jellyfin:latest",
            ports=["8096:8096"],
            volumes=[
                "{config}:/config",
                "{media}:/media"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC"
            }
        )
    
    @staticmethod
    def create_content_aggregator() -> ServiceConfig:
        """Create content aggregator configuration."""
        return ServiceConfig(
            name="content-aggregator",
            description="Content discovery and organization",
            image="linuxserver/sonarr:latest",
            ports=["8989:8989"],
            volumes=[
                "{config}:/config",
                "{downloads}:/downloads",
                "{media}:/media"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC"
            }
        )
    
    @staticmethod
    def create_download_manager() -> ServiceConfig:
        """Create download manager configuration."""
        return ServiceConfig(
            name="download-manager",
            description="Download automation service",
            image="linuxserver/qbittorrent:latest",
            ports=["8080:8080"],
            volumes=[
                "{config}:/config",
                "{downloads}:/downloads"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC",
                "WEBUI_PORT": "8080"
            }
        )

def get_pirate_config(base_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Generate a complete configuration for Pirate mode.
    
    Args:
        base_path: Optional base path for media storage
        
    Returns:
        Dict containing the complete Pirate mode configuration
    """
    logger.debug("Generating Pirate mode configuration")
    
    if base_path is None:
        base_path = Path.home() / "media"
        logger.debug(f"Using default base path: {base_path}")
    
    # Create service configurations
    factory = PirateConfigFactory()
    services = [
        factory.create_media_server(),
        factory.create_content_aggregator(),
        factory.create_download_manager()
    ]
    
    # Create complete configuration
    config = PirateConfig(
        services=services,
        base_path=base_path
    )
    
    logger.debug("Configuration generated successfully")
    return config.to_dict() 