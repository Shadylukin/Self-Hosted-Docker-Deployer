# Self-Hosted Docker Deployer

A powerful, user-friendly tool for deploying and managing self-hosted Docker applications, with a special focus on media automation services.

## Features

- 🚀 **Easy Deployment**: Deploy Docker applications with a single command
- 🏴‍☠️ **Pirate Mode**: One-click deployment of media automation services
- 🔄 **Service Integration**: Automatic service discovery and configuration
- 📁 **Volume Management**: Smart handling of persistent storage
- 🌐 **Network Configuration**: Automatic network setup and service discovery
- 🔒 **Security First**: Secure defaults and best practices built-in

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/lukin-ackroydAI/Self-Hosted-Docker-Deployer.git
cd Self-Hosted-Docker-Deployer

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

Deploy a single application:
```bash
easy-docker-deploy deploy app-name
```

List available applications:
```bash
easy-docker-deploy list
```

### Pirate Mode

Deploy a complete media automation suite:
```bash
easy-docker-deploy pirate
```

Customize the deployment:
```bash
easy-docker-deploy pirate --media-path /path/to/media --timezone "America/New_York"
```

## Documentation

- [Pirate Mode Guide](docs/pirate_mode.md)
- [Deployment Guide](docs/Deployment_Assistant_Design_Document.md)

## Development

### Setup Development Environment

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
pytest
```

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config/test_pirate.py

# Run with coverage
pytest --cov=src
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

### Guidelines

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

For security concerns, please open an issue or contact the repository owner directly.

## Acknowledgments

- Built with Python and Docker
- Inspired by the need for simple, secure self-hosting solutions
- Special thanks to the open-source community 