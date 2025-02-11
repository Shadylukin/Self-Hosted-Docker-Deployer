#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to detect Linux distribution
detect_distro() {
    if [ -f /etc/os-release ]; then
        . /etc/os-release
        OS=$NAME
        VER=$VERSION_ID
    elif type lsb_release >/dev/null 2>&1; then
        OS=$(lsb_release -si)
        VER=$(lsb_release -sr)
    else
        OS=$(uname -s)
        VER=$(uname -r)
    fi
}

# Function to check system requirements
check_requirements() {
    echo -e "\n${BLUE}Checking system requirements for Docker...${NC}"
    
    # Check if running as root
    if [ "$EUID" -ne 0 ]; then
        echo -e "${RED}Please run as root or with sudo${NC}"
        return 1
    fi
    
    # Check architecture
    ARCH=$(uname -m)
    echo -n "Architecture: "
    echo -e "${BLUE}$ARCH${NC}"
    if [[ ! "$ARCH" =~ ^(x86_64|amd64|arm64|aarch64)$ ]]; then
        echo -e "${RED}[ERROR] Unsupported architecture${NC}"
        return 1
    fi
    
    # Check kernel version
    KERNEL=$(uname -r)
    echo -n "Kernel version: "
    echo -e "${BLUE}$KERNEL${NC}"
    if ! [[ $(uname -r) =~ ^([0-9]+)\.([0-9]+) ]]; then
        echo -e "${RED}[ERROR] Could not determine kernel version${NC}"
        return 1
    fi
    
    # Check memory
    MEMORY=$(grep MemTotal /proc/meminfo | awk '{print $2/1024/1024}')
    echo -n "Available RAM: "
    echo -e "${BLUE}${MEMORY%.*} GB${NC}"
    if (( $(echo "$MEMORY < 2" | bc -l) )); then
        echo -e "${RED}[ERROR] At least 2GB of RAM required${NC}"
        return 1
    fi
    
    return 0
}

# Function to install Docker on Ubuntu/Debian
install_docker_ubuntu() {
    echo -e "\n${BLUE}Installing Docker on Ubuntu/Debian...${NC}"
    
    # Remove old versions
    echo "Removing old versions..."
    apt-get remove docker docker-engine docker.io containerd runc >/dev/null 2>&1
    
    # Install prerequisites
    echo "Installing prerequisites..."
    apt-get update
    apt-get install -y \
        apt-transport-https \
        ca-certificates \
        curl \
        gnupg \
        lsb-release
    
    # Add Docker's official GPG key
    echo "Adding Docker's GPG key..."
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # Set up repository
    echo "Setting up Docker repository..."
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    echo "Installing Docker Engine..."
    apt-get update
    apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    echo "Starting Docker service..."
    systemctl start docker
    systemctl enable docker
    
    # Add user to docker group
    echo "Adding current user to docker group..."
    usermod -aG docker $SUDO_USER
    
    echo -e "${GREEN}Docker installation completed!${NC}"
}

# Function to install Docker on CentOS/RHEL
install_docker_centos() {
    echo -e "\n${BLUE}Installing Docker on CentOS/RHEL...${NC}"
    
    # Remove old versions
    echo "Removing old versions..."
    yum remove docker docker-common docker-selinux docker-engine >/dev/null 2>&1
    
    # Install prerequisites
    echo "Installing prerequisites..."
    yum install -y yum-utils device-mapper-persistent-data lvm2
    
    # Add Docker repository
    echo "Adding Docker repository..."
    yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo
    
    # Install Docker Engine
    echo "Installing Docker Engine..."
    yum install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    
    # Start and enable Docker
    echo "Starting Docker service..."
    systemctl start docker
    systemctl enable docker
    
    # Add user to docker group
    echo "Adding current user to docker group..."
    usermod -aG docker $SUDO_USER
    
    echo -e "${GREEN}Docker installation completed!${NC}"
}

# Main installation process
echo -e "${BLUE}Docker Installation Helper${NC}"
echo "=============================="

# Check if Docker is already installed
if command -v docker >/dev/null 2>&1; then
    echo -e "${GREEN}Docker is already installed!${NC}"
    docker --version
    exit 0
fi

# Check system requirements
check_requirements
if [ $? -ne 0 ]; then
    echo -e "${RED}System requirements not met. Please check the requirements at:${NC}"
    echo "https://docs.docker.com/engine/install/"
    exit 1
fi

# Detect distribution and install Docker
detect_distro
echo -e "\nDetected system: ${BLUE}$OS $VER${NC}"

case "$OS" in
    *"Ubuntu"*|*"Debian"*)
        install_docker_ubuntu
        ;;
    *"CentOS"*|*"Red Hat"*|*"Fedora"*)
        install_docker_centos
        ;;
    *)
        echo -e "${RED}Unsupported distribution: $OS${NC}"
        echo "Please install Docker manually following the instructions at:"
        echo "https://docs.docker.com/engine/install/"
        exit 1
        ;;
esac

# Install pytest and pytest-cov
echo -e "\n${BLUE}Installing pytest and pytest-cov...${NC}"
pip install pytest pytest-cov

# Run tests with coverage report
echo -e "\n${BLUE}Running tests with coverage report...${NC}"
pytest --cov=src/easy_docker_deploy --cov-report=term-missing

# Final instructions
echo -e "\n${GREEN}Installation completed successfully!${NC}"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Log out and log back in for group changes to take effect"
echo "2. Verify installation with: docker run hello-world"
echo "3. Run the Easy Docker Deploy installer"

# Ask to proceed with Easy Docker Deploy installation
echo -e "\n${BLUE}Would you like to proceed with Easy Docker Deploy installation? (y/n)${NC}"
read -r proceed
if [[ $proceed =~ ^[Yy]$ ]]; then
    exec ./install.sh
fi
