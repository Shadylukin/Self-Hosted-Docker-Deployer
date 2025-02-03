"""
GitHub repository parser for Easy Docker Deploy.
"""
from dataclasses import dataclass, asdict
import json
import os
from pathlib import Path
import time
from typing import Dict, List, Optional, Union
import requests
from rich.console import Console
from .markdown_parser import MarkdownParser
import re

console = Console()

@dataclass
class Application:
    """Application metadata."""
    name: str
    description: str
    category: str
    language: Optional[str]
    license_type: Optional[str]
    docker_ready: bool
    docker_url: Optional[str]
    repository_url: Optional[str]
    deployment_guide: Optional[str]

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "language": self.language,
            "license_type": self.license_type,
            "docker_ready": self.docker_ready,
            "docker_url": self.docker_url,
            "repository_url": self.repository_url,
            "deployment_guide": self.deployment_guide
        }

    @classmethod
    def from_dict(cls, data: dict) -> 'Application':
        """Create from dictionary after deserialization."""
        return cls(
            name=data["name"],
            description=data["description"],
            category=data["category"],
            language=data["language"],
            license_type=data["license_type"],
            docker_ready=data["docker_ready"],
            docker_url=data["docker_url"],
            repository_url=data["repository_url"],
            deployment_guide=data["deployment_guide"]
        )

    def matches_search(self, query: str) -> bool:
        """Check if the application matches a search query."""
        query = query.lower()
        searchable_fields = [
            self.name.lower() if self.name else "",
            self.description.lower() if self.description else "",
            self.language.lower() if self.language else "",
            self.category.lower() if self.category else ""
        ]
        return any(query in field for field in searchable_fields)

    @property
    def docker_available(self) -> bool:
        """Alias for docker_ready to maintain compatibility with tests."""
        return self.docker_ready

