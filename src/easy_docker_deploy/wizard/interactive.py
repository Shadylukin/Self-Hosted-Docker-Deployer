"""
Interactive wizard for guiding users through deployment setup.
"""
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm
from rich import print as rprint

from ..utils.docker import check_docker_installation
from ..utils.validation import validate_path
from ..utils.logging import get_logger
from ..utils.diagnostics import SystemDiagnostics
from ..utils.autofix import AutoFix

logger = get_logger(__name__)
console = Console()

class DeploymentWizard:
    """Interactive wizard for deployment configuration."""
    
    def __init__(self):
        self.console = Console()
        self.diagnostics = SystemDiagnostics()
    
    def welcome(self):
        """Display welcome message and introduction."""
        welcome_text = """
        # Welcome to Easy Docker Deploy! 🐳
        
        I'll guide you through setting up your media automation stack. Don't worry if you're new to Docker
        - I'll explain everything along the way!
        
        ## What we'll do:
        1. Run system diagnostics
        2. Check your system requirements
        3. Set up your media storage location
        4. Configure your services
        5. Deploy everything automatically
        
        Let's get started! 🚀
        """
        self.console.print(Panel(Markdown(welcome_text), title="Easy Docker Deploy Wizard"))
        
        # Run initial diagnostics
        self.console.print("\n[bold]Running system diagnostics...[/bold]")
        self.diagnostics.run_all_checks()
        self.diagnostics.print_report()
        
        # Handle any issues
        issues = self.diagnostics.get_issues()
        if issues:
            self.console.print("\n[yellow]⚠️ Some issues were detected that may affect deployment.[/yellow]")
            
            # Group issues by whether they can be auto-fixed
            fixable = [(name, result) for name, result in issues if result.can_autofix]
            manual = [(name, result) for name, result in issues if not result.can_autofix]
            
            if fixable:
                self.console.print("\n[bold]The following issues can be automatically fixed:[/bold]")
                for name, result in fixable:
                    self.console.print(f"• {name}: {result.message}")
                
                if Confirm.ask("Would you like me to attempt to fix these issues?"):
                    self.diagnostics.attempt_fixes()
                    # Re-run diagnostics to show updated status
                    self.console.print("\n[bold]Updated system status:[/bold]")
                    self.diagnostics.print_report()
            
            if manual:
                self.console.print("\n[bold]The following issues require manual intervention:[/bold]")
                for name, result in manual:
                    self.console.print(f"• {name}: {result.message}")
                    self.console.print(f"  To fix: {result.fix_instructions}")
            
            # Check if there are still issues after fixes
            remaining_issues = self.diagnostics.get_issues()
            if remaining_issues and not Confirm.ask("Would you like to continue anyway?"):
                raise typer.Exit()
    
    def check_prerequisites(self) -> bool:
        """
        Check and guide through prerequisites installation.
        
        Returns:
            bool: True if all prerequisites are met
        """
        self.console.print("\n[bold]Checking system requirements...[/bold]")
        
        # Re-run Docker check
        self.diagnostics.check_docker_status()
        if not self.diagnostics.results["docker"].status:
            result = self.diagnostics.results["docker"]
            self.console.print(Panel(
                f"[red]{result.message}[/red]\n\n"
                f"{result.details}\n\n"
                f"To fix:\n{result.fix_instructions}",
                title="Docker Required"
            ))
            
            if result.can_autofix and Confirm.ask("Would you like me to try to fix this?"):
                if AutoFix.attempt_fix("docker", result):
                    self.diagnostics.check_docker_status()  # Re-check Docker status
                    if self.diagnostics.results["docker"].status:
                        self.console.print("[green]✓[/green] Docker is now installed and running")
                        return True
            
            return False
        
        self.console.print("[green]✓[/green] Docker is installed and running")
        return True
    
    def configure_media_path(self, default_path: Optional[Path] = None) -> Path:
        """
        Guide user through media path configuration.
        
        Args:
            default_path: Optional default path to suggest
            
        Returns:
            Path: Configured media path
        """
        self.console.print("\n[bold]Media Storage Configuration[/bold]")
        
        help_text = """
        The media path is where all your files will be stored:
        • Movies and TV shows
        • Download files
        • Application settings
        
        Make sure you have enough space and proper permissions!
        """
        self.console.print(Panel(help_text, title="About Media Storage"))
        
        while True:
            if default_path:
                path_str = Prompt.ask(
                    "Enter media path",
                    default=str(default_path)
                )
            else:
                path_str = Prompt.ask("Enter media path")
            
            try:
                path = Path(path_str).resolve()
                validate_path(str(path))
                
                # Check disk space and permissions
                self.diagnostics.check_disk_space()
                self.diagnostics.check_permissions()
                
                issues_fixed = False
                
                if not self.diagnostics.results["disk"].status:
                    self.console.print(f"[yellow]Warning: {self.diagnostics.results['disk'].message}[/yellow]")
                    self.console.print(self.diagnostics.results["disk"].details)
                    
                    if self.diagnostics.results["disk"].can_autofix:
                        if Confirm.ask("Would you like me to try to free up some space?"):
                            if AutoFix.attempt_fix("disk", self.diagnostics.results["disk"]):
                                issues_fixed = True
                    
                    if not issues_fixed and not Confirm.ask("Continue with limited space?"):
                        continue
                
                if not self.diagnostics.results["permissions"].status:
                    self.console.print(f"[red]Error: {self.diagnostics.results['permissions'].message}[/red]")
                    
                    if self.diagnostics.results["permissions"].can_autofix:
                        if Confirm.ask("Would you like me to try to fix the permissions?"):
                            if AutoFix.attempt_fix("permissions", self.diagnostics.results["permissions"]):
                                issues_fixed = True
                    
                    if not issues_fixed:
                        self.console.print(self.diagnostics.results["permissions"].fix_instructions)
                        continue
                
                if issues_fixed:
                    # Re-check after fixes
                    self.diagnostics.check_disk_space()
                    self.diagnostics.check_permissions()
                
                # Show space information
                total, used, free = self._get_disk_space(path)
                self.console.print(f"\nDisk space at {path}:")
                self.console.print(f"• Total: {total}")
                self.console.print(f"• Used: {used}")
                self.console.print(f"• Free: {free}")
                
                if Confirm.ask("Use this location?"):
                    return path
            except Exception as e:
                self.console.print(f"[red]Error:[/red] {str(e)}")
                self.console.print("Please try a different path.")
    
    def configure_services(self) -> dict:
        """
        Guide user through service configuration.
        
        Returns:
            dict: Service configuration options
        """
        self.console.print("\n[bold]Service Configuration[/bold]")
        
        # Check ports before showing service list
        self.diagnostics.check_ports()
        if not self.diagnostics.results["ports"].status:
            self.console.print(f"\n[yellow]Warning: {self.diagnostics.results['ports'].message}[/yellow]")
            self.console.print(self.diagnostics.results["ports"].details)
            
            if self.diagnostics.results["ports"].can_autofix:
                if Confirm.ask("Would you like me to try to free up the required ports?"):
                    if AutoFix.attempt_fix("ports", self.diagnostics.results["ports"]):
                        self.diagnostics.check_ports()  # Re-check ports
            
            if not self.diagnostics.results["ports"].status:
                if not Confirm.ask("Would you like to continue with different ports?"):
                    raise typer.Exit()
        
        config = {
            "plex": True,  # Plex is required
            "overseerr": True,  # Overseerr is required
            "sonarr": True,
            "radarr": True,
            "prowlarr": True,
            "qbittorrent": True
        }
        
        help_text = """
        The following services will be deployed:
        
        • [bold]Plex[/bold]: Media server for streaming
        • [bold]Overseerr[/bold]: Request management and discovery
        • [bold]Sonarr[/bold]: TV show automation
        • [bold]Radarr[/bold]: Movie automation
        • [bold]Prowlarr[/bold]: Indexer management
        • [bold]qBittorrent[/bold]: Download client
        
        All services are pre-configured to work together!
        """
        self.console.print(Panel(help_text, title="About Services"))
        
        return config
    
    def show_deployment_plan(self, config: dict):
        """
        Show the deployment plan for confirmation.
        
        Args:
            config: Configuration to display
        """
        # Run final checks
        self.diagnostics.check_memory()
        self.diagnostics.check_network()
        
        issues = self.diagnostics.get_issues()
        if issues:
            self.console.print("\n[yellow]⚠️ Some issues may affect deployment:[/yellow]")
            
            # Group issues by whether they can be auto-fixed
            fixable = [(name, result) for name, result in issues if result.can_autofix]
            manual = [(name, result) for name, result in issues if not result.can_autofix]
            
            if fixable:
                self.console.print("\n[bold]The following issues can be automatically fixed:[/bold]")
                for name, result in fixable:
                    self.console.print(f"• {name}: {result.message}")
                
                if Confirm.ask("Would you like me to attempt to fix these issues?"):
                    self.diagnostics.attempt_fixes()
                    # Re-run checks to show updated status
                    self.diagnostics.check_memory()
                    self.diagnostics.check_network()
            
            if manual:
                self.console.print("\n[bold]The following issues require manual intervention:[/bold]")
                for name, result in manual:
                    self.console.print(f"• {name}: {result.message}")
                    self.console.print(f"  To fix: {result.fix_instructions}")
        
        plan_text = """
        I'll now:
        1. Create necessary directories
        2. Set up Docker network
        3. Deploy and configure all services
        4. Integrate everything automatically
        
        After deployment:
        • Access Plex at http://localhost:32400/web
        • Access Overseerr at http://localhost:5055
        • Access Sonarr at http://localhost:8989
        • Access Radarr at http://localhost:7878
        • Access Prowlarr at http://localhost:9696
        • Access qBittorrent at http://localhost:8080
        
        Need help? Check our documentation at:
        https://github.com/yourusername/easy-docker-deploy
        """
        self.console.print(Panel(
            Markdown(plan_text),
            title="Deployment Plan"
        ))
    
    def _get_disk_space(self, path: Path) -> tuple[str, str, str]:
        """Get formatted disk space information."""
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            return (
                self._format_size(total),
                self._format_size(used),
                self._format_size(free)
            )
        except Exception:
            return ("Unknown", "Unknown", "Unknown")
    
    @staticmethod
    def _format_size(size: int) -> str:
        """Format size in bytes to human readable string."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024:
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} PB" 