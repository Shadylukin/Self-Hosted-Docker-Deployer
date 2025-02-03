"""
Configuration module for Pirate mode services and settings.
This module provides preset configurations for media automation services.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from pathlib import Path

from ..utils.logging import get_logger
from ..config.settings import get_config

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
    comments: Optional[Dict[str, str]] = None

@dataclass
class PirateConfig:
    """Complete configuration for Pirate mode."""
    services: List[ServiceConfig]
    base_path: Path
    network_name: str = get_config().default_network
    compose_version: str = "3.8"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to Docker Compose format."""
        return {
            "version": self.compose_version,
            "services": {
                service.name: self._format_service_config(service)
                for service in self.services
            },
            "networks": {
                self.network_name: {
                    "driver": "bridge",
                    "external": True
                }
            },
            "volumes": self._generate_volume_config()
        }
    
    def _format_service_config(self, service: ServiceConfig) -> Dict[str, Any]:
        """Format a service configuration with proper paths."""
        paths = self._get_path_mappings()
        
        # Format volumes with proper paths
        volumes = []
        for volume in service.volumes:
            for key, path in paths.items():
                volume = volume.replace(f"{{{key}}}", path)
            volumes.append(volume)
        
        config = {
            "image": service.image,
            "ports": service.ports,
            "volumes": volumes,
            "environment": service.environment,
            "networks": [self.network_name],
            "restart": "unless-stopped"
        }
        
        return config
    
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
    def create_plex() -> ServiceConfig:
        """Create Plex media server configuration."""
        return ServiceConfig(
            name="plex",
            description="Media streaming and organization server",
            image="linuxserver/plex:latest",
            ports=["32400:32400"],
            volumes=[
                "{config}:/config",
                "{media}:/media"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC",
                "VERSION": "docker"
            },
            comments={
                "description": "Plex Media Server - Stream your media collection",
                "ports": "Port 32400 is used for the web interface and streaming",
                "volumes": "Config stores Plex settings, Media contains your media files",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )
    
    @staticmethod
    def create_overseerr() -> ServiceConfig:
        """Create Overseerr configuration."""
        return ServiceConfig(
            name="overseerr",
            description="Media request and discovery",
            image="linuxserver/overseerr:latest",
            ports=["5055:5055"],
            volumes=[
                "{config}:/config"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC"
            },
            comments={
                "description": "Overseerr - Request and discover new media",
                "ports": "Port 5055 is used for the web interface",
                "volumes": "Config stores Overseerr settings and database",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )
    
    @staticmethod
    def create_sonarr() -> ServiceConfig:
        """Create Sonarr configuration."""
        return ServiceConfig(
            name="sonarr",
            description="TV series management",
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
            },
            comments={
                "description": "Sonarr - Automated TV series management",
                "ports": "Port 8989 is used for the web interface",
                "volumes": "Config stores settings, Downloads for temporary files, Media for TV shows",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )
    
    @staticmethod
    def create_radarr() -> ServiceConfig:
        """Create Radarr configuration."""
        return ServiceConfig(
            name="radarr",
            description="Movie collection management",
            image="linuxserver/radarr:latest",
            ports=["7878:7878"],
            volumes=[
                "{config}:/config",
                "{downloads}:/downloads",
                "{media}:/media"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC"
            },
            comments={
                "description": "Radarr - Automated movie management",
                "ports": "Port 7878 is used for the web interface",
                "volumes": "Config stores settings, Downloads for temporary files, Media for movies",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )
    
    @staticmethod
    def create_prowlarr() -> ServiceConfig:
        """Create Prowlarr configuration."""
        return ServiceConfig(
            name="prowlarr",
            description="Indexer management",
            image="linuxserver/prowlarr:latest",
            ports=["9696:9696"],
            volumes=[
                "{config}:/config"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC"
            },
            comments={
                "description": "Prowlarr - Indexer management and proxy",
                "ports": "Port 9696 is used for the web interface",
                "volumes": "Config stores settings and indexer data",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )
    
    @staticmethod
    def create_qbittorrent() -> ServiceConfig:
        """Create qBittorrent configuration."""
        return ServiceConfig(
            name="qbittorrent",
            description="Download client",
            image="linuxserver/qbittorrent:latest",
            ports=["8080:8080", "6881:6881", "6881:6881/udp"],
            volumes=[
                "{config}:/config",
                "{downloads}:/downloads"
            ],
            environment={
                "PUID": "1000",
                "PGID": "1000",
                "TZ": "Etc/UTC",
                "WEBUI_PORT": "8080"
            },
            comments={
                "description": "qBittorrent - Download client with web interface",
                "ports": "Port 8080 for web UI, 6881 for torrent communication",
                "volumes": "Config stores settings, Downloads for downloaded files",
                "environment": "PUID/PGID ensure proper file permissions"
            }
        )

def get_pirate_config(media_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get the complete Pirate mode configuration.
    
    Args:
        media_path: Optional path for media storage
        
    Returns:
        Dictionary containing the complete configuration
    """
    if media_path is None:
        media_path = Path.home() / "media"
    
    factory = PirateConfigFactory()
    config = PirateConfig(
        services=[
            factory.create_plex(),
            factory.create_overseerr(),
            factory.create_sonarr(),
            factory.create_radarr(),
            factory.create_prowlarr(),
            factory.create_qbittorrent()
        ],
        base_path=media_path
    )
    
    return config.to_dict() 