"""
Enhanced YAML configuration manager with inline documentation and validation.
"""
import os
import yaml
import jinja2
import subprocess
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from rich.console import Console
from rich.syntax import Syntax
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.layout import Layout
from rich.box import ROUNDED
from rich.text import Text

from .logging import get_logger
from .visualizer import ServiceVisualizer, DeploymentProgress

logger = get_logger(__name__)
console = Console()

class YAMLManager:
    """
    Enhanced YAML configuration manager with inline documentation and validation.
    
    Features:
    - Jinja2 templating for dynamic configuration
    - Inline documentation for each service
    - Docker Compose validation
    - Syntax highlighting for configuration preview
    - Service dependency visualization
    - Animated deployment progress
    """
    
    def __init__(self, config_dir: Path):
        self.config_dir = config_dir
        self.template_dir = Path(__file__).parent.parent / "templates"
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(self.template_dir)),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True
        )
        self.tooltips = self._load_tooltips()
        self.deployment_progress = None
    
    def start_deployment(self, config: dict):
        """
        Start deployment progress tracking.
        
        Args:
            config: Service configuration dictionary
        """
        self.deployment_progress = DeploymentProgress(config.get("services", {}))
        self.deployment_progress.start_deployment()
        return self.deployment_progress
    
    def update_deployment_progress(self, service_name: str, status: str, progress: int):
        """
        Update deployment progress for a service.
        
        Args:
            service_name: Name of the service
            status: Current status message
            progress: Progress percentage (0-100)
        """
        if self.deployment_progress:
            self.deployment_progress.update_service(service_name, status, progress)
    
    def complete_deployment(self):
        """Complete deployment and show summary."""
        if self.deployment_progress:
            self.deployment_progress.complete_deployment()
            self.deployment_progress = None
    
    def _load_tooltips(self) -> dict:
        """Load tooltips and help text for configuration elements."""
        return {
            "general": {
                "version": "Docker Compose file version. Version 3.8 supports all modern Docker features.",
                "services": "Define the containers that make up your application.",
                "networks": "Define how containers communicate with each other.",
                "volumes": "Define persistent storage for your containers."
            },
            "service_options": {
                "image": "The Docker image to use for this container.",
                "container_name": "A custom name for the container (optional).",
                "restart": "Container restart policy (e.g., 'always', 'unless-stopped').",
                "ports": "Map container ports to host ports (format: 'host:container').",
                "environment": "Set environment variables for the container.",
                "volumes": "Mount paths or named volumes into the container.",
                "networks": "Connect the container to specific networks.",
                "depends_on": "Specify service dependencies for startup order."
            },
            "volume_options": {
                "driver": "Storage driver to use (default: 'local').",
                "driver_opts": "Driver-specific options.",
                "external": "Use a pre-existing volume instead of creating one."
            },
            "network_options": {
                "driver": "Network driver to use (default: 'bridge').",
                "internal": "Restrict external access to the network.",
                "attachable": "Allow standalone containers to connect."
            },
            "best_practices": [
                "Always use specific image tags instead of 'latest'",
                "Set restart policies for production services",
                "Use named volumes for persistent data",
                "Define custom networks for service isolation",
                "Set resource limits for production containers"
            ]
        }
    
    def generate_compose_file(self, config: dict, mode: str = "pirate") -> Path:
        """
        Generate a Docker Compose file with inline documentation.
        
        Args:
            config: Configuration dictionary
            mode: Deployment mode (e.g., "pirate")
            
        Returns:
            Path: Path to generated compose file
        """
        try:
            # Show service dependencies before generation
            console.print("\n[bold]Service Dependencies:[/bold]")
            console.print(ServiceVisualizer.create_dependency_graph(config.get("services", {})))
            
            # Load the template
            template = self.env.get_template(f"{mode}_compose.yml.j2")
            
            # Add helpful comments to the configuration
            documented_config = self._add_documentation(config)
            
            # Render the template
            content = template.render(**documented_config)
            
            # Save the configuration
            compose_file = self.config_dir / "docker-compose.yml"
            compose_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(compose_file, "w") as f:
                f.write(content)
            
            # Preview the configuration with enhanced visuals
            self._preview_config(compose_file, config)
            
            return compose_file
            
        except Exception as e:
            logger.error(f"Failed to generate compose file: {str(e)}")
            raise
    
    def validate_compose_file(self, compose_file: Path) -> Tuple[bool, List[str]]:
        """
        Validate a Docker Compose file.
        
        Args:
            compose_file: Path to compose file
            
        Returns:
            Tuple of (is_valid, list of errors)
        """
        try:
            with console.status("[bold yellow]Validating configuration...", spinner="dots"):
                # Run docker-compose config
                result = subprocess.run(
                    ["docker-compose", "-f", str(compose_file), "config"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                console.print("[green]✓[/green] Configuration is valid!")
                return True, []
        except subprocess.CalledProcessError as e:
            # Parse error messages
            errors = []
            for line in e.stderr.split("\n"):
                if line.strip():
                    errors.append(line)
            
            # Show error details
            console.print("[red]✗[/red] Configuration validation failed!")
            for error in errors:
                console.print(f"  [red]•[/red] {error}")
            
            return False, errors
    
    def _add_documentation(self, config: dict) -> dict:
        """Add helpful inline documentation to the configuration."""
        docs = {
            "services": {
                "plex": {
                    "description": "Media server for streaming your content",
                    "ports": "Default web interface port: 32400",
                    "volumes": "Mounts your media and configuration directories",
                    "environment": "Configuration variables including timezone",
                    "learn_more": "https://hub.docker.com/r/linuxserver/plex",
                    "quick_setup": [
                        "1. Access web UI at http://localhost:32400/web",
                        "2. Sign in or create a Plex account",
                        "3. Add your media libraries"
                    ]
                },
                "overseerr": {
                    "description": "Request and discover new content",
                    "ports": "Web interface accessible on port 5055",
                    "volumes": "Persists configuration data",
                    "environment": "Basic configuration including timezone",
                    "learn_more": "https://hub.docker.com/r/linuxserver/overseerr",
                    "quick_setup": [
                        "1. Visit http://localhost:5055",
                        "2. Complete initial setup wizard",
                        "3. Connect to your Plex server"
                    ]
                },
                "sonarr": {
                    "description": "TV show automation and management",
                    "ports": "Web interface accessible on port 8989",
                    "volumes": "Access to media and download directories",
                    "environment": "Configuration including timezone and user IDs",
                    "learn_more": "https://hub.docker.com/r/linuxserver/sonarr",
                    "quick_setup": [
                        "1. Open http://localhost:8989",
                        "2. Add indexers (from Prowlarr)",
                        "3. Configure download client",
                        "4. Add your first show"
                    ]
                },
                "radarr": {
                    "description": "Movie automation and management",
                    "ports": "Web interface accessible on port 7878",
                    "volumes": "Access to media and download directories",
                    "environment": "Configuration including timezone and user IDs",
                    "learn_more": "https://hub.docker.com/r/linuxserver/radarr",
                    "quick_setup": [
                        "1. Open http://localhost:7878",
                        "2. Add indexers (from Prowlarr)",
                        "3. Configure download client",
                        "4. Add your first movie"
                    ]
                },
                "prowlarr": {
                    "description": "Indexer management and proxy",
                    "ports": "Web interface accessible on port 9696",
                    "volumes": "Persists configuration data",
                    "environment": "Basic configuration including timezone",
                    "learn_more": "https://hub.docker.com/r/linuxserver/prowlarr",
                    "quick_setup": [
                        "1. Visit http://localhost:9696",
                        "2. Add your indexers",
                        "3. Configure applications (Sonarr/Radarr)"
                    ]
                },
                "qbittorrent": {
                    "description": "Download client with web interface",
                    "ports": "Web UI on 8080, incoming connections on 6881",
                    "volumes": "Access to download directory",
                    "environment": "Configuration including timezone and user IDs",
                    "learn_more": "https://hub.docker.com/r/linuxserver/qbittorrent",
                    "quick_setup": [
                        "1. Access UI at http://localhost:8080",
                        "2. Login with admin/adminadmin",
                        "3. Change default password",
                        "4. Configure download paths"
                    ]
                }
            },
            "networks": {
                "description": "Internal network for service communication",
                "details": "Allows services to communicate securely",
                "learn_more": "https://docs.docker.com/network/"
            },
            "volumes": {
                "description": "Named volumes for persistent data",
                "details": "Ensures your configuration survives container restarts",
                "learn_more": "https://docs.docker.com/storage/volumes/"
            }
        }
        
        # Add documentation to each service
        for service_name, service_config in config.get("services", {}).items():
            if service_name in docs["services"]:
                service_docs = docs["services"][service_name]
                service_config["_docs"] = service_docs
        
        # Add documentation for networks and volumes
        if "networks" in config:
            config["_network_docs"] = docs["networks"]
        if "volumes" in config:
            config["_volume_docs"] = docs["volumes"]
        
        return config
    
    def _preview_config(self, compose_file: Path, config: dict):
        """Show an enhanced preview of the generated configuration."""
        try:
            # Create layout
            layout = Layout()
            layout.split_column(
                Layout(name="header"),
                Layout(name="main", ratio=3),
                Layout(name="footer")
            )
            
            # Header with title and description
            header_md = """
            # Docker Compose Configuration Preview
            Your configuration has been generated with inline documentation and tooltips.
            Each service is configured to work together out of the box.
            """
            layout["header"].update(Panel(Markdown(header_md)))
            
            # Main content with configuration
            with open(compose_file) as f:
                content = f.read()
            
            syntax = Syntax(
                content,
                "yaml",
                theme="monokai",
                line_numbers=True,
                word_wrap=True
            )
            layout["main"].update(Panel(syntax, title="docker-compose.yml"))
            
            # Footer with quick setup guides
            quick_setup_table = Table(
                title="Quick Setup Guides",
                box=ROUNDED,
                show_header=True,
                header_style="bold magenta"
            )
            quick_setup_table.add_column("Service")
            quick_setup_table.add_column("Steps")
            quick_setup_table.add_column("Learn More")
            
            for service_name, service in config.get("services", {}).items():
                if "_docs" in service and "quick_setup" in service["_docs"]:
                    steps = "\n".join(service["_docs"]["quick_setup"])
                    learn_more = service["_docs"].get("learn_more", "")
                    quick_setup_table.add_row(
                        Text(service_name, style="cyan"),
                        Text(steps),
                        Text(f"[link]{learn_more}[/link]", style="blue underline")
                    )
            
            layout["footer"].update(Panel(quick_setup_table))
            
            # Print the layout
            console.print(layout)
            
            # Show best practices
            console.print("\n[bold]Best Practices:[/bold]")
            for practice in self.tooltips["best_practices"]:
                console.print(f"• {practice}")
            
        except Exception as e:
            logger.error(f"Failed to preview configuration: {str(e)}")
    
    def suggest_fixes(self, errors: List[str]) -> List[str]:
        """
        Suggest fixes for common configuration errors.
        
        Args:
            errors: List of error messages
            
        Returns:
            List of suggested fixes
        """
        suggestions = []
        
        for error in errors:
            if "port is already allocated" in error.lower():
                suggestions.append(
                    "• A port is already in use. Try:\n"
                    "  1. Stop any running services using these ports\n"
                    "  2. Modify the port mappings in the configuration\n"
                    "  3. Use 'docker ps' to see what's using the ports"
                )
            elif "volume" in error.lower() and "permission denied" in error.lower():
                suggestions.append(
                    "• Volume permission issue. Try:\n"
                    "  1. Check the ownership of your media directories\n"
                    "  2. Ensure the paths exist and are accessible\n"
                    "  3. Run 'chown -R $USER:$USER' on the directories"
                )
            elif "network" in error.lower():
                suggestions.append(
                    "• Network configuration issue. Try:\n"
                    "  1. Remove any existing networks with 'docker network prune'\n"
                    "  2. Ensure Docker has network creation permissions\n"
                    "  3. Check if the network name is already in use"
                )
        
        if not suggestions:
            suggestions.append(
                "• For detailed troubleshooting:\n"
                "  1. Check our documentation at https://github.com/yourusername/easy-docker-deploy\n"
                "  2. Visit the Docker Compose documentation\n"
                "  3. Join our community support channels"
            )
        
        return suggestions 