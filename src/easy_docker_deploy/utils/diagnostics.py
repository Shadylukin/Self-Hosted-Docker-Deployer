"""
Diagnostic utilities for detecting and reporting common issues.
"""
import os
import socket
import psutil
import subprocess
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass
from rich.console import Console
from rich.table import Table
from rich.prompt import Confirm

from .logging import get_logger
from .docker import check_docker_installation, get_docker_info

logger = get_logger(__name__)
console = Console()

@dataclass
class DiagnosticResult:
    """Result of a diagnostic check."""
    status: bool
    message: str
    details: str = ""
    fix_instructions: str = ""
    can_autofix: bool = False

class SystemDiagnostics:
    """System diagnostics checker."""
    
    def __init__(self):
        self.results: Dict[str, DiagnosticResult] = {}
        
    def run_all_checks(self) -> bool:
        """
        Run all diagnostic checks.
        
        Returns:
            bool: True if all critical checks pass
        """
        self.check_docker_status()
        self.check_ports()
        self.check_disk_space()
        self.check_memory()
        self.check_network()
        self.check_permissions()
        
        return all(result.status for result in self.results.values())
    
    def check_docker_status(self):
        """Check Docker installation and status."""
        is_installed, docker_version, compose_version = get_docker_info()
        
        if not is_installed:
            self.results["docker"] = DiagnosticResult(
                status=False,
                message="Docker is not installed or not running",
                details="Docker and Docker Compose are required for deployment",
                fix_instructions="Install Docker Desktop (Windows/Mac) or Docker Engine (Linux)",
                can_autofix=False  # Installation requires manual intervention
            )
            return
            
        # Check Docker daemon
        try:
            subprocess.run(["docker", "info"], capture_output=True, check=True)
            self.results["docker"] = DiagnosticResult(
                status=True,
                message="Docker is installed and running",
                details=f"Docker: {docker_version}\nCompose: {compose_version}"
            )
        except subprocess.CalledProcessError:
            self.results["docker"] = DiagnosticResult(
                status=False,
                message="Docker daemon is not running",
                details="The Docker service needs to be started",
                fix_instructions="Start Docker Desktop or run 'sudo systemctl start docker'",
                can_autofix=True
            )
    
    def check_ports(self):
        """Check if required ports are available."""
        required_ports = {
            32400: "Plex",
            5055: "Overseerr",
            8989: "Sonarr",
            7878: "Radarr",
            9696: "Prowlarr",
            8080: "qBittorrent"
        }
        
        used_ports = []
        for port, service in required_ports.items():
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('127.0.0.1', port))
                sock.close()
            except OSError:
                used_ports.append((port, service))
                
        if used_ports:
            ports_str = "\n".join(f"• Port {port} ({service})" for port, service in used_ports)
            self.results["ports"] = DiagnosticResult(
                status=False,
                message="Some required ports are in use",
                details=f"The following ports are not available:\n{ports_str}",
                fix_instructions="Stop any services using these ports or modify the port mappings",
                can_autofix=True
            )
        else:
            self.results["ports"] = DiagnosticResult(
                status=True,
                message="All required ports are available"
            )
    
    def check_disk_space(self, min_space_gb: int = 50):
        """Check available disk space."""
        path = Path.home()
        try:
            total, used, free = psutil.disk_usage(str(path))
            free_gb = free / (1024 * 1024 * 1024)
            
            if free_gb < min_space_gb:
                self.results["disk"] = DiagnosticResult(
                    status=False,
                    message=f"Insufficient disk space",
                    details=f"Available: {free_gb:.1f}GB\nRecommended: {min_space_gb}GB",
                    fix_instructions="Free up disk space or choose a different location",
                    can_autofix=True
                )
            else:
                self.results["disk"] = DiagnosticResult(
                    status=True,
                    message="Sufficient disk space available",
                    details=f"Available: {free_gb:.1f}GB"
                )
        except Exception as e:
            self.results["disk"] = DiagnosticResult(
                status=False,
                message="Unable to check disk space",
                details=str(e)
            )
    
    def check_memory(self, min_memory_gb: int = 4):
        """Check available system memory."""
        try:
            memory = psutil.virtual_memory()
            total_gb = memory.total / (1024 * 1024 * 1024)
            available_gb = memory.available / (1024 * 1024 * 1024)
            
            if available_gb < min_memory_gb:
                self.results["memory"] = DiagnosticResult(
                    status=False,
                    message="Low available memory",
                    details=f"Available: {available_gb:.1f}GB\nRecommended: {min_memory_gb}GB",
                    fix_instructions="Close unnecessary applications or add more RAM",
                    can_autofix=False  # Memory issues require manual intervention
                )
            else:
                self.results["memory"] = DiagnosticResult(
                    status=True,
                    message="Sufficient memory available",
                    details=f"Available: {available_gb:.1f}GB of {total_gb:.1f}GB"
                )
        except Exception as e:
            self.results["memory"] = DiagnosticResult(
                status=False,
                message="Unable to check memory",
                details=str(e)
            )
    
    def check_network(self):
        """Check network connectivity."""
        try:
            # Test Docker Hub connectivity
            subprocess.run(
                ["curl", "-f", "https://hub.docker.com"],
                capture_output=True,
                check=True
            )
            self.results["network"] = DiagnosticResult(
                status=True,
                message="Network connectivity OK",
                details="Can reach Docker Hub"
            )
        except subprocess.CalledProcessError:
            self.results["network"] = DiagnosticResult(
                status=False,
                message="Network connectivity issues",
                details="Cannot reach Docker Hub",
                fix_instructions="Check your internet connection and firewall settings",
                can_autofix=True
            )
        except Exception as e:
            self.results["network"] = DiagnosticResult(
                status=False,
                message="Unable to check network",
                details=str(e)
            )
    
    def check_permissions(self):
        """Check file system permissions."""
        path = Path.home()
        try:
            test_file = path / ".docker_test"
            test_file.touch()
            test_file.unlink()
            
            self.results["permissions"] = DiagnosticResult(
                status=True,
                message="File system permissions OK"
            )
        except Exception as e:
            self.results["permissions"] = DiagnosticResult(
                status=False,
                message="Permission issues detected",
                details=str(e),
                fix_instructions="Ensure you have write permissions in the target directory",
                can_autofix=True
            )
    
    def print_report(self):
        """Print a formatted diagnostic report."""
        table = Table(title="System Diagnostic Report")
        table.add_column("Check", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Message")
        table.add_column("Details", style="dim")
        table.add_column("Fix", style="yellow")
        table.add_column("Auto-Fix", style="green")
        
        for check, result in self.results.items():
            status = "✓" if result.status else "✗"
            status_style = "green" if result.status else "red"
            autofix = "Available" if result.can_autofix else "Manual Fix"
            
            table.add_row(
                check.title(),
                f"[{status_style}]{status}[/{status_style}]",
                result.message,
                result.details,
                result.fix_instructions,
                autofix if not result.status else ""
            )
        
        console.print(table)
        
    def get_issues(self) -> List[Tuple[str, DiagnosticResult]]:
        """
        Get list of failed checks.
        
        Returns:
            List of (check_name, result) tuples for failed checks
        """
        return [(name, result) for name, result in self.results.items() 
                if not result.status]
    
    def attempt_fixes(self) -> bool:
        """
        Attempt to fix all failed checks that support auto-fixing.
        
        Returns:
            bool: True if all attempted fixes were successful
        """
        from .autofix import AutoFix
        
        fixed = []
        for name, result in self.get_issues():
            if result.can_autofix:
                if AutoFix.attempt_fix(name, result):
                    fixed.append(name)
        
        if fixed:
            console.print(f"\n[green]Successfully fixed {len(fixed)} issue(s)![/green]")
            # Re-run checks to update status
            self.run_all_checks()
            return True
            
        return False 