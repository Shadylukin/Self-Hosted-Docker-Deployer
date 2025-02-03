"""
Commands for deploying applications.
"""
from pathlib import Path
from typing import Dict, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from ...config.settings import get_config
from ...docker.manager import get_docker_manager
from ...parser.github_parser import Application
from ...services.deployment_service import get_deployment_service
from ...utils.logging import get_logger

logger = get_logger(__name__)
console = Console()

app = typer.Typer(help="Deploy Docker applications")

@app.command()
def deploy(
    name: str = typer.Argument(..., help="Name of the application to deploy"),
    port: Optional[int] = typer.Option(None, help="Override the default port mapping"),
    volume: Optional[str] = typer.Option(None, help="Override the default volume mapping"),
    env_file: Optional[Path] = typer.Option(None, help="Path to environment file"),
    network: Optional[str] = typer.Option(None, help="Docker network to use"),
    pull: bool = typer.Option(True, help="Pull latest image before deploying"),
) -> None:
    """
    Deploy a Docker application.
    """
    try:
        # Get services
        deployment_service = get_deployment_service()
        docker_manager = get_docker_manager()
        
        # Find application
        app = deployment_service.find_application(name)
        if not app:
            logger.error(f"Application '{name}' not found")
            raise typer.Exit(1)
        
        # Show deployment plan
        _show_deployment_plan(app, port, volume, network)
        
        if not typer.confirm("Do you want to proceed with the deployment?"):
            logger.info("Deployment cancelled by user")
            raise typer.Exit()
        
        # Create deployment
        deploy_dir = deployment_service.deploy_application(
            app,
            port_override=port,
            volume_override=volume,
            network_override=network
        )
        
        # Pull image if requested
        if pull:
            docker_manager.pull_image(app.docker_url)
        
        # Ensure network exists
        if network:
            docker_manager.ensure_network_exists(network)
        
        # Start container
        docker_manager.start_container(deploy_dir)
        
        # Show success message
        _show_success_message(app, deploy_dir)
        
    except Exception as e:
        logger.error(f"Deployment failed: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def stop(
    name: str = typer.Argument(..., help="Name of the application to stop"),
) -> None:
    """
    Stop a deployed application.
    """
    try:
        # Get services
        deployment_service = get_deployment_service()
        docker_manager = get_docker_manager()
        
        # Get deployment directory
        deploy_dir = deployment_service.get_deployment_directory(name)
        if not deploy_dir.exists():
            logger.error(f"Application '{name}' is not deployed")
            raise typer.Exit(1)
        
        # Stop container
        docker_manager.stop_container(deploy_dir)
        
        console.print(f"[green]Successfully stopped {name}[/green]")
        
    except Exception as e:
        logger.error(f"Failed to stop application: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def status(
    name: Optional[str] = typer.Argument(None, help="Name of the application to check"),
) -> None:
    """
    Show status of deployed applications.
    """
    try:
        # Get services
        deployment_service = get_deployment_service()
        docker_manager = get_docker_manager()
        
        if name:
            # Show status for single application
            deploy_dir = deployment_service.get_deployment_directory(name)
            if not deploy_dir.exists():
                logger.error(f"Application '{name}' is not deployed")
                raise typer.Exit(1)
            
            status = docker_manager.get_container_status(deploy_dir)
            _show_application_status(name, status)
            
        else:
            # Show status for all deployed applications
            deployments = deployment_service.list_deployments()
            if not deployments:
                console.print("No applications are currently deployed")
                return
            
            table = Table(title="Deployed Applications")
            table.add_column("Name")
            table.add_column("Status")
            
            for name, deploy_dir in deployments.items():
                status = docker_manager.get_container_status(deploy_dir)
                for container, state in status.items():
                    table.add_row(name, state)
            
            console.print(table)
        
    except Exception as e:
        logger.error(f"Failed to get status: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

@app.command()
def logs(
    name: str = typer.Argument(..., help="Name of the application"),
    tail: Optional[int] = typer.Option(100, help="Number of lines to show"),
    follow: bool = typer.Option(False, help="Follow log output"),
) -> None:
    """
    Show logs for a deployed application.
    """
    try:
        # Get services
        deployment_service = get_deployment_service()
        docker_manager = get_docker_manager()
        
        # Get deployment directory
        deploy_dir = deployment_service.get_deployment_directory(name)
        if not deploy_dir.exists():
            logger.error(f"Application '{name}' is not deployed")
            raise typer.Exit(1)
        
        # Get logs
        logs = docker_manager.get_container_logs(deploy_dir, tail=tail)
        console.print(logs)
        
        if follow:
            # TODO: Implement log following
            logger.warning("Log following is not yet implemented")
        
    except Exception as e:
        logger.error(f"Failed to get logs: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1)

def _show_deployment_plan(
    app: Application,
    port_override: Optional[int],
    volume_override: Optional[str],
    network_override: Optional[str],
) -> None:
    """Show deployment plan to user."""
    table = Table(title="Deployment Plan")
    
    table.add_column("Setting")
    table.add_column("Value")
    
    table.add_row("Application", app.name)
    table.add_row("Image", app.docker_url or "Not specified")
    table.add_row("Category", app.category)
    
    if port_override:
        table.add_row("Port Mapping", f"{port_override}:80 (Override)")
    else:
        table.add_row("Port Mapping", "Default")
        
    if volume_override:
        table.add_row("Volume Mapping", f"{volume_override} (Override)")
    else:
        table.add_row("Volume Mapping", "Default")
        
    if network_override:
        table.add_row("Network", network_override)
    else:
        table.add_row("Network", "default")
    
    console.print(table)

def _show_success_message(app: Application, deploy_dir: Path) -> None:
    """Show success message after deployment."""
    panel = Panel(
        f"""
        [green]Successfully deployed {app.name}![/green]
        
        Deployment directory: {deploy_dir}
        
        To view logs:
            easy-docker-deploy logs {app.name}
            
        To check status:
            easy-docker-deploy status {app.name}
            
        To stop the application:
            easy-docker-deploy stop {app.name}
        """,
        title="Deployment Complete",
        expand=False
    )
    console.print(panel)

def _show_application_status(name: str, status: Dict[str, str]) -> None:
    """Show status for a single application."""
    table = Table(title=f"Status for {name}")
    table.add_column("Container")
    table.add_column("Status")
    
    for container, state in status.items():
        table.add_row(container, state)
    
    console.print(table) 