class GithubParser:
    """Parser for GitHub repositories containing application metadata."""
    
    def __init__(self):
        """Initialize the parser."""
        self.base_url = "https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md"
        self.applications = []
        self.cache_dir = Path.home() / ".easy-docker-deploy" / "cache"
        self.cache_file = self.cache_dir / "applications.json"
        self.cache_expiry = 24 * 60 * 60  # 24 hours in seconds
        self._ensure_cache_dir()
        
        # Docker-related keywords for better detection
        self.docker_keywords = [
            'docker',
            'container',
            'docker-compose',
            'dockerfile',
            'containerized',
            'docker hub',
            'docker image',
            'docker container',
            '🐳'  # Docker whale emoji
        ]
    
    def _ensure_cache_dir(self):
        """Ensure cache directory exists."""
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_cache(self) -> Optional[List[Application]]:
        """Load applications from cache if available and not expired."""
        if not self.cache_file.exists():
            return None
            
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            if time.time() - cache_data["timestamp"] > self.cache_expiry:
                return None
            
            return [Application.from_dict(app_data) for app_data in cache_data["applications"]]
        except Exception:
            return None
    
    def _save_cache(self, applications: List[Application]):
        """Save applications to cache."""
        cache_data = {
            "timestamp": time.time(),
            "applications": [app.to_dict() for app in applications]
        }
        with open(self.cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)
    
    def _check_docker_availability(self, url: str) -> bool:
        """Check if a repository has Docker support."""
        try:
            # Check common Docker-related files
            docker_files = [
                'Dockerfile',
                'docker-compose.yml',
                'docker-compose.yaml',
                '.docker/',
                'docker/'
            ]
            
            # Convert GitHub URLs to raw content URLs
            if 'github.com' in url:
                # Convert HTTPS clone URL to API URL
                api_url = url.replace('github.com', 'api.github.com/repos')
                if api_url.endswith('.git'):
                    api_url = api_url[:-4]
                
                # Get repository contents
                response = requests.get(f"{api_url}/contents")
                if response.status_code == 200:
                    contents = response.json()
                    filenames = [item['name'].lower() for item in contents if isinstance(item, dict)]
                    return any(docker_file.lower() in filenames for docker_file in docker_files)
            
            return False
        except Exception:
            return False
    
    def _extract_docker_url(self, description: str, repository_url: str) -> Optional[str]:
        """Extract Docker image URL from description or repository."""
        # Check for Docker Hub URL
        docker_hub_pattern = r'hub\.docker\.com/r/([^/\s]+/[^/\s)]+)'
        if match := re.search(docker_hub_pattern, description):
            return f"https://hub.docker.com/r/{match.group(1)}"
        
        # Check for GitHub Container Registry
        ghcr_pattern = r'ghcr\.io/([^/\s]+/[^/\s]+)'
        if match := re.search(ghcr_pattern, description):
            return match.group(0)
        
        # Check if repository URL contains dockerfile
        if repository_url and 'dockerfile' in repository_url.lower():
            return repository_url
        
        # If no explicit Docker URL found but has repository URL, check repository
        if repository_url and self._check_docker_availability(repository_url):
            # Convert GitHub URL to potential GitHub Container Registry URL
            if 'github.com' in repository_url:
                org_repo = repository_url.split('github.com/')[-1].strip('/')
                if org_repo.endswith('.git'):
                    org_repo = org_repo[:-4]
                return f"ghcr.io/{org_repo}"
        
        return None
    
    def _is_docker_ready(self, description: str, repository_url: str) -> bool:
        """Check if an application is Docker-ready."""
        # Check for Docker keywords in description
        desc_lower = description.lower()
        if any(keyword in desc_lower for keyword in self.docker_keywords):
            return True
        
        # Check for Docker Hub or GitHub Container Registry URLs
        if self._extract_docker_url(description, repository_url):
            return True
        
        # Check if URL contains dockerfile
        if repository_url and 'dockerfile' in repository_url.lower():
            return True
        
        # Check repository for Docker files
        if repository_url and self._check_docker_availability(repository_url):
            return True
        
        return False
    
    def parse_content(self, content: str, return_dict: bool = True) -> Union[List[Application], Dict[str, Application]]:
        """Parse repository content and extract application metadata.
        
        Args:
            content: The markdown content to parse
            return_dict: If True, returns a dictionary with application names as keys.
                        If False, returns a list of applications.
        
        Returns:
            Either a dictionary mapping application names to Application objects,
            or a list of Application objects, depending on return_dict parameter.
        """
        applications = []
        current_category = None
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
                
            # Try to match category
            if line.startswith('###'):
                current_category = line.lstrip('#').strip()
                if current_category.startswith('[') and current_category.endswith(']'):
                    current_category = current_category[1:-1]
                continue
            
            # Try to match application
            if line.startswith('- ') and current_category:
                result = MarkdownParser.parse_application_line(line)
                if result:
                    name, url, desc, lang, license_type = result
                    docker_ready = self._is_docker_ready(desc, url)
                    docker_url = self._extract_docker_url(desc, url) if docker_ready else None
                    app = Application(
                        name=name,
                        description=desc,
                        category=current_category,
                        language=lang,
                        license_type=license_type,
                        docker_ready=docker_ready,
                        docker_url=docker_url,
                        repository_url=url,
                        deployment_guide=None
                    )
                    applications.append(app)
        
        # Store applications in instance for searching
        self.applications = applications
        
        if return_dict:
            return {app.name: app for app in applications}
        return applications

    def fetch_repository(self) -> List[Application]:
        """Fetch and parse the awesome-selfhosted repository."""
        try:
            response = requests.get(self.base_url)
            response.raise_for_status()
            content = response.text
            
            # Parse content and store as list
            applications = self.parse_content(content, return_dict=False)
            
            # Cache the results
            self._save_cache(applications)
            
            # Store in instance
            self.applications = applications
            return applications
            
        except requests.RequestException as e:
            console.print(f"[red]Failed to fetch repository: {str(e)}[/red]")
            raise RuntimeError(f"Failed to fetch repository: {str(e)}")
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
            raise
    
    def load_applications(self) -> List[Application]:
        """Load applications from cache or fetch from GitHub."""
        try:
            # Try loading from cache first
            cached_apps = self._load_cache()
            if cached_apps is not None:
                return cached_apps
            
            # If not in cache or expired, fetch from repository
            return self.fetch_repository()
        except Exception as e:
            console.print(f"[yellow]Warning: Failed to load applications. Error: {str(e)}[/yellow]")
            return []  # Return empty list instead of None
    
    def get_applications(self) -> List[Application]:
        """Get all parsed applications."""
        return self.applications
    
    def search_applications(self, query: str) -> List[Application]:
        """Search for applications by name or description."""
        if isinstance(self.applications, dict):
            applications = list(self.applications.values())
        else:
            applications = self.applications
            
        return [
            app for app in applications
            if app.matches_search(query)
        ]
    
    def get_applications_by_category(self, category: str) -> List[Application]:
        """Get all applications in a specific category."""
        return [
            app for app in self.applications
            if app.category.lower() == category.lower()
        ]
    
    def get_docker_ready_applications(self) -> List[Application]:
        """Get all applications that have Docker support."""
        return [
            app for app in self.applications
            if app.docker_ready
        ]
    
    def clear_cache(self):
        """Clear the application cache."""
        if self.cache_file.exists():
            try:
                self.cache_file.unlink()
                console.print("[green]Cache cleared successfully.[/green]")
            except Exception as e:
                console.print(f"[yellow]Warning: Failed to clear cache. Error: {str(e)}[/yellow]") 