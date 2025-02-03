"""
Command module for listing available applications.
"""
import typer
from typing import Optional
from rich.console import Console
from rich.table import Table

from ...config.pirate import PirateConfigFactory
from ...utils.logging import get_logger

# Initialize logger and console
logger = get_logger(__name__)
console = Console()

app = typer.Typer()

@app.callback(invoke_without_command=True)
def list_services(
    category: Optional[str] = typer.Option(None, help="Filter by category"),
    details: bool = typer.Option(False, "--details", "-d", help="Show detailed information")
) -> None:
    """List all available applications."""
    try:
        # Create table
        table = Table(title="Available Applications")
        table.add_column("Name")
        table.add_column("Description")
        table.add_column("Category")
        if details:
            table.add_column("Ports")
            table.add_column("Volumes")
        
        # Add Pirate mode services
        factory = PirateConfigFactory()
        services = [
            factory.create_media_server(),
            factory.create_content_aggregator(),
            factory.create_download_manager()
        ]
        
        for service in services:
            if category and category.lower() != "media":
                continue
                
            row = [
                service.name,
                service.description,
                "Media Automation"
            ]
            
            if details:
                row.extend([
                    ", ".join(str(p) for p in service.ports),
                    ", ".join(str(v) for v in service.volumes)
                ])
            
            table.add_row(*row)
        
        console.print(table)
        
    except Exception as e:
        logger.error(f"Failed to list services: {str(e)}")
        console.print(f"[red]Error:[/red] {str(e)}")
        raise typer.Exit(1) 