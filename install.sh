#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}Installing Easy Docker Deploy...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 first."
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo "pip3 is required but not installed. Please install pip3 first."
    exit 1
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "docker-compose is required but not installed. Please install docker-compose first."
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install the package
echo "Installing dependencies..."
pip install -e .

# Install pytest and pytest-cov
echo "Installing pytest and pytest-cov..."
pip install pytest pytest-cov

# Run tests with coverage report
echo "Running tests with coverage report..."
pytest --cov=src/easy_docker_deploy --cov-report=term-missing

# Create aliases for easier usage
echo "Creating aliases..."
SHELL_RC="$HOME/.bashrc"
if [ -f "$HOME/.zshrc" ]; then
    SHELL_RC="$HOME/.zshrc"
fi

# Add aliases to shell configuration
cat << EOF >> "$SHELL_RC"

# Easy Docker Deploy aliases
alias edd='easy-docker-deploy'
alias edd-list='easy-docker-deploy list'
alias edd-deploy='easy-docker-deploy deploy'
alias edd-search='easy-docker-deploy deploy -s'
EOF

echo -e "${GREEN}Installation complete!${NC}"
echo -e "\nYou can now use the following commands:"
echo -e "${BLUE}edd list${NC} - List available applications"
echo -e "${BLUE}edd deploy <number>${NC} - Deploy application by number"
echo -e "${BLUE}edd-search <term>${NC} - Search and deploy applications"
echo -e "\nPlease restart your terminal or run: source $SHELL_RC"
