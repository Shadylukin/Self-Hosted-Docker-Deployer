"""
Docker utility functions for Easy Docker Deploy.
"""
import subprocess
from typing import Optional, Tuple
import platform
import os
from pathlib import Path

from .logging import get_logger

logger = get_logger(__name__)

def check_docker_installation() -> bool:
    """
    Check if Docker is installed and running.
    
    Returns:
        bool: True if Docker is installed and running
    """
    try:
        # Check Docker CLI
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error("Docker CLI not found")
            return False
            
        # Check Docker daemon
        result = subprocess.run(
            ["docker", "info"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error("Docker daemon not running")
            return False
            
        # Check Docker Compose
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            logger.error("Docker Compose not found")
            return False
            
        return True
        
    except Exception as e:
        logger.error(f"Error checking Docker installation: {str(e)}")
        return False

def get_docker_info() -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Get Docker version and status information.
    
    Returns:
        Tuple of (is_installed: bool, version: Optional[str], compose_version: Optional[str])
    """
    try:
        # Get Docker version
        result = subprocess.run(
            ["docker", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return False, None, None
            
        docker_version = result.stdout.strip()
        
        # Get Docker Compose version
        result = subprocess.run(
            ["docker-compose", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            return True, docker_version, None
            
        compose_version = result.stdout.strip()
        return True, docker_version, compose_version
        
    except Exception as e:
        logger.error(f"Error getting Docker info: {str(e)}")
        return False, None, None

def get_installation_instructions() -> str:
    """
    Get platform-specific Docker installation instructions.
    
    Returns:
        str: Installation instructions
    """
    system = platform.system().lower()
    
    if system == "windows":
        return """
        To install Docker on Windows:
        
        1. Download Docker Desktop for Windows:
           https://docs.docker.com/desktop/install/windows-install/
           
        2. Run the installer and follow the prompts
        
        3. Start Docker Desktop after installation
        
        4. Open PowerShell and run:
           docker --version
           
        To verify the installation
        """
    elif system == "darwin":
        return """
        To install Docker on macOS:
        
        1. Download Docker Desktop for Mac:
           https://docs.docker.com/desktop/install/mac-install/
           
        2. Drag Docker to your Applications folder
        
        3. Start Docker Desktop
        
        4. Open Terminal and run:
           docker --version
           
        To verify the installation
        """
    else:
        return """
        To install Docker on Linux:
        
        1. Update your package list:
           sudo apt-get update
           
        2. Install prerequisites:
           sudo apt-get install ca-certificates curl gnupg
           
        3. Add Docker's official GPG key:
           sudo install -m 0755 -d /etc/apt/keyrings
           curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
           sudo chmod a+r /etc/apt/keyrings/docker.gpg
           
        4. Add the repository:
           echo "deb [arch="$(dpkg --print-architecture)" signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu "$(. /etc/os-release && echo "$VERSION_CODENAME")" stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
           
        5. Update and install Docker:
           sudo apt-get update
           sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
           
        6. Start Docker:
           sudo systemctl start docker
           sudo systemctl enable docker
           
        7. Add your user to the docker group:
           sudo usermod -aG docker $USER
           
        8. Log out and back in, then verify:
           docker --version
        """

def check_disk_space(path: Path, min_space_gb: int = 50) -> Tuple[bool, str]:
    """
    Check if there's enough disk space available.
    
    Args:
        path: Path to check
        min_space_gb: Minimum required space in GB
        
    Returns:
        Tuple of (has_space: bool, message: str)
    """
    try:
        import shutil
        _, _, free = shutil.disk_usage(path)
        free_gb = free / (1024 * 1024 * 1024)
        
        if free_gb < min_space_gb:
            return False, f"Only {free_gb:.1f}GB available. Minimum {min_space_gb}GB recommended."
            
        return True, f"{free_gb:.1f}GB available"
        
    except Exception as e:
        logger.error(f"Error checking disk space: {str(e)}")
        return False, "Unable to check disk space" 