"""
Main CLI entry point for Easy Docker Deploy.
"""
import os
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console

from ..config.settings import get_config
from ..utils.logging import setup_logging, get_logger
from .commands import deploy
from .commands.list import list_services
from .commands.pirate import pirate

# Create Typer app
app = typer.Typer(
    help="Easy Docker Deploy - Deploy Docker applications with ease",
    add_completion=False
)

# Add sub-commands
app.add_typer(deploy.app, name="deploy")
app.add_typer(list_services.app, name="list")
app.add_typer(pirate.app, name="pirate")

# Create console
console = Console()

# Get logger
logger = get_logger(__name__)

@app.callback()
def main(
    log_level: str = typer.Option(
        "INFO",
        "--log-level",
        "-l",
        help="Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)"
    ),
    log_file: Optional[Path] = typer.Option(
        None,
        "--log-file",
        "-f",
        help="Log file path"
    ),
    config_file: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Configuration file path"
    ),
) -> None:
    """
    Easy Docker Deploy - Deploy Docker applications with ease.
    """
    try:
        # Setup logging
        setup_logging(log_level=log_level, log_file=log_file)
        
        # Load configuration
        config = get_config()
        if config_file:
            config.load_from_file(config_file)
        
        # Create necessary directories
        os.makedirs(config.cache_dir, exist_ok=True)
        os.makedirs(config.log_dir, exist_ok=True)
        os.makedirs(config.default_volume_base, exist_ok=True)
        
        logger.debug("CLI initialized successfully")
        
    except Exception as e:
        console.print(f"[red]Error during initialization:[/red] {str(e)}")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 