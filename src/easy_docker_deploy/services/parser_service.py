"""
Service layer for handling application parsing and caching.
"""
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Union

from ..config.settings import get_config
from ..parser.github_parser import GithubParser, Application, ParserError
from ..utils.logging import get_logger, log_with_context

logger = get_logger(__name__)

class ParserService:
    """Service for handling application parsing and caching."""
    
    def __init__(self):
        self.config = get_config()
        self.parser = GithubParser()
        self._cache_file = self.config.cache_dir / 'applications.json'
        
    def get_applications(self, force_refresh: bool = False) -> List[Application]:
        """
        Get all applications, using cache if available and not expired.
        
        Args:
            force_refresh: Whether to force a refresh of the cache
            
        Returns:
            List of Application objects
        """
        if not force_refresh and self._is_cache_valid():
            try:
                return self._load_from_cache()
            except Exception as e:
                logger.warning(
                    "Failed to load from cache",
                    **log_with_context(error=str(e))
                )
        
        return self._fetch_and_cache()
    
    def get_applications_by_category(self, category: str) -> List[Application]:
        """
        Get applications filtered by category.
        
        Args:
            category: Category to filter by
            
        Returns:
            List of Application objects in the specified category
        """
        apps = self.get_applications()
        return [app for app in apps if app.category == category]
    
    def search_applications(self, query: str) -> List[Application]:
        """
        Search for applications matching a query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching Application objects
        """
        apps = self.get_applications()
        return [app for app in apps if app.matches_search(query)]
    
    def get_docker_ready_applications(self) -> List[Application]:
        """
        Get all Docker-ready applications.
        
        Returns:
            List of Docker-ready Application objects
        """
        apps = self.get_applications()
        return [app for app in apps if app.docker_ready]
    
    def clear_cache(self) -> None:
        """Clear the application cache."""
        try:
            if self._cache_file.exists():
                self._cache_file.unlink()
                logger.info("Cache cleared successfully")
        except Exception as e:
            logger.error(
                "Failed to clear cache",
                **log_with_context(error=str(e))
            )
            raise
    
    def _is_cache_valid(self) -> bool:
        """Check if the cache exists and is not expired."""
        if not self._cache_file.exists():
            return False
            
        cache_age = time.time() - self._cache_file.stat().st_mtime
        return cache_age < self.config.cache_ttl
    
    def _load_from_cache(self) -> List[Application]:
        """Load applications from cache."""
        logger.debug("Loading applications from cache")
        try:
            with open(self._cache_file) as f:
                data = json.load(f)
            
            applications = []
            for app_data in data:
                app = Application(**app_data)
                applications.append(app)
            
            logger.info(
                "Loaded applications from cache",
                **log_with_context(count=len(applications))
            )
            return applications
            
        except Exception as e:
            logger.error(
                "Failed to load from cache",
                **log_with_context(error=str(e))
            )
            raise
    
    def _fetch_and_cache(self) -> List[Application]:
        """Fetch applications and update cache."""
        logger.info("Fetching fresh application data")
        try:
            applications = self.parser.load_applications()
            
            # Ensure cache directory exists
            self._cache_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Save to cache
            with open(self._cache_file, 'w') as f:
                json.dump(
                    [app.__dict__ for app in applications],
                    f,
                    indent=2
                )
            
            logger.info(
                "Updated application cache",
                **log_with_context(count=len(applications))
            )
            return applications
            
        except Exception as e:
            logger.error(
                "Failed to fetch and cache applications",
                **log_with_context(error=str(e))
            )
            raise

# Global service instance
_service: Optional[ParserService] = None

def get_parser_service() -> ParserService:
    """Get the global parser service instance."""
    global _service
    if _service is None:
        _service = ParserService()
    return _service 