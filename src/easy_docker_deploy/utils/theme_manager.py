"""
Theme manager for Easy Docker Deploy visualization components.
Provides predefined themes and customization options for resource monitoring and service visualization.
"""
from dataclasses import dataclass
from typing import Dict, Optional
from rich.style import Style
from rich.theme import Theme

@dataclass
class ThemeColors:
    """Color scheme for a theme."""
    # Background colors
    background: str
    surface: str
    panel: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    text_muted: str
    
    # Status colors
    success: str
    warning: str
    error: str
    info: str
    
    # Resource usage colors
    cpu: str
    memory: str
    network: str
    disk: str
    
    # Accent colors
    accent_primary: str
    accent_secondary: str

class ThemeManager:
    """Manages themes for Easy Docker Deploy visualization."""
    
    # Predefined themes
    THEMES = {
        "default": ThemeColors(
            # Light theme with blue accents
            background="#ffffff",
            surface="#f5f5f5",
            panel="#e0e0e0",
            text_primary="#2e3440",
            text_secondary="#4c566a",
            text_muted="#9e9e9e",
            success="#00c853",
            warning="#ffd600",
            error="#ff1744",
            info="#00b0ff",
            cpu="#2196f3",
            memory="#673ab7",
            network="#009688",
            disk="#ff9800",
            accent_primary="#1976d2",
            accent_secondary="#0097a7"
        ),
        "dark": ThemeColors(
            # Dark theme with modern colors
            background="#1e1e1e",
            surface="#252526",
            panel="#333333",
            text_primary="#ffffff",
            text_secondary="#cccccc",
            text_muted="#808080",
            success="#4caf50",
            warning="#ffeb3b",
            error="#f44336",
            info="#03a9f4",
            cpu="#29b6f6",
            memory="#ba68c8",
            network="#26a69a",
            disk="#ffa726",
            accent_primary="#2196f3",
            accent_secondary="#00bcd4"
        ),
        "pirate": ThemeColors(
            # Fun pirate theme
            background="#1a1c2c",
            surface="#29366f",
            panel="#3b5dc9",
            text_primary="#f4f4f4",
            text_secondary="#c0cbdc",
            text_muted="#566c86",
            success="#41a6f6",
            warning="#f4b41b",
            error="#ef7d57",
            info="#29366f",
            cpu="#41a6f6",
            memory="#f4b41b",
            network="#ef7d57",
            disk="#7b5ba6",
            accent_primary="#ef7d57",
            accent_secondary="#41a6f6"
        ),
        "ocean": ThemeColors(
            # Calm ocean-inspired theme
            background="#0f111a",
            surface="#1a1c25",
            panel="#292d3e",
            text_primary="#d0d0d0",
            text_secondary="#a0a0a0",
            text_muted="#676767",
            success="#c3e88d",
            warning="#ffcb6b",
            error="#ff5370",
            info="#82aaff",
            cpu="#89ddff",
            memory="#c792ea",
            network="#f78c6c",
            disk="#f07178",
            accent_primary="#82aaff",
            accent_secondary="#c792ea"
        )
    }

    def __init__(self, theme_name: str = "default"):
        """Initialize theme manager with specified theme."""
        self.current_theme_name = theme_name
        self.current_theme = self.THEMES[theme_name]

    def get_rich_theme(self) -> Theme:
        """Convert current theme to Rich Theme object."""
        return Theme({
            # General styles
            "default": Style(color=self.current_theme.text_primary),
            "dim": Style(color=self.current_theme.text_muted),
            "title": Style(color=self.current_theme.accent_primary, bold=True),
            
            # Status styles
            "success": Style(color=self.current_theme.success),
            "warning": Style(color=self.current_theme.warning),
            "error": Style(color=self.current_theme.error),
            "info": Style(color=self.current_theme.info),
            
            # Resource monitoring styles
            "cpu": Style(color=self.current_theme.cpu),
            "memory": Style(color=self.current_theme.memory),
            "network": Style(color=self.current_theme.network),
            "disk": Style(color=self.current_theme.disk),
            
            # Panel styles
            "panel.border": Style(color=self.current_theme.panel),
            "panel.title": Style(color=self.current_theme.accent_primary, bold=True),
            
            # Progress bar styles
            "bar.back": Style(color=self.current_theme.surface),
            "bar.complete": Style(color=self.current_theme.accent_primary),
            "bar.finished": Style(color=self.current_theme.success),
            "bar.pulse": Style(color=self.current_theme.accent_secondary),
            
            # Table styles
            "table.header": Style(color=self.current_theme.accent_primary, bold=True),
            "table.cell": Style(color=self.current_theme.text_primary),
            "table.row": Style(bgcolor=self.current_theme.surface),
            
            # Service map styles
            "service.running": Style(color=self.current_theme.success),
            "service.stopped": Style(color=self.current_theme.error),
            "service.starting": Style(color=self.current_theme.warning),
            "service.healthy": Style(color=self.current_theme.success, bold=True),
            "service.unhealthy": Style(color=self.current_theme.error, bold=True)
        })

    def get_panel_style(self) -> Dict[str, str]:
        """Get style configuration for panels."""
        return {
            "background": self.current_theme.background,
            "border_style": self.current_theme.panel,
            "pad": (1, 1)
        }

    def get_table_style(self) -> Dict[str, str]:
        """Get style configuration for tables."""
        return {
            "header_style": f"bold {self.current_theme.accent_primary}",
            "border_style": self.current_theme.panel,
            "row_styles": [f"dim on {self.current_theme.surface}"]
        }

    def switch_theme(self, theme_name: str) -> None:
        """Switch to a different theme."""
        if theme_name not in self.THEMES:
            raise ValueError(f"Theme '{theme_name}' not found")
        self.current_theme_name = theme_name
        self.current_theme = self.THEMES[theme_name]

    def get_status_style(self, status: str) -> Style:
        """Get style for a status indicator."""
        status_styles = {
            "running": Style(color=self.current_theme.success, bold=True),
            "stopped": Style(color=self.current_theme.error, bold=True),
            "starting": Style(color=self.current_theme.warning, bold=True),
            "healthy": Style(color=self.current_theme.success),
            "unhealthy": Style(color=self.current_theme.error),
            "unknown": Style(color=self.current_theme.text_muted)
        }
        return status_styles.get(status.lower(), status_styles["unknown"])

    def get_resource_style(self, usage_percent: float) -> Style:
        """Get style for resource usage based on percentage."""
        if usage_percent >= 90:
            return Style(color=self.current_theme.error, bold=True)
        elif usage_percent >= 75:
            return Style(color=self.current_theme.warning, bold=True)
        elif usage_percent >= 50:
            return Style(color=self.current_theme.info)
        return Style(color=self.current_theme.success) 