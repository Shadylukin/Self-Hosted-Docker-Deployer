# Easy Docker Deploy

[![CI](https://github.com/yourusername/easy-docker-deploy/actions/workflows/ci.yml/badge.svg)](https://github.com/yourusername/easy-docker-deploy/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/yourusername/easy-docker-deploy/branch/main/graph/badge.svg)](https://codecov.io/gh/yourusername/easy-docker-deploy)
[![License](https://img.shields.io/github/license/yourusername/easy-docker-deploy)](https://github.com/yourusername/easy-docker-deploy/blob/main/LICENSE)

A command-line tool to easily deploy self-hosted applications using Docker.

## Features

- 🚀 Easy deployment of popular self-hosted applications
- 🐳 Automatic Docker configuration generation
- 🔄 Smart port and volume management
- 📝 Structured logging with rotation
- 💾 Efficient caching of application data
- 🔒 Secure environment variable handling
- 🎯 Validation of all configurations
- 🔍 Rich CLI interface with detailed feedback

## Installation

### Using pip

```bash
pip install easy-docker-deploy
```

### From source

```bash
git clone https://github.com/yourusername/easy-docker-deploy.git
cd easy-docker-deploy
pip install -e .
```

### Requirements

- Python 3.8 or higher
- Docker and Docker Compose
- Git (for development)

## Usage

### Basic Commands

```bash
# Deploy an application
easy-docker-deploy deploy nextcloud

# Check application status
easy-docker-deploy status nextcloud

# View application logs
easy-docker-deploy logs nextcloud

# Stop an application
easy-docker-deploy stop nextcloud
```

### Advanced Options

```bash
# Deploy with custom port
easy-docker-deploy deploy wordpress --port 8080

# Deploy with custom volume
easy-docker-deploy deploy gitea --volume /data/gitea:/data

# Deploy with custom environment file
easy-docker-deploy deploy postgres --env-file .env

# Deploy on custom network
easy-docker-deploy deploy nginx --network web-proxy
```

### Configuration

The tool can be configured using:

1. Environment variables:
   ```bash
   export EASY_DOCKER_DEPLOY_BASE_DIR=/opt/docker
   export EASY_DOCKER_DEPLOY_PORT_RANGE=8000-9000
   export EASY_DOCKER_DEPLOY_NETWORK=custom-network
   ```

2. Configuration file:
   ```yaml
   # ~/.easy-docker-deploy/config.yml
   base_dir: /opt/docker
   default_port_range: [8000, 9000]
   default_network: custom-network
   cache_ttl: 3600
   ```

3. Command-line options:
   ```bash
   easy-docker-deploy --config config.yml deploy nextcloud
   ```

## Logging

The tool provides structured logging with the following features:

- JSON-formatted logs for easy parsing
- Log rotation with configurable size and backup count
- Different log levels (DEBUG, INFO, WARNING, ERROR)
- Context-aware logging with extra fields
- Console output using Rich for better readability

Configure logging using:

```bash
# Set log level
easy-docker-deploy --log-level DEBUG deploy nextcloud

# Specify log file
easy-docker-deploy --log-file /var/log/easy-docker-deploy.log deploy nextcloud
```

## Development

### Setting up development environment

```bash
# Clone repository
git clone https://github.com/yourusername/easy-docker-deploy.git
cd easy-docker-deploy

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install development dependencies
pip install -e ".[dev]"
```

### Running tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/easy_docker_deploy

# Run specific test file
pytest tests/test_utils/test_validation.py
```

### Code quality

```bash
# Check code formatting
ruff check .

# Type checking
mypy src tests
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [awesome-selfhosted](https://github.com/awesome-selfhosted/awesome-selfhosted) for the application list
- [Typer](https://typer.tiangolo.com/) for the CLI framework
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output 