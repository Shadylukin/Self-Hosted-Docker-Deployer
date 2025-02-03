"""
Resource monitoring and visualization for Docker containers.
"""
import psutil
import docker
from typing import Dict, List, Optional
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.progress import BarColumn, Progress
from rich.layout import Layout
from rich.box import ROUNDED
from rich import print as rprint
from .theme_manager import ThemeManager

class ResourceMonitor:
    """Monitor and visualize Docker container resource usage."""
    
    def __init__(self, theme_name: str = "default"):
        self.docker_client = docker.from_env()
        self.containers = {}
        self.stats = {}
        self.theme = ThemeManager(theme_name)
        self.console = Console(theme=self.theme.get_rich_theme())
    
    def update_stats(self):
        """Update container resource statistics."""
        try:
            for container in self.docker_client.containers.list():
                stats = container.stats(stream=False)
                self.stats[container.name] = {
                    "cpu_percent": self._calculate_cpu_percent(stats),
                    "memory_usage": self._calculate_memory_usage(stats),
                    "network_io": self._calculate_network_io(stats),
                    "disk_io": self._calculate_disk_io(stats),
                    "status": container.status,
                    "health": self._get_health_status(container)
                }
        except Exception as e:
            self.console.print(f"[error]Error updating stats: {str(e)}[/error]")
    
    def create_resource_panel(self) -> Panel:
        """Create a panel showing resource usage."""
        table = Table(box=ROUNDED, **self.theme.get_table_style())
        
        # Add columns
        table.add_column("Container", style="default")
        table.add_column("CPU", justify="right", style="cpu")
        table.add_column("Memory", justify="right", style="memory")
        table.add_column("Network I/O", justify="right", style="network")
        table.add_column("Disk I/O", justify="right", style="disk")
        table.add_column("Status", justify="center")
        table.add_column("Health", justify="center")
        
        # Add rows
        for name, stats in self.stats.items():
            status_style = self.theme.get_status_style(stats["status"])
            health_style = self.theme.get_status_style(stats["health"])
            cpu_style = self.theme.get_resource_style(stats["cpu_percent"])
            memory_percent = (stats["memory_usage"] / psutil.virtual_memory().total) * 100
            memory_style = self.theme.get_resource_style(memory_percent)
            
            table.add_row(
                name,
                f"{stats['cpu_percent']:.1f}%",
                self._format_bytes(stats["memory_usage"]),
                self._format_network_io(stats["network_io"]),
                self._format_disk_io(stats["disk_io"]),
                status_style.render(stats["status"]),
                health_style.render(stats["health"])
            )
        
        return Panel(
            table,
            title="[title]Container Resource Usage[/title]",
            **self.theme.get_panel_style()
        )
    
    def create_resource_bars(self) -> Progress:
        """Create progress bars for resource usage."""
        progress = Progress(
            *Progress.get_default_columns(),
            console=self.console,
            expand=True
        )
        
        for name, stats in self.stats.items():
            # CPU bar
            progress.add_task(
                f"[title]{name}[/title] CPU",
                total=100,
                completed=stats["cpu_percent"],
                style="cpu"
            )
            # Memory bar
            memory_percent = (stats["memory_usage"] / psutil.virtual_memory().total) * 100
            progress.add_task(
                f"[title]{name}[/title] Memory",
                total=100,
                completed=memory_percent,
                style="memory"
            )
        
        return progress
    
    def create_service_health_map(self) -> Layout:
        """Create an interactive service health map."""
        layout = Layout()
        
        # Create status indicators
        status_table = Table(box=ROUNDED, **self.theme.get_table_style())
        status_table.add_column("Service")
        status_table.add_column("Status")
        status_table.add_column("Health")
        status_table.add_column("Ports")
        status_table.add_column("Networks")
        
        for name, stats in self.stats.items():
            container = self.docker_client.containers.get(name)
            
            # Get port mappings
            ports = []
            for port in container.attrs["NetworkSettings"]["Ports"] or {}:
                if container.attrs["NetworkSettings"]["Ports"][port]:
                    host_port = container.attrs["NetworkSettings"]["Ports"][port][0]["HostPort"]
                    ports.append(f"{host_port}->{port}")
            
            # Get networks
            networks = list(container.attrs["NetworkSettings"]["Networks"].keys())
            
            status_table.add_row(
                name,
                self._get_status_indicator(stats["status"]),
                self._get_health_indicator(stats["health"]),
                "\n".join(ports) or "-",
                "\n".join(networks) or "-"
            )
        
        layout.update(Panel(
            status_table,
            title="[title]Service Health Map[/title]",
            **self.theme.get_panel_style()
        ))
        return layout
    
    @staticmethod
    def _calculate_cpu_percent(stats: dict) -> float:
        """Calculate CPU usage percentage."""
        cpu_delta = stats["cpu_stats"]["cpu_usage"]["total_usage"] - \
                   stats["precpu_stats"]["cpu_usage"]["total_usage"]
        system_delta = stats["cpu_stats"]["system_cpu_usage"] - \
                      stats["precpu_stats"]["system_cpu_usage"]
        
        if system_delta > 0.0:
            return (cpu_delta / system_delta) * 100.0
        return 0.0
    
    @staticmethod
    def _calculate_memory_usage(stats: dict) -> int:
        """Calculate memory usage in bytes."""
        return stats["memory_stats"].get("usage", 0)
    
    @staticmethod
    def _calculate_network_io(stats: dict) -> tuple:
        """Calculate network I/O in bytes."""
        networks = stats.get("networks", {})
        rx_bytes = sum(net.get("rx_bytes", 0) for net in networks.values())
        tx_bytes = sum(net.get("tx_bytes", 0) for net in networks.values())
        return (rx_bytes, tx_bytes)
    
    @staticmethod
    def _calculate_disk_io(stats: dict) -> tuple:
        """Calculate disk I/O in bytes."""
        if "blkio_stats" in stats:
            read_bytes = sum(stat["value"] for stat in stats["blkio_stats"]["io_service_bytes_recursive"]
                           if stat["op"] == "Read")
            write_bytes = sum(stat["value"] for stat in stats["blkio_stats"]["io_service_bytes_recursive"]
                            if stat["op"] == "Write")
            return (read_bytes, write_bytes)
        return (0, 0)
    
    @staticmethod
    def _get_health_status(container) -> str:
        """Get container health status."""
        if "Health" in container.attrs["State"]:
            return container.attrs["State"]["Health"]["Status"]
        return "N/A"
    
    @staticmethod
    def _format_bytes(bytes_value: int) -> str:
        """Format bytes to human readable string."""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes_value < 1024:
                return f"{bytes_value:.1f}{unit}"
            bytes_value /= 1024
        return f"{bytes_value:.1f}TB"
    
    @staticmethod
    def _format_network_io(io_tuple: tuple) -> str:
        """Format network I/O tuple."""
        rx, tx = io_tuple
        return f"↓{ResourceMonitor._format_bytes(rx)} ↑{ResourceMonitor._format_bytes(tx)}"
    
    @staticmethod
    def _format_disk_io(io_tuple: tuple) -> str:
        """Format disk I/O tuple."""
        read, write = io_tuple
        return f"R:{ResourceMonitor._format_bytes(read)} W:{ResourceMonitor._format_bytes(write)}"
    
    def _get_status_indicator(self, status: str) -> str:
        """Get status indicator with emoji."""
        indicators = {
            "running": "[service.running]🟢 Running[/]",
            "exited": "[service.stopped]🔴 Stopped[/]",
            "paused": "[service.starting]🟡 Paused[/]",
            "restarting": "[service.starting]🔄 Restarting[/]"
        }
        return indicators.get(status, "[dim]⚪ Unknown[/]")
    
    def _get_health_indicator(self, health: str) -> str:
        """Get health indicator with emoji."""
        indicators = {
            "healthy": "[service.healthy]✅ Healthy[/]",
            "unhealthy": "[service.unhealthy]❌ Unhealthy[/]",
            "starting": "[service.starting]⏳ Starting[/]",
            "N/A": "[dim]ℹ️ N/A[/]"
        }
        return indicators.get(health, "[dim]❓ Unknown[/]") 