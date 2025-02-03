"""
Command module for Pirate mode deployment.
"""
import typer
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

from ...config.pirate import get_pirate_config
from ...services.deployment_service import DeploymentService
from ...utils.validation import validate_path
from ...utils.logging import get_logger
from ...wizard.interactive import DeploymentWizard

# Initialize logger and console
logger = get_logger(__name__)
console = Console()

app = typer.Typer()

class PirateDeploymentError(Exception):
    """Custom exception for Pirate mode deployment errors."""
    pass

@app.command()
def deploy(
    media_path: Optional[str] = typer.Option(None, help="Base path for media storage (will be created if it doesn't exist)"),
    timezone: str = typer.Option("Etc/UTC", help="Timezone for the services (e.g. America/New_York)"),
    verbose: bool = typer.Option(False, help="Enable verbose logging"),
    interactive: bool = typer.Option(True, help="Use interactive wizard mode")
) -> None:
    """
    Deploy a preconfigured suite of media automation services.
    
    This command sets up a complete media automation environment with:
    - Plex: Media streaming server
    - Overseerr: Request management and discovery
    - Sonarr: TV show automation
    - Radarr: Movie automation
    - Prowlarr: Indexer management
    - qBittorrent: Download client
    
    All services are configured to work together out of the box.
    """
    try:
        logger.info("Starting Pirate mode deployment")
        if verbose:
            logger.setLevel("DEBUG")
        
        if interactive:
            # Use interactive wizard
            wizard = DeploymentWizard()
            
            # Show welcome message
            wizard.welcome()
            
            # Check prerequisites
            if not wizard.check_prerequisites():
                raise PirateDeploymentError("Prerequisites not met")
            
            # Configure media path
            media_path_obj = wizard.configure_media_path(
                default_path=Path(media_path) if media_path else None
            )
            
            # Configure services
            service_config = wizard.configure_services()
            
            # Show deployment plan
            wizard.show_deployment_plan(service_config)
            
            # Confirm deployment
            if not typer.confirm("Ready to deploy?"):
                logger.info("Deployment cancelled by user")
                raise typer.Exit()
        else:
            # Use command line arguments
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
        raise typer.Exit(1)
    except Exception as e:
        logger.exception("Unexpected error during deployment")
        console.print("[red]An unexpected error occurred during deployment.[/red]")
        console.print(f"[red]Error details:[/red] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(1)

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

def _generate_configuration(media_path: Path, timezone: str) -> dict:
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

def _deploy_services(config: dict) -> None:
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

def _show_success_message(config: dict) -> None:
    """Show deployment success message and next steps."""
    # Create service status table
    services_info = []
    for name, service in config["services"].items():
        ports = service.get("ports", [])
        port_info = [f"http://localhost:{p.split(':')[0]}" for p in ports]
        services_info.append(f"• {name}")
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