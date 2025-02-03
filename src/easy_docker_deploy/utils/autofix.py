"""
Automatic fix attempts for common deployment issues.
"""
import os
import sys
import subprocess
import psutil
import socket
from pathlib import Path
from typing import Optional, List, Tuple
from rich.console import Console
from rich.prompt import Confirm

from .logging import get_logger
from .diagnostics import DiagnosticResult

logger = get_logger(__name__)
console = Console()

class AutoFix:
    """Automatic fix attempts for common issues."""
    
    @staticmethod
    def attempt_fix(issue_type: str, diagnostic: DiagnosticResult) -> bool:
        """
        Attempt to automatically fix an issue.
        
        Args:
            issue_type: Type of issue to fix
            diagnostic: Diagnostic result containing issue details
            
        Returns:
            bool: True if fix was successful
        """
        fix_method = getattr(AutoFix, f"_fix_{issue_type}", None)
        if fix_method is None:
            logger.warning(f"No automatic fix available for {issue_type}")
            return False
            
        if not Confirm.ask(f"Would you like me to attempt to fix the {issue_type} issue?"):
            return False
            
        try:
            console.print(f"\n[bold]Attempting to fix {issue_type} issue...[/bold]")
            return fix_method(diagnostic)
        except Exception as e:
            logger.error(f"Error during {issue_type} fix: {str(e)}")
            console.print(f"[red]Failed to fix {issue_type}: {str(e)}[/red]")
            return False
    
    @staticmethod
    def _fix_docker(diagnostic: DiagnosticResult) -> bool:
        """Attempt to fix Docker issues."""
        if sys.platform == "win32":
            # Try starting Docker Desktop on Windows
            try:
                console.print("Attempting to start Docker Desktop...")
                subprocess.run(
                    ["powershell", "-Command", "Start-Process 'C:\\Program Files\\Docker\\Docker\\Docker Desktop.exe'"],
                    check=True
                )
                console.print("Waiting for Docker to start (this may take a minute)...")
                for _ in range(30):  # Wait up to 30 seconds
                    try:
                        subprocess.run(["docker", "info"], capture_output=True, check=True)
                        console.print("[green]Successfully started Docker Desktop![/green]")
                        return True
                    except subprocess.CalledProcessError:
                        import time
                        time.sleep(1)
                return False
            except Exception as e:
                logger.error(f"Failed to start Docker Desktop: {str(e)}")
                return False
        elif sys.platform == "linux":
            # Try starting Docker daemon on Linux
            try:
                console.print("Attempting to start Docker daemon...")
                subprocess.run(["sudo", "systemctl", "start", "docker"], check=True)
                console.print("[green]Successfully started Docker daemon![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to start Docker daemon: {str(e)}")
                return False
        else:
            console.print("[yellow]Automatic Docker fixes are only available on Windows and Linux[/yellow]")
            return False
    
    @staticmethod
    def _fix_ports(diagnostic: DiagnosticResult) -> bool:
        """Attempt to fix port conflicts."""
        # Extract used ports from diagnostic details
        used_ports = []
        for line in diagnostic.details.split("\n"):
            if "Port" in line:
                try:
                    port = int(line.split("Port")[1].split("(")[0].strip())
                    used_ports.append(port)
                except (ValueError, IndexError):
                    continue
        
        if not used_ports:
            return False
        
        fixed = []
        for port in used_ports:
            try:
                # Find process using the port
                for conn in psutil.net_connections(kind='inet'):
                    if conn.laddr.port == port:
                        try:
                            process = psutil.Process(conn.pid)
                            name = process.name()
                            if Confirm.ask(f"Kill {name} (PID: {conn.pid}) using port {port}?"):
                                process.terminate()
                                process.wait(timeout=3)
                                fixed.append(port)
                                console.print(f"[green]Successfully freed port {port}[/green]")
                        except (psutil.NoSuchProcess, psutil.TimeoutExpired):
                            pass
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue
        
        return len(fixed) > 0
    
    @staticmethod
    def _fix_disk(diagnostic: DiagnosticResult) -> bool:
        """Attempt to fix disk space issues."""
        if sys.platform == "win32":
            try:
                # Run disk cleanup on Windows
                console.print("Running Windows Disk Cleanup...")
                subprocess.run(
                    ["cleanmgr", "/sagerun:1"],
                    capture_output=True,
                    check=True
                )
                console.print("[green]Disk Cleanup completed![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to run Disk Cleanup: {str(e)}")
                return False
        else:
            # On Linux/Mac, clean Docker system
            try:
                console.print("Cleaning Docker system...")
                subprocess.run(["docker", "system", "prune", "-f"], check=True)
                console.print("[green]Successfully cleaned Docker system![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to clean Docker system: {str(e)}")
                return False
    
    @staticmethod
    def _fix_permissions(diagnostic: DiagnosticResult) -> bool:
        """Attempt to fix permission issues."""
        path = Path.home()
        
        if sys.platform == "win32":
            try:
                # Take ownership and grant full control on Windows
                console.print("Attempting to fix permissions...")
                subprocess.run(
                    ["takeown", "/F", str(path), "/R", "/D", "Y"],
                    capture_output=True,
                    check=True
                )
                subprocess.run(
                    ["icacls", str(path), "/grant", f"{os.getlogin()}:F", "/T"],
                    capture_output=True,
                    check=True
                )
                console.print("[green]Successfully updated permissions![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to fix permissions: {str(e)}")
                return False
        else:
            try:
                # Fix ownership on Linux/Mac
                console.print("Attempting to fix permissions...")
                subprocess.run(
                    ["sudo", "chown", "-R", f"{os.getlogin()}:", str(path)],
                    check=True
                )
                console.print("[green]Successfully updated permissions![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to fix permissions: {str(e)}")
                return False
    
    @staticmethod
    def _fix_network(diagnostic: DiagnosticResult) -> bool:
        """Attempt to fix network connectivity issues."""
        if sys.platform == "win32":
            try:
                # Flush DNS and reset Winsock on Windows
                console.print("Attempting to fix network connectivity...")
                subprocess.run(["ipconfig", "/flushdns"], check=True)
                subprocess.run(["netsh", "winsock", "reset"], check=True)
                console.print("[green]Network settings reset! You may need to restart your computer.[/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to fix network: {str(e)}")
                return False
        else:
            try:
                # Flush DNS on Linux/Mac
                console.print("Attempting to fix network connectivity...")
                if sys.platform == "darwin":
                    subprocess.run(["sudo", "killall", "-HUP", "mDNSResponder"], check=True)
                else:
                    subprocess.run(["sudo", "systemd-resolve", "--flush-caches"], check=True)
                console.print("[green]DNS cache flushed![/green]")
                return True
            except Exception as e:
                logger.error(f"Failed to fix network: {str(e)}")
                return False 