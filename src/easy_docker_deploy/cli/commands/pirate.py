"""
Command module for Pirate mode deployment.
"""
import click
from pathlib import Path
from typing import Optional, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ...config.pirate import get_pirate_config
from ...services.deployment_service import DeploymentService
from ...utils.validation import validate_path
from ...utils.logging import get_logger

# Initialize logger and console
logger = get_logger(__name__)
console = Console()

class PirateDeploymentError(Exception):
    """Custom exception for Pirate mode deployment errors."""
    pass

@click.command()
@click.option(
    "--media-path",
    type=click.Path(exists=False),
    help="Base path for media storage (will be created if it doesn't exist)",
)
@click.option(
    "--timezone",
    default="Etc/UTC",
    help="Timezone for the services (e.g. America/New_York)",
)
@click.option(
    "--verbose",
    is_flag=True,
    help="Enable verbose logging",
)
def pirate(media_path: Optional[str], timezone: str, verbose: bool) -> None:
    """
    Deploy a preconfigured suite of media automation services.
    
    This command sets up a complete media automation environment with:
    - Media streaming server
    - Content aggregation and organization
    - Download automation
    
    All services are configured to work together out of the box.
    """
    try:
        logger.info("Starting Pirate mode deployment")
        if verbose:
            logger.setLevel("DEBUG")
        
        # Validate and create media path
        media_path_obj = _setup_media_path(media_path)
        
        # Generate and validate configuration
        config = _generate_configuration(media_path_obj, timezone)
        
        # Deploy services with progress feedback
        _deploy_services(config)
        
        # Show success message and next steps
        _show_success_message(config)
        
    except PirateDeploymentError as e:
        logger.error(f"Deployment failed: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise click.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error during deployment")
        console.print("[red]An unexpected error occurred during deployment.[/red]")
        console.print(f"[red]Error details:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        raise click.Exit(1)

def _setup_media_path(media_path: Optional[str]) -> Path:
    """Set up and validate the media storage path."""
    try:
        if media_path:
            path = Path(media_path)
        else:
            path = Path.home() / "media"
            logger.info(f"Using default media path: {path}")
        
        # Create directory structure
        for subdir in ["downloads", "media", "config"]:
            subpath = path / subdir
            subpath.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {subpath}")
        
        validate_path(str(path))
        return path
        
    except Exception as e:
        raise PirateDeploymentError(f"Failed to set up media path: {str(e)}")

def _generate_configuration(media_path: Path, timezone: str) -> Dict:
    """Generate and validate the deployment configuration."""
    try:
        logger.info("Generating deployment configuration")
        config = get_pirate_config(media_path)
        
        # Update timezone in all services
        for service in config["services"].values():
            if "environment" in service:
                service["environment"]["TZ"] = timezone
                
        logger.debug("Configuration generated successfully")
        return config
        
    except Exception as e:
        raise PirateDeploymentError(f"Failed to generate configuration: {str(e)}")

def _deploy_services(config: Dict) -> None:
    """Deploy services with progress feedback."""
    try:
        deployment = DeploymentService()
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            # Create overall progress
            deploy_task = progress.add_task("Deploying services...", total=None)
            
            # Deploy each service
            for name, service in config["services"].items():
                progress.update(deploy_task, description=f"Deploying {name}...")
                logger.debug(f"Deploying service: {name}")
                deployment.deploy({"services": {name: service}})
                
            progress.update(deploy_task, description="Deployment complete!")
            
    except Exception as e:
        raise PirateDeploymentError(f"Failed to deploy services: {str(e)}")

def _show_success_message(config: Dict) -> None:
    """Show deployment success message and next steps."""
    # Create service status table
    services_info = []
    for name, service in config["services"].items():
        ports = service.get("ports", [])
        port_info = [f"http://localhost:{p.split(':')[0]}" for p in ports]
        services_info.append(f"• {name}: {service['description']}")
        if port_info:
            services_info.append(f"  URLs: {', '.join(port_info)}")
    
    # Create and show success panel
    panel = Panel(
        "\n".join([
            "[green]Pirate mode deployment complete! 🏴‍☠️[/green]",
            "",
            "[bold]Services deployed:[/bold]",
            *services_info,
            "",
            "[bold]Next steps:[/bold]",
            "1. Access each service using the URLs above",
            "2. Complete the initial setup for each service",
            "3. Configure service integration using the guide",
            "",
            "[bold]For detailed setup instructions and automation guides:[/bold]",
            "docs/pirate_mode.md"
        ]),
        title="Deployment Complete",
        expand=False
    )
    console.print("\n")
    console.print(panel)
    logger.info("Deployment completed successfully") 