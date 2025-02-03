"""
Markdown parser for the awesome-selfhosted repository.
"""
import re
from typing import Dict, List, Optional, Tuple, Union
from rich.console import Console
import requests
from dataclasses import dataclass
from ..utils.logging import get_logger

console = Console()
logger = get_logger(__name__)

@dataclass
class Application:
    """Represents a self-hosted application."""
    name: str
    url: str
    description: str
    category: str
    license_info: Optional[str] = None
    docker_ready: bool = False
    repository_url: Optional[str] = None
    docker_url: Optional[str] = None
    language: Optional[str] = None
    license_type: Optional[str] = None

    def matches_search(self, query: str) -> bool:
        """Check if the application matches the search query."""
        query = query.lower()
        return (
            query in self.name.lower() or
            query in self.description.lower() or
            query in self.category.lower()
        )

    @property
    def docker_available(self) -> bool:
        """Alias for docker_ready to maintain compatibility with tests."""
        return self.docker_ready

class ParserError(Exception):
    """Base class for parser-related exceptions."""
    pass

class ContentFetchError(ParserError):
    """Raised when content cannot be fetched from the repository."""
    pass

class ParseError(ParserError):
    """Raised when content cannot be parsed correctly."""
    pass

class GithubParser:
    """Parser for GitHub markdown files."""
    
    def __init__(self):
        self.cache = {}
        self.categories = {}  # Changed from set to dict for better organization
        self.applications = []
        
        # Improved regex patterns
        self.category_pattern = re.compile(r'^#+\s+(.+?)\s*$')
        self.application_pattern = re.compile(r'^\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*-\s*(.+?)(?:\s*`([^`]+)`)?(?:\s*\([^)]+\))?\s*$')
        self.license_pattern = re.compile(r'^\s*-\s*`([^`]+)`\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*$')
        self.toc_pattern = re.compile(r'^\s*-\s*\[([^\]]+)\]\(#[^)]+\)\s*$')
        
    def parse_content(self, content: str) -> None:
        """Parse the markdown content."""
        current_category = None
        in_license_section = False
        in_toc_section = False
        
        try:
            for line in content.split('\n'):
                line = line.strip()
                if not line:
                    continue
                    
                # Check if we're in a special section
                if any(line.lower().startswith(header) for header in ['# license', '## license']):
                    in_license_section = True
                    continue
                elif any(line.lower().startswith(header) for header in ['# table of contents', '## table of contents']):
                    in_toc_section = True
                    continue
                elif line.startswith('#'):
                    in_license_section = False
                    in_toc_section = False
                
                # Skip processing if we're in a special section
                if in_license_section or in_toc_section:
                    continue
                
                # Try to match category
                if category_match := self.category_pattern.match(line):
                    current_category = category_match.group(1)
                    if current_category not in self.categories:
                        self.categories[current_category] = []
                    continue
                
                # Try to match application
                if app_match := self.application_pattern.match(line):
                    if not current_category:
                        logger.warning(f"Found application entry outside of category: {line}")
                        continue
                        
                    name, url, description = app_match.group(1, 2, 3)
                    license_info = app_match.group(4) if len(app_match.groups()) > 3 else None
                    
                    # Clean up description
                    description = description.strip()
                    if description.endswith('.'):
                        description = description[:-1]
                    
                    # Determine if application is Docker-ready
                    docker_ready = any(keyword in description.lower() 
                                     for keyword in ['docker', 'container', 'containerized'])
                    
                    app = Application(
                        name=name,
                        url=url,
                        description=description,
                        category=current_category,
                        license_info=license_info,
                        docker_ready=docker_ready
                    )
                    self.applications.append(app)
                    self.categories[current_category].append(app)
                    continue
                
                # Skip known patterns
                if self.license_pattern.match(line) or self.toc_pattern.match(line):
                    continue
                
                # Only warn about unparsed lines if they look like they might be important
                if line.startswith('-') and not line.startswith('---'):
                    logger.warning(f"Failed to parse line: {line}")
                    
        except Exception as e:
            logger.error(f"Error parsing content: {str(e)}")
            raise ParseError(f"Failed to parse content: {str(e)}") from e
    
    def load_applications(self) -> Union[List[Application], Dict[str, Application]]:
        """
        Load applications from the GitHub repository.
        
        Returns:
            Either a list of Application objects or a dictionary of applications keyed by name,
            depending on the needs of the calling code.
        """
        if not self.applications:
            try:
                content = self._fetch_content()
                self.parse_content(content)
            except Exception as e:
                logger.error(f"Failed to load applications: {str(e)}")
                raise
        
        # Return as list by default, but provide option to get as dict
        return self.applications
    
    def get_applications_dict(self) -> Dict[str, Application]:
        """Get applications as a dictionary keyed by name."""
        return {app.name: app for app in self.load_applications()}
    
    def _fetch_content(self) -> str:
        """Fetch content from GitHub repository."""
        if 'content' not in self.cache:
            try:
                logger.info("Fetching repository content...")
                response = requests.get(
                    'https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md'
                )
                response.raise_for_status()
                self.cache['content'] = response.text
                logger.debug("Content fetched successfully")
            except requests.RequestException as e:
                logger.error(f"Failed to fetch content: {str(e)}")
                raise ContentFetchError(f"Failed to fetch repository content: {str(e)}") from e
        return self.cache['content']
    
    def clear_cache(self) -> None:
        """Clear the parser's cache."""
        self.cache.clear()
        self.categories.clear()
        self.applications.clear()
        logger.debug("Parser cache cleared")

class MarkdownParser:
    """Parser for the awesome-selfhosted markdown format."""
    
    PROGRAMMING_LANGUAGES = [
        'C', 'C++', 'C#', 'JavaScript', 'K8S', 'deb', 'Perl', 'Shell',
        'Python', 'Ruby', 'PHP', 'Java', 'Go', 'Rust', 'TypeScript'
    ]
    
    FRAMEWORKS = [
        'Alpine', 'Node.js', 'Django', 'Flask', 'Rails'
    ]
    
    def __init__(self):
        """Initialize the parser."""
        self.categories = {}
        self.applications = []
        self.current_category = None
        self._content_loaded = False
        
        # Regular expressions for parsing
        self.category_pattern = re.compile(r'^## \[?([^\]]+)\]?')
        self.application_pattern = re.compile(
            r'^\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*-\s*(.+?)(?:\s*`([^`]+)`)?(?:\s*\([^)]+\))?\s*$'
        )
        self.license_pattern = re.compile(
            r'^\s*-\s*`([^`]+)`\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*$'
        )
        self.toc_pattern = re.compile(
            r'^\s*-\s*\[([^\]]+)\]\(#[^)]+\)\s*$'
        )
    
    def parse_content(self, content: str) -> None:
        """Parse the markdown content."""
        if self._content_loaded:
            return
            
        current_category = None
        in_license_section = False
        in_toc_section = False
        
        for line in content.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if we're in a special section
            if any(line.lower().startswith(header) for header in ['# license', '## license']):
                in_license_section = True
                continue
            elif any(line.lower().startswith(header) for header in ['# table of contents', '## table of contents']):
                in_toc_section = True
                continue
            elif line.startswith('#'):
                in_license_section = False
                in_toc_section = False
            
            # Skip processing if we're in a special section
            if in_license_section or in_toc_section:
                continue
            
            # Try to match category
            category_match = self.category_pattern.match(line)
            if category_match:
                current_category = category_match.group(1)
                if current_category not in self.categories:
                    self.categories[current_category] = []
                continue
            
            # Try to match application
            app_match = self.application_pattern.match(line)
            if app_match and current_category:
                name, url, description = app_match.group(1, 2, 3)
                license_info = app_match.group(4) if len(app_match.groups()) > 3 else None
                
                # Clean up description
                description = description.strip()
                if description.endswith('.'):
                    description = description[:-1]
                
                # Determine if application is Docker-ready
                docker_ready = any(keyword in description.lower() 
                                 for keyword in ['docker', 'container', 'containerized'])
                
                app = Application(
                    name=name,
                    url=url,
                    description=description,
                    category=current_category,
                    license_info=license_info,
                    docker_ready=docker_ready
                )
                self.applications.append(app)
                self.categories[current_category].append(app)
                continue
            
            # Skip known patterns
            if self.license_pattern.match(line) or self.toc_pattern.match(line):
                continue
            
            # Only warn about unparsed lines if they look like they might be important
            if line.startswith('-') and not line.startswith('---'):
                console.print(f"[yellow]Warning: Failed to parse line: {line}[/yellow]")
        
        self._content_loaded = True
    
    def load_applications(self) -> List[Application]:
        """Load applications from the GitHub repository."""
        if not self._content_loaded:
            content = self._fetch_content()
            self.parse_content(content)
        return self.applications
    
    def _fetch_content(self) -> str:
        """Fetch content from GitHub repository."""
        if not hasattr(self, '_content_cache'):
            console.print("Fetching repository content...")
            response = requests.get(
                'https://raw.githubusercontent.com/awesome-selfhosted/awesome-selfhosted/master/README.md'
            )
            response.raise_for_status()
            self._content_cache = response.text
            console.print("First few lines of content:")
            console.print('\n'.join(self._content_cache.split('\n')[:10]))
        return self._content_cache

    # Regular expressions for parsing
    CATEGORY_PATTERN = r'^## \[?([^\]]+)\]?'
    APP_PATTERN = r'^\s*-\s*(?:\[([^\]]+)\]\(([^)]+)\)|([^-\s][^\s]*))(?:\s*-\s*|\s+)(.*?)(?:\s*`([^`]+)`)?(?:\s*`([^`]+)`)?(?:\s*(?:\[[^\]]+\](?:\([^)]+\))?|\([^)]+\))*)?(?:\s*\([^)]+\))*\s*$'
    TOC_PATTERN = r'^\s*-\s*\[([^\]]+)\]\(#[^)]+\)\s*$'
    LICENSE_PATTERN = r'^\s*-\s*`([^`]+)`\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*$'
    DOCKER_HUB_PATTERN = r'(?:hub\.docker\.com|docker\.io|quay\.io)/(?:r/)?[a-zA-Z0-9_-]+/[a-zA-Z0-9_-]+'
    DOCKER_REFERENCE_PATTERN = r'(?:docker(?:ized|file|hub|compose)?|container(?:ized)?)'
    
    @staticmethod
    def extract_categories(content: str) -> List[str]:
        """Extract categories from markdown content."""
        categories = []
        category_pattern = re.compile(r'^###\s+\[?([^\]]+)\]?')
        
        for line in content.split('\n'):
            if match := category_pattern.match(line.strip()):
                categories.append(match.group(1))
        
        return categories
    
    @staticmethod
    def parse_application_line(line: str) -> Optional[Tuple[str, str, str, Optional[str], Optional[str]]]:
        """Parse a single application line."""
        pattern = re.compile(r'^\s*-\s*\[([^\]]+)\]\(([^)]+)\)\s*-\s*(.+?)(?:\s*`([^`]+)`)?(?:\s*\[([^\]]+)\])?(?:\s*\([^)]+\))?\s*$')
        
        if match := pattern.match(line):
            name = match.group(1)
            url = match.group(2)
            desc = match.group(3).strip().rstrip('.')
            lang = match.group(4)
            license_type = match.group(5)
            
            return name, url, desc, lang, license_type
            
        return None
    
    @staticmethod
    def is_docker_url(url: str) -> bool:
        """Check if the URL is likely a Docker-related URL."""
        # Check for Docker registry URLs
        if re.search(MarkdownParser.DOCKER_HUB_PATTERN, url):
            return True
            
        # Check for Docker-related words in URL
        url_lower = url.lower()
        if re.search(MarkdownParser.DOCKER_REFERENCE_PATTERN, url_lower):
            return True
            
        # Check for GitHub repositories with Docker-related names
        if 'github.com' in url_lower and re.search(r'/docker-[a-zA-Z0-9-]+/?$', url_lower):
            return True
            
        return False
    
    @staticmethod
    def has_docker_reference(text: str) -> bool:
        """Check if text contains Docker-related references."""
        text_lower = text.lower()
        
        # Common Docker-related phrases
        docker_phrases = [
            'docker image',
            'docker container',
            'dockerized',
            'docker-compose',
            'dockerfile',
            'docker hub',
            'containerized',
            'runs in docker',
            'docker support',
            'docker deployment',
            'docker',
            'container'
        ]
        
        # Check for phrases
        if any(phrase in text_lower for phrase in docker_phrases):
            return True
            
        # Check for pattern matches
        if re.search(MarkdownParser.DOCKER_REFERENCE_PATTERN, text_lower):
            return True
            
        return False
    
    @staticmethod
    def extract_docker_url(description: str, url: str) -> Optional[str]:
        """Extract Docker-related URL from description or main URL."""
        # Look for Docker registry URLs in description
        if docker_match := re.search(MarkdownParser.DOCKER_HUB_PATTERN, description):
            return f"https://{docker_match.group(0)}"
        
        # If description mentions Docker and we have a GitHub URL
        if MarkdownParser.has_docker_reference(description):
            if 'github.com' in url.lower():
                return url
        
        # Check if main URL is Docker-related
        if MarkdownParser.is_docker_url(url):
            return url
            
        return None 