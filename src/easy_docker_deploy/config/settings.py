"""
Configuration settings for Easy Docker Deploy.
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

@dataclass
class AppSettings:
    """Application settings."""
    
    # Base directories
    base_dir: Path = field(default_factory=lambda: Path.home() / ".easy-docker-deploy")
    cache_dir: Path = field(init=False)
    log_dir: Path = field(init=False)
    default_volume_base: Path = field(init=False)
    
    # Docker settings
    default_network: str = "easy-docker-deploy"
    default_port_range: Tuple[int, int] = (8000, 9000)
    default_registry: str = "docker.io"
    
    # Cache settings
    cache_ttl: int = 3600  # 1 hour in seconds
    
    # GitHub settings
    github_repo: str = "awesome-selfhosted/awesome-selfhosted"
    github_branch: str = "master"
    github_token: Optional[str] = None
    
    def __post_init__(self):
        """Initialize derived paths."""
        self.cache_dir = self.base_dir / "cache"
        self.log_dir = self.base_dir / "logs"
        self.default_volume_base = self.base_dir / "volumes"
        
        # Create directories if they don't exist
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.default_volume_base.mkdir(parents=True, exist_ok=True)
    
    def to_dict(self) -> Dict:
        """Convert settings to dictionary."""
        return {
            "base_dir": str(self.base_dir),
            "default_network": self.default_network,
            "default_port_range": list(self.default_port_range),
            "default_registry": self.default_registry,
            "cache_ttl": self.cache_ttl,
            "github_repo": self.github_repo,
            "github_branch": self.github_branch,
            "github_token": self.github_token
        }
    
    def save_to_file(self, path: Path) -> None:
        """Save settings to YAML file."""
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)
    
    def load_from_file(self, path: Path) -> None:
        """Load settings from YAML file."""
        if not path.exists():
            return
        
        with open(path) as f:
            data = yaml.safe_load(f)
        
        # Update settings
        if "base_dir" in data:
            self.base_dir = Path(data["base_dir"])
            self.__post_init__()  # Reinitialize derived paths
            
        if "default_network" in data:
            self.default_network = data["default_network"]
            
        if "default_port_range" in data:
            self.default_port_range = tuple(data["default_port_range"])
            
        if "default_registry" in data:
            self.default_registry = data["default_registry"]
            
        if "cache_ttl" in data:
            self.cache_ttl = int(data["cache_ttl"])
            
        if "github_repo" in data:
            self.github_repo = data["github_repo"]
            
        if "github_branch" in data:
            self.github_branch = data["github_branch"]
            
        if "github_token" in data:
            self.github_token = data["github_token"]
    
    @classmethod
    def from_env(cls) -> "AppSettings":
        """Create settings from environment variables."""
        settings = cls()
        
        # Base directory
        if base_dir := os.getenv("EASY_DOCKER_DEPLOY_BASE_DIR"):
            settings.base_dir = Path(base_dir)
            settings.__post_init__()
        
        # Docker settings
        if network := os.getenv("EASY_DOCKER_DEPLOY_NETWORK"):
            settings.default_network = network
            
        if port_range := os.getenv("EASY_DOCKER_DEPLOY_PORT_RANGE"):
            start, end = map(int, port_range.split("-"))
            settings.default_port_range = (start, end)
            
        if registry := os.getenv("EASY_DOCKER_DEPLOY_REGISTRY"):
            settings.default_registry = registry
        
        # Cache settings
        if cache_ttl := os.getenv("EASY_DOCKER_DEPLOY_CACHE_TTL"):
            settings.cache_ttl = int(cache_ttl)
        
        # GitHub settings
        if repo := os.getenv("EASY_DOCKER_DEPLOY_GITHUB_REPO"):
            settings.github_repo = repo
            
        if branch := os.getenv("EASY_DOCKER_DEPLOY_GITHUB_BRANCH"):
            settings.github_branch = branch
            
        if token := os.getenv("EASY_DOCKER_DEPLOY_GITHUB_TOKEN"):
            settings.github_token = token
        
        return settings

# Global settings instance
_settings: Optional[AppSettings] = None

def get_config() -> AppSettings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = AppSettings.from_env()
    return _settings 