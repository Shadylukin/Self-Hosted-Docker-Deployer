"""
Module for managing unified YAML configuration files.
"""
import os
import subprocess
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import yaml

from ..utils.logging import get_logger
from ..utils.exceptions import ConfigurationError
from ..config.settings import get_config

logger = get_logger(__name__)

class YAMLManager:
    """Manager for unified YAML configuration files."""
    
    def __init__(self, base_dir: Path):
        """
        Initialize the YAML manager.
        
        Args:
            base_dir: Base directory for configuration files
        """
        self.base_dir = base_dir
        self.compose_file = base_dir / "docker-compose.yml"
        self.comments_file = base_dir / "docker-compose.comments.yml"
        self.config = get_config()
        
    def load_config(self) -> Dict[str, Any]:
        """
        Load existing configuration from YAML file.
        
        Returns:
            Dictionary containing the configuration
        """
        try:
            if not self.compose_file.exists():
                return {
                    "services": {},
                    "networks": {
                        self.config.default_network: {
                            "external": True
                        }
                    },
                    "volumes": {}
                }
            
            with open(self.compose_file) as f:
                return yaml.safe_load(f) or {}
                
        except Exception as e:
            logger.error(f"Failed to load configuration: {str(e)}")
            raise ConfigurationError(f"Failed to load configuration: {str(e)}")
    
    def load_comments(self) -> Dict[str, Any]:
        """
        Load comments from comments file.
        
        Returns:
            Dictionary containing comments
        """
        try:
            if not self.comments_file.exists():
                return {
                    "services": {},
                    "networks": {
                        self.config.default_network: "External network for service communication"
                    },
                    "volumes": "Persistent storage configuration",
                    "global": "Docker Compose configuration for Self-Hosted Docker Deployer"
                }
            
            with open(self.comments_file) as f:
                return yaml.safe_load(f) or {}
                
        except Exception as e:
            logger.error(f"Failed to load comments: {str(e)}")
            return {}  # Return empty comments if loading fails
    
    def save_config(self, config: Dict[str, Any], comments: Optional[Dict[str, Any]] = None) -> None:
        """
        Save configuration to YAML file.
        
        Args:
            config: Configuration dictionary to save
            comments: Optional comments dictionary to save
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(self.base_dir, exist_ok=True)
            
            # Save configuration
            with open(self.compose_file, 'w') as f:
                yaml.dump(
                    config,
                    f,
                    default_flow_style=False,
                    sort_keys=False,
                    width=120,
                    allow_unicode=True
                )
            
            # Save comments if provided
            if comments:
                with open(self.comments_file, 'w') as f:
                    yaml.dump(
                        comments,
                        f,
                        default_flow_style=False,
                        sort_keys=False,
                        width=120,
                        allow_unicode=True
                    )
                
            logger.debug(f"Configuration saved to {self.compose_file}")
            
        except Exception as e:
            logger.error(f"Failed to save configuration: {str(e)}")
            raise ConfigurationError(f"Failed to save configuration: {str(e)}")
    
    def validate_config(self, config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate Docker Compose configuration.
        
        Args:
            config: Optional configuration to validate. If not provided,
                   the current configuration file will be validated.
                   
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If validation fails
        """
        try:
            if config is not None:
                # Save temporary file for validation
                temp_file = self.base_dir / "docker-compose.validate.yml"
                with open(temp_file, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                file_to_validate = temp_file
            else:
                file_to_validate = self.compose_file
            
            # Validate using docker-compose config
            result = subprocess.run(
                ["docker-compose", "-f", str(file_to_validate), "config", "--quiet"],
                capture_output=True,
                text=True
            )
            
            if config is not None:
                # Clean up temporary file
                temp_file.unlink()
            
            if result.returncode != 0:
                raise ConfigurationError(
                    f"Invalid Docker Compose configuration: {result.stderr}"
                )
            
            return True
            
        except FileNotFoundError:
            raise ConfigurationError("docker-compose command not found. Please install docker-compose.")
        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            logger.error(f"Configuration validation failed: {str(e)}")
            raise ConfigurationError(f"Configuration validation failed: {str(e)}")
    
    def merge_config(self, new_config: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Merge new configuration with existing configuration.
        
        Args:
            new_config: New configuration to merge
            
        Returns:
            Tuple of (merged configuration dictionary, merged comments dictionary)
        """
        try:
            # Load existing configuration and comments
            current_config = self.load_config()
            current_comments = self.load_comments()
            
            # Extract comments from new config
            new_comments = {}
            clean_config = {}
            
            for key, value in new_config.items():
                if key == "_comments":
                    new_comments.update(value)
                else:
                    if isinstance(value, dict):
                        service_comments = value.pop("_comments", {})
                        if service_comments:
                            new_comments[key] = service_comments
                    clean_config[key] = value
            
            # Merge services
            if "services" in clean_config:
                if "services" not in current_config:
                    current_config["services"] = {}
                current_config["services"].update(clean_config["services"])
            
            # Merge networks
            if "networks" in clean_config:
                if "networks" not in current_config:
                    current_config["networks"] = {}
                current_config["networks"].update(clean_config["networks"])
            
            # Merge volumes
            if "volumes" in clean_config:
                if "volumes" not in current_config:
                    current_config["volumes"] = {}
                current_config["volumes"].update(clean_config["volumes"])
            
            # Merge comments
            for key, value in new_comments.items():
                if key not in current_comments:
                    current_comments[key] = {}
                if isinstance(value, dict):
                    current_comments[key].update(value)
                else:
                    current_comments[key] = value
            
            return current_config, current_comments
            
        except Exception as e:
            logger.error(f"Failed to merge configurations: {str(e)}")
            raise ConfigurationError(f"Failed to merge configurations: {str(e)}")
    
    def update_config(self, new_config: Dict[str, Any], validate: bool = True) -> None:
        """
        Update configuration with new settings.
        
        Args:
            new_config: New configuration to apply
            validate: Whether to validate the configuration before saving
        """
        try:
            # Merge configurations and comments
            merged_config, merged_comments = self.merge_config(new_config)
            
            # Ensure network configuration is present
            if "networks" not in merged_config:
                merged_config["networks"] = {}
            if self.config.default_network not in merged_config["networks"]:
                merged_config["networks"][self.config.default_network] = {
                    "external": True
                }
            
            # Update service network configuration
            for service in merged_config.get("services", {}).values():
                if "networks" not in service:
                    service["networks"] = [self.config.default_network]
                elif self.config.default_network not in service["networks"]:
                    service["networks"].append(self.config.default_network)
            
            # Validate if requested
            if validate:
                self.validate_config(merged_config)
            
            # Save merged configuration and comments
            self.save_config(merged_config, merged_comments)
            
            logger.info("Configuration updated successfully")
            
        except Exception as e:
            logger.error(f"Failed to update configuration: {str(e)}")
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(f"Failed to update configuration: {str(e)}")
            
    def remove_services(self, service_names: list[str]) -> None:
        """
        Remove services from the configuration.
        
        Args:
            service_names: List of service names to remove
        """
        try:
            # Load current configuration and comments
            config = self.load_config()
            comments = self.load_comments()
            
            # Remove services
            for name in service_names:
                if name in config.get("services", {}):
                    del config["services"][name]
                    if "services" in comments and name in comments["services"]:
                        del comments["services"][name]
                    logger.debug(f"Removed service: {name}")
            
            # Save updated configuration and comments
            self.save_config(config, comments)
            
            logger.info(f"Removed services: {', '.join(service_names)}")
            
        except Exception as e:
            logger.error(f"Failed to remove services: {str(e)}")
            raise ConfigurationError(f"Failed to remove services: {str(e)}")
            
    def get_service_names(self) -> list[str]:
        """
        Get list of configured service names.
        
        Returns:
            List of service names
        """
        try:
            config = self.load_config()
            return list(config.get("services", {}).keys())
            
        except Exception as e:
            logger.error(f"Failed to get service names: {str(e)}")
            raise ConfigurationError(f"Failed to get service names: {str(e)}") 
