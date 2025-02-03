"""
Visualization utilities for service dependencies and deployment progress.
"""
import time
from typing import Dict, List, Set
from rich.console import Console
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn
)
from rich.live import Live
from rich.panel import Panel
from rich.tree import Tree
from rich.table import Table
from rich.box import HEAVY
from rich import print as rprint

console = Console()

class ServiceVisualizer:
    """Service dependency and deployment visualization."""
    
    @staticmethod
    def create_dependency_graph(services: dict) -> Panel:
        """
        Create a visual representation of service dependencies.
        
        Args:
            services: Service configuration dictionary
            
        Returns:
            Panel containing the dependency tree
        """
        # Create dependency tree
        tree = Tree("🐳 Services", guide_style="bold cyan")
        
        # Track processed services to handle circular dependencies
        processed: Set[str] = set()
        
        def add_dependencies(service_name: str, node: Tree, depth: int = 0):
            """Recursively add service dependencies to the tree."""
            if depth > 10 or service_name in processed:  # Prevent infinite recursion
                return
            
            processed.add(service_name)
            service = services.get(service_name, {})
            
            # Get service details
            description = service.get("_docs", {}).get("description", "")
            ports = service.get("_docs", {}).get("ports", "")
            
            # Create service node with details
            service_node = node.add(
                f"[bold cyan]{service_name}[/bold cyan]\n"
                f"├─ [dim]{description}[/dim]\n"
                f"└─ [blue]{ports}[/blue]"
            )
            
            # Add dependencies
            if "depends_on" in service:
                deps_node = service_node.add("[yellow]Dependencies[/yellow]")
                for dep in service["depends_on"]:
                    add_dependencies(dep, deps_node, depth + 1)
            
            # Add network connections
            if "networks" in service:
                nets_node = service_node.add("[green]Networks[/green]")
                for net in service["networks"]:
                    nets_node.add(f"[dim green]└─ {net}[/dim green]")
            
            # Add volumes
            if "volumes" in service:
                vols_node = service_node.add("[magenta]Volumes[/magenta]")
                for vol in service["volumes"]:
                    vols_node.add(f"[dim magenta]└─ {vol}[/dim magenta]")
        
        # Add all services to the tree
        for service_name in services:
            if service_name not in processed:
                add_dependencies(service_name, tree)
        
        return Panel(tree, title="Service Dependencies", border_style="cyan")
    
    @staticmethod
    def create_deployment_progress() -> Progress:
        """
        Create a rich progress bar for deployment visualization.
        
        Returns:
            Progress: Configured progress bar
        """
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            console=console,
            expand=True
        )
    
    @staticmethod
    def create_service_matrix(services: dict) -> Table:
        """
        Create a matrix view of service relationships.
        
        Args:
            services: Service configuration dictionary
            
        Returns:
            Table: Service relationship matrix
        """
        # Get all service names
        service_names = list(services.keys())
        
        # Create table
        table = Table(
            title="Service Relationship Matrix",
            box=HEAVY,
            show_header=True,
            header_style="bold magenta"
        )
        
        # Add columns
        table.add_column("Service", style="cyan")
        for name in service_names:
            table.add_column(name, justify="center")
        
        # Add rows
        for service_name in service_names:
            row = [service_name]
            service = services[service_name]
            
            for other_service in service_names:
                # Check relationships
                relations = []
                
                # Check dependencies
                if "depends_on" in service and other_service in service["depends_on"]:
                    relations.append("D")  # Depends on
                
                # Check network connections
                if ("networks" in service and "networks" in services[other_service] and 
                    set(service["networks"]) & set(services[other_service]["networks"])):
                    relations.append("N")  # Network connection
                
                # Add cell content
                if relations:
                    row.append("[green]" + ",".join(relations) + "[/green]")
                else:
                    row.append("[dim]-[/dim]")
            
            table.add_row(*row)
        
        return table
    
    @staticmethod
    def show_deployment_summary(services: dict):
        """
        Show a deployment summary with service status.
        
        Args:
            services: Service configuration dictionary
        """
        # Create status table
        table = Table(
            title="Deployment Summary",
            box=HEAVY,
            show_header=True,
            header_style="bold magenta"
        )
        
        table.add_column("Service", style="cyan")
        table.add_column("Status", justify="center")
        table.add_column("Web UI")
        table.add_column("Description")
        
        for name, service in services.items():
            # Get service details
            description = service.get("_docs", {}).get("description", "")
            ports = service.get("ports", [])
            
            # Find web UI port
            web_ui = ""
            for port in ports:
                if isinstance(port, str) and ":" in port:
                    host_port = port.split(":")[0]
                    web_ui = f"http://localhost:{host_port}"
                    break
            
            table.add_row(
                name,
                "[green]✓[/green]",
                web_ui if web_ui else "[dim]-[/dim]",
                description
            )
        
        console.print(table)

class DeploymentProgress:
    """Deployment progress tracking and visualization."""
    
    def __init__(self, services: dict):
        self.services = services
        self.progress = ServiceVisualizer.create_deployment_progress()
        self.tasks = {}
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.progress.stop()
    
    def start_deployment(self):
        """Start deployment progress tracking."""
        # Show dependency graph
        console.print(ServiceVisualizer.create_dependency_graph(self.services))
        
        # Show relationship matrix
        console.print(ServiceVisualizer.create_service_matrix(self.services))
        
        # Create overall progress
        self.tasks["overall"] = self.progress.add_task(
            "[bold]Overall Deployment Progress",
            total=len(self.services) * 100
        )
        
        # Create service-specific tasks
        for name in self.services:
            self.tasks[name] = self.progress.add_task(
                f"[cyan]Deploying {name}...",
                total=100
            )
    
    def update_service(self, service_name: str, status: str, progress: int):
        """
        Update service deployment progress.
        
        Args:
            service_name: Name of the service
            status: Current status message
            progress: Progress percentage (0-100)
        """
        if service_name in self.tasks:
            # Update service progress
            self.progress.update(
                self.tasks[service_name],
                completed=progress,
                description=f"[cyan]{service_name}:[/cyan] {status}"
            )
            
            # Update overall progress
            total_progress = sum(
                self.progress.tasks[self.tasks[name]].completed
                for name in self.services
            ) / len(self.services)
            
            self.progress.update(
                self.tasks["overall"],
                completed=total_progress
            )
    
    def complete_deployment(self):
        """Complete deployment and show summary."""
        # Ensure all progress bars are complete
        for task_id in self.tasks.values():
            self.progress.update(task_id, completed=100)
        
        # Show deployment summary
        console.print("\n[bold green]Deployment Complete![/bold green]")
        ServiceVisualizer.show_deployment_summary(self.services) 