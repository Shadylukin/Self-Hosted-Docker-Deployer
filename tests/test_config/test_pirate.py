"""
Tests for Pirate mode configuration.
"""
import pytest
from pathlib import Path
from typing import Dict, Any

from easy_docker_deploy.config.pirate import (
    ServiceConfig,
    PirateConfig,
    PirateConfigFactory,
    get_pirate_config
)

@pytest.fixture
def base_path(tmp_path: Path) -> Path:
    """Create a temporary base path for testing."""
    media_path = tmp_path / "media"
    media_path.mkdir()
    return media_path

@pytest.fixture
def service_config() -> ServiceConfig:
    """Create a sample service configuration for testing."""
    return ServiceConfig(
        name="test-service",
        description="Test service",
        image="test/image:latest",
        ports=["8080:8080"],
        volumes=["{config}:/config"],
        environment={"TEST": "value"}
    )

@pytest.fixture
def pirate_config(base_path: Path, service_config: ServiceConfig) -> PirateConfig:
    """Create a sample Pirate configuration for testing."""
    return PirateConfig(
        services=[service_config],
        base_path=base_path
    )

class TestServiceConfig:
    """Tests for ServiceConfig class."""
    
    def test_service_config_creation(self, service_config: ServiceConfig) -> None:
        """Test creating a service configuration."""
        assert service_config.name == "test-service"
        assert service_config.description == "Test service"
        assert service_config.image == "test/image:latest"
        assert service_config.ports == ["8080:8080"]
        assert service_config.volumes == ["{config}:/config"]
        assert service_config.environment == {"TEST": "value"}

class TestPirateConfig:
    """Tests for PirateConfig class."""
    
    def test_to_dict_basic(self, pirate_config: PirateConfig) -> None:
        """Test basic dictionary conversion."""
        result = pirate_config.to_dict()
        
        assert result["version"] == "3.8"
        assert "services" in result
        assert "volumes" in result
        assert "networks" in result
    
    def test_service_formatting(self, pirate_config: PirateConfig) -> None:
        """Test service configuration formatting."""
        result = pirate_config.to_dict()
        service = result["services"]["test-service"]
        
        assert service["image"] == "test/image:latest"
        assert service["ports"] == ["8080:8080"]
        assert "volumes" in service
        assert service["environment"] == {"TEST": "value"}
        assert service["networks"] == ["pirate_network"]
        assert service["restart"] == "unless-stopped"
    
    def test_volume_paths(self, pirate_config: PirateConfig, base_path: Path) -> None:
        """Test volume path formatting."""
        result = pirate_config.to_dict()
        service = result["services"]["test-service"]
        
        expected_config_path = str(base_path / "config")
        assert service["volumes"] == [f"{expected_config_path}:/config"]
    
    def test_network_configuration(self, pirate_config: PirateConfig) -> None:
        """Test network configuration."""
        result = pirate_config.to_dict()
        
        assert "pirate_network" in result["networks"]
        assert result["networks"]["pirate_network"]["driver"] == "bridge"

class TestPirateConfigFactory:
    """Tests for PirateConfigFactory class."""
    
    def test_create_media_server(self) -> None:
        """Test media server configuration creation."""
        factory = PirateConfigFactory()
        config = factory.create_media_server()
        
        assert config.name == "media-server"
        assert "jellyfin" in config.image.lower()
        assert "8096:8096" in config.ports
        assert any("/media" in vol for vol in config.volumes)
    
    def test_create_content_aggregator(self) -> None:
        """Test content aggregator configuration creation."""
        factory = PirateConfigFactory()
        config = factory.create_content_aggregator()
        
        assert config.name == "content-aggregator"
        assert "sonarr" in config.image.lower()
        assert "8989:8989" in config.ports
        assert any("/media" in vol for vol in config.volumes)
        assert any("/downloads" in vol for vol in config.volumes)
    
    def test_create_download_manager(self) -> None:
        """Test download manager configuration creation."""
        factory = PirateConfigFactory()
        config = factory.create_download_manager()
        
        assert config.name == "download-manager"
        assert "qbittorrent" in config.image.lower()
        assert "8080:8080" in config.ports
        assert any("/downloads" in vol for vol in config.volumes)

def test_get_pirate_config_default_path() -> None:
    """Test getting Pirate configuration with default path."""
    config = get_pirate_config()
    assert isinstance(config, Dict)
    assert "services" in config
    assert len(config["services"]) == 3

def test_get_pirate_config_custom_path(base_path: Path) -> None:
    """Test getting Pirate configuration with custom path."""
    config = get_pirate_config(base_path)
    
    # Check services
    assert len(config["services"]) == 3
    assert "media-server" in config["services"]
    assert "content-aggregator" in config["services"]
    assert "download-manager" in config["services"]
    
    # Check paths
    for service in config["services"].values():
        for volume in service["volumes"]:
            if "/config" in volume:
                assert str(base_path / "config") in volume
            elif "/media" in volume:
                assert str(base_path / "media") in volume
            elif "/downloads" in volume:
                assert str(base_path / "downloads") in volume